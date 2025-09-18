# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import add_years, add_days, cint, get_link_to_form, getdate, flt, nowdate, now_datetime, nowtime, today, date_diff, time_diff_in_hours, format_date
from frappe.utils.background_jobs import enqueue
from erpnext.accounts.utils import get_account_currency
from frappe.core.doctype.user.user import STANDARD_USERS
from erpnext.accounts.doctype.payment_entry.payment_entry import (
	PaymentEntry,
	get_bank_cash_account,
	get_reference_details,
)
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_employee_currency

def validate(doc, method=None):
	max_advance_days, block_new_advances = frappe.db.get_value("Company", doc.company, ["custom_max_advance_days", "custom_block_new_advances"])

	if block_new_advances:
		advances =  frappe.get_list(
			"Employee Advance",
			fields=["*"],
			filters=[
				["docstatus", "=", '1'],
				["employee", "=", doc.employee],
				["status", "in", ['Paid','Partly Claimed and Returned'] ],
				#["advance_amount", "=", "claimed_amount"], #Sanity check: Don't rely on status only
				["posting_date", "<=", add_days(today(), -max_advance_days)]
			]
		)

		if advances:
			advances_info = ""
			for advance in advances:
				link = get_link_to_form("Employee Advance", advance.name)
				advances_info += f"\n- {link}"

			employee = frappe.db.get_value("Employee", doc.employee, ["first_name", "last_name"], as_dict=1)
			frappe.throw(
				_(f"<b>{employee.first_name} {employee.last_name}</b> has {len(advances)} Unclaimed Advances that are <b>older than {max_advance_days} day(s)</b>. Make sure to claim outstanding advances before requesting a new advance.\n{advances_info}")
			)

@frappe.whitelist()
def recover_overdue_advances():
    """Queue the advance recovery process in background"""
    enqueue(
        method="seal_hrms.seal_hrms.overrides.employee_advance.process_overdue_advance_recovery",
        queue="default",  # or "long" for longer-running tasks
        timeout=1800,  # 30 minutes timeout
        is_async=True,
        job_name="Employee Advance Recovery"
    )
    
def process_overdue_advance_recovery():
	companies = frappe.get_list("Company", fields=[
			"name", 
			"custom_max_advance_days", 
			"custom_auto_recover_advances_from_salary", 
			"custom_salary_component_for_recovery"
		])

	# Track processing results
	processing_results = {
		"total_companies": len(companies),
		"processed_companies": 0,
		"total_advances_processed": 0,
		"successful_recoveries": 0,
		"errors": [],
		"companies_processed": []
	}

	for company in companies:
		try:
			auto_recover_advances_from_salary = company.custom_auto_recover_advances_from_salary 
			salary_component_for_recovery = company.custom_salary_component_for_recovery
			max_advance_days = company.custom_max_advance_days or 30

			# Skip if auto recovery is disabled
			if not auto_recover_advances_from_salary:
				continue

			processing_results["processed_companies"] += 1
			company_result = {
				"name": company.name,
				"advances_found": 0,
				"recoveries_created": 0,
				"errors": []
			}

			# Check if salary component is configured
			if not salary_component_for_recovery:
				error_msg = f"Cannot create Additional Salary (Deduction) to recover Employee Advances because Salary Component for Advance Recovery in Company Settings for {company.name} has not been set."
				frappe.log_error(message=error_msg, title="Overdue Employee Advance Recovery")
				
				processing_results["errors"].append(error_msg)
				company_result["errors"].append(error_msg)
				processing_results["companies_processed"].append(company_result)
				continue

			# Get overdue advances
			cutoff_date = add_days(today(), -max_advance_days)
			advances = frappe.get_list("Employee Advance", 
				fields=[
					"name", "employee", "company", "advance_amount", 
					"posting_date", "currency"
				], 
				filters=[
					["company", "=", company.name], 
					["docstatus", "=", 1],  # Submitted
					["status", "=", "Paid"], 
					["posting_date", "<", cutoff_date]
				]
			)

			company_result["advances_found"] = len(advances)
			processing_results["total_advances_processed"] += len(advances)
	
			if not advances:
				processing_results["companies_processed"].append(company_result)
				continue

			for advance in advances:
				try:
					# Check if employee has salary structure assignment
					if not frappe.db.exists("Salary Structure Assignment", {"employee": advance.employee}):
						frappe.log_error(message=f"Cannot create Additional Salary (Deduction) to recover {advance.name} for {advance.employee} in {advance.company} because there is no Salary Structure assigned.", title="Overdue Employee Advance Recovery")
						processing_results["errors"].append(error_msg)
						company_result["errors"].append(error_msg)
						continue	

					# Check if Additional Salary already exists for this advance
					existing_additional_salary = frappe.db.exists("Additional Salary", {
						"company": advance.company, 
						"ref_doctype": "Employee Advance", 
						"ref_docname": advance.name,
						"docstatus": ["!=", 2]  # Not cancelled
					})

					if existing_additional_salary:
						continue		

					# Create Additional Salary for recovery
					additional_salary = frappe.new_doc("Additional Salary")
					additional_salary.employee = advance.employee
					additional_salary.company = advance.company
					additional_salary.is_recurring = 0
					additional_salary.salary_component = salary_component_for_recovery
					additional_salary.amount = advance.advance_amount
					additional_salary.currency = advance.currency or get_employee_currency(advance.employee)
					additional_salary.ref_doctype = "Employee Advance"
					additional_salary.ref_docname = advance.name
					additional_salary.payroll_date = add_days(advance.posting_date, max_advance_days)
					additional_salary.posting_date = today()

					additional_salary.insert()
					additional_salary.submit()

					company_result["recoveries_created"] += 1
					processing_results["successful_recoveries"] += 1
				except Exception as e:
					frappe.log_error(message=f"Error creating Additional Salary for advance {advance.name}: {str(e)}", title="Overdue Employee Advance Recovery")
					continue

			processing_results["companies_processed"].append(company_result)

		except Exception as e:
				frappe.log_error(message=f"Error processing company {company.name}: {str(e)}", title="Overdue Employee Advance Recovery")
				continue

	# Send comprehensive notification to HR
	send_hr_notification(processing_results)

@frappe.whitelist()
def get_global_recovery_status():
    """
    Get global status of advance recovery across all companies
    """
    try:
        # Get companies with auto-recovery enabled
        enabled_companies = frappe.get_list("Company", 
            filters={"custom_auto_recover_advances_from_salary": 1},
            fields=["name", "custom_max_advance_days", "custom_salary_component_for_recovery"]
        )
        
        total_overdue_advances = 0
        total_outstanding_amount = 0
        company_breakdown = []
        configuration_issues = []
        
        for company in enabled_companies:
            try:
                max_advance_days = company.custom_max_advance_days or 30
                cutoff_date = add_days(today(), -max_advance_days)
                
                # Check configuration
                if not company.custom_salary_component_for_recovery:
                    configuration_issues.append(f"{company.name}: Missing salary component for recovery")
                
                # Get overdue advances for this company
                overdue_data = frappe.db.sql("""
                    SELECT 
                        COUNT(*) as count,
                        COALESCE(SUM(advance_amount), 0) as total_amount
                    FROM `tabEmployee Advance`
                    WHERE company = %s 
                        AND docstatus = 1 
                        AND status = 'Paid'
                        AND posting_date < %s
                """, (company.name, cutoff_date), as_dict=True)
                
                if overdue_data:
                    company_count = overdue_data[0].count
                    company_amount = overdue_data[0].total_amount
                    
                    total_overdue_advances += company_count
                    total_outstanding_amount += company_amount
                    
                    if company_count > 0:
                        company_breakdown.append({
                            "company": company.name,
                            "overdue_count": company_count,
                            "outstanding_amount": company_amount
                        })
                        
            except Exception as e:
                configuration_issues.append(f"{company.name}: Error checking status - {str(e)}")
        
        # Get pending recovery records
        pending_recoveries = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabAdditional Salary`
            WHERE ref_doctype = 'Employee Advance'
                AND docstatus = 1
        """, as_dict=True)
        
        # Get last recovery run from logs
        last_run = frappe.db.sql("""
            SELECT MAX(creation) as last_run
            FROM `tabError Log`
            WHERE error LIKE %s
        """, ("%advance recovery%",), as_dict=True)
        
        # Check for active recovery jobs
        active_jobs = 0
        try:
            from frappe.utils.background_jobs import get_jobs
            jobs = get_jobs()
            active_jobs = len([job for job in jobs if 
                            job.get('job_name') == 'Employee Advance Recovery' and 
                            job.get('status') in ['queued', 'started']])
        except:
            pass
        
        return {
            "enabled_companies": len(enabled_companies),
            "total_overdue_advances": total_overdue_advances,
            "total_outstanding_amount": total_outstanding_amount,
            "pending_recoveries": pending_recoveries[0].count if pending_recoveries else 0,
            "last_run": last_run[0].last_run if last_run and last_run[0].last_run else None,
            "active_recovery_jobs": active_jobs,
            "company_breakdown": company_breakdown,
            "configuration_issues": configuration_issues
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting global recovery status: {str(e)}", "Global Status Error")
        return {"error": str(e)}

def send_hr_notification(processing_results):
    """Send comprehensive email notification to HR users about advance recovery processing"""
    try:
        # Get HR users
        hr_users = frappe.get_list("User", 
            filters={
                "enabled": 1,
                "name": ["in", [
                    user.parent for user in frappe.get_list("Has Role", 
                        filters={"role": "HR User"}, 
                        fields=["parent"]
                    )
                ]]
            },
            fields=["email", "full_name"]
        )
        
        if not hr_users:
            return
            
        recipients = [user.email for user in hr_users if user.email]
        if not recipients:
            return

        # Determine subject and message type
        has_errors = len(processing_results["errors"]) > 0
        has_successes = processing_results["successful_recoveries"] > 0
        
        if has_errors and has_successes:
            subject = f"Employee Advance Recovery - Partial Success ({today()})"
            status_color = "orange"
        elif has_errors:
            subject = f"Employee Advance Recovery - Issues Found ({today()})"
            status_color = "red"
        elif has_successes:
            subject = f"Employee Advance Recovery - Completed Successfully ({today()})"
            status_color = "green"
        else:
            subject = f"Employee Advance Recovery - No Actions Needed ({today()})"
            status_color = "blue"

        # Build detailed message
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px;">
            <h2 style="color: {status_color};">Employee Advance Recovery Report</h2>
            <p><strong>Date:</strong> {today()}</p>
            
            <h3>Summary</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Companies</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{processing_results["total_companies"]}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Companies Processed</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{processing_results["processed_companies"]}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Advances Found</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{processing_results["total_advances_processed"]}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; color: green;"><strong>Successful Recoveries</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: green;">{processing_results["successful_recoveries"]}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="border: 1px solid #ddd; padding: 8px; color: red;"><strong>Errors</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: red;">{len(processing_results["errors"])}</td>
                </tr>
            </table>
        """

        # Add company-wise details
        if processing_results["companies_processed"]:
            message += "<h3>Company-wise Details</h3>"
            for company_result in processing_results["companies_processed"]:
                message += f"""
                <div style="margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <h4>{company_result["name"]}</h4>
                    <ul>
                        <li>Overdue Advances Found: {company_result["advances_found"]}</li>
                        <li>Recovery Records Created: {company_result["recoveries_created"]}</li>
                """
                if company_result["errors"]:
                    message += f"<li style='color: red;'>Errors: {len(company_result['errors'])}</li>"
                message += "</ul>"
                
                if company_result["errors"]:
                    message += "<p><strong>Error Details:</strong></p><ul>"
                    for error in company_result["errors"]:
                        message += f"<li style='color: red; font-size: 12px;'>{error}</li>"
                    message += "</ul>"
                message += "</div>"

        # Add global errors if any
        if processing_results["errors"]:
            message += """
            <h3 style="color: red;">Issues Requiring Attention</h3>
            <div style="background-color: #fff2f2; padding: 10px; border-radius: 5px; border-left: 4px solid red;">
                <ul>
            """
            for error in processing_results["errors"]:
                message += f"<li style='margin: 5px 0;'>{error}</li>"
            message += "</ul></div>"

        # Add action items
        if has_errors:
            message += """
            <h3>Required Actions</h3>
            <div style="background-color: #fffacd; padding: 10px; border-radius: 5px; border-left: 4px solid orange;">
                <ul>
                    <li>Review and configure missing salary components for advance recovery</li>
                    <li>Ensure all employees have valid salary structure assignments</li>
                    <li>Check system logs for detailed error information</li>
                </ul>
            </div>
            """

        message += """
            <br>
            <p style="font-size: 12px; color: #666;">
                This is an automated report from the Employee Advance Recovery system. 
                For technical support, please contact your system administrator.
            </p>
        </div>
        """

        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )        
    except Exception as e:
        frappe.log_error(message=f"Failed to send HR notification: {str(e)}", title="HR Notification Error")

@frappe.whitelist()
def notify_overdue_advances():
    """Queue the advance notification process in background"""
    enqueue(
        method="seal_hrms.seal_hrms.overrides.employee_advance.process_notify_overdue_advance",
        queue="default",  # or "long" for longer-running tasks
        timeout=1800,  # 30 minutes timeout
        is_async=True,
        job_name="Employee Advance Notification"
    )

def process_notify_overdue_advance():
    """
    PRE-DUE REMINDERS (simplified policy):
      - Urgent: send when due is tomorrow (days_to_due == 1).
      - Custom (daily): send on every day where 2 <= days_to_due <= notice_days.
      - Do not send both on the same day; urgent outranks custom.
      - Skip overdue (days_to_due < 0).
    One email max per (Company, Employee) per day; include all triggered advances in that email.
    """
    LOGNS = "ADV Notify"

    try:
        frappe.log_error("START process_notify_overdue_advance()", f"{LOGNS}: Start")

        results = {
            "total_companies": 0,
            "processed_companies": 0,
            "total_employees_notified": 0,
            "total_advances_expiring": 0,   # count of advances matched today
            "notifications_sent": 0,        # set by send_advance_notification
            "errors": [],
            # Key: f"{company}::{employee}"
            "employee_notifications": {},
        }

        # --- Companies with notifications enabled
        companies = frappe.get_list(
            "Company",
            fields=["name", "custom_notify_outstanding_advance",
                    "custom_advance_notification_days", "custom_max_advance_days"],
            filters={"custom_notify_outstanding_advance": 1},
        )
        results["total_companies"] = len(companies)
        frappe.log_error(
            f"Companies enabled={len(companies)}; { [c.name for c in companies] }",
            f"{LOGNS}: Companies"
        )

        # Cache for Employee metadata to avoid repeated lookups
        emp_cache = {}
        def get_emp_meta(emp_id: str):
            if not emp_id:
                return {"employee_name": None, "employee_email": None}
            if emp_id not in emp_cache:
                row = frappe.db.get_value(
                    "Employee", emp_id, ["employee_name", "prefered_email"], as_dict=True
                ) or {}
                emp_cache[emp_id] = {
                    "employee_name": row.get("employee_name"),
                    "employee_email": row.get("prefered_email"),
                }
                frappe.log_error(
                    f"Cached employee meta [{emp_id}] -> {emp_cache[emp_id]}",
                    f"{LOGNS}: Emp Cache"
                )
            return emp_cache[emp_id]

        # --- Per company
        for company in companies:
            try:
                # Coerce settings
                notice_days = cint(company.custom_advance_notification_days) or 7
                max_days    = cint(company.custom_max_advance_days) or 30
                if notice_days < 0:
                    notice_days = 0  # keep sane
                if max_days < 1:
                    max_days = 30
                frappe.log_error(
                    f"[{company.name}] Config notice_days={notice_days}, max_days={max_days}",
                    f"{LOGNS}: Company Config"
                )

                # Fetch candidate advances and classify in Python
                advances = frappe.get_all(
                    "Employee Advance",
                    filters={
                        "company": company.name,
                        "docstatus": 1,
                        "status": ["in", ["Paid", "Partly Claimed and Returned"]],
                        # Optional: prevent future-dated posts
                        # "posting_date": ("<=", today()),
                    },
                    fields=["name", "employee", "company", "advance_amount", "currency", "posting_date"],
                )
                frappe.log_error(
                    f"[{company.name}] Candidate advances={len(advances)}; sample={ [a['name'] for a in advances[:10]] }",
                    f"{LOGNS}: Candidates"
                )

                # One email per employee per day (urgent > custom)
                per_emp = {}
                prio = {"custom": 1, "urgent": 2}

                for adv in advances:
                    due_date    = add_days(adv["posting_date"], max_days)
                    d           = date_diff(due_date, today())  # >0 future; 0 due today; <0 overdue

                    # Skip overdue in pre-due policy
                    if d < 0:
                        frappe.log_error(
                            f"[{company.name}] ADV {adv['name']} skipped: overdue (days_to_due={d})",
                            f"{LOGNS}: Skip"
                        )
                        continue

                    trigger, trigger_days = None, None

                    # Urgent: tomorrow only
                    if d == 1:
                        trigger, trigger_days = "urgent", 1

                    # Custom daily window: 2..notice_days
                    elif 2 <= d <= notice_days:
                        trigger, trigger_days = "custom", d

                    # Optional: enable due-day notice by uncommenting
                    # elif notice_days == 0 and d == 0:
                    #     trigger, trigger_days = "custom", 0

                    if not trigger:
                        frappe.log_error(
                            f"[{company.name}] ADV {adv['name']} no-trigger today: "
                            f"days_to_due={d}, notice_days={notice_days} "
                            f"(rules: urgent if 1; custom if 2..{notice_days})",
                            f"{LOGNS}: No Trigger"
                        )
                        continue

                    frappe.log_error(
                        f"[{company.name}] ADV {adv['name']} -> trigger={trigger}, days_to_due={d}, "
                        f"posting={adv['posting_date']}, due={due_date}",
                        f"{LOGNS}: Decision"
                    )

                    meta = get_emp_meta(adv["employee"])
                    if not meta.get("employee_email"):
                        msg = f"No preferred email for employee {adv['employee']} in {company.name}; skipping {adv['name']}"
                        results["errors"].append(msg)
                        frappe.log_error(msg, f"{LOGNS}: Missing Email")
                        continue

                    key = f"{company.name}::{adv['employee']}"
                    bucket = per_emp.get(key)
                    if not bucket:
                        bucket = per_emp[key] = {
                            "employee_name": meta["employee_name"],
                            "employee_email": meta["employee_email"],
                            "company": company.name,
                            "advances": [],
                            "notification_type": trigger,      # may upgrade to urgent
                            "notification_days": trigger_days, # display-friendly (min for custom)
                        }
                        frappe.log_error(
                            f"[{company.name}] New bucket for {key}: type={trigger}, notif_days={trigger_days}",
                            f"{LOGNS}: Bucket New"
                        )
                    else:
                        # Upgrade email type to urgent if any advance is urgent today
                        if prio.get(trigger, 0) > prio.get(bucket["notification_type"], 0):
                            old_type = bucket["notification_type"]
                            bucket["notification_type"] = trigger
                            bucket["notification_days"] = trigger_days
                            frappe.log_error(
                                f"[{company.name}] Bucket {key} type upgrade {old_type} -> {trigger}",
                                f"{LOGNS}: Bucket Upgrade"
                            )
                        # If both custom, keep the smallest d for cleaner text
                        elif bucket["notification_type"] == "custom" and trigger == "custom":
                            prev = bucket["notification_days"]
                            if trigger_days is not None and prev is not None and trigger_days < prev:
                                bucket["notification_days"] = trigger_days
                                frappe.log_error(
                                    f"[{company.name}] Bucket {key} custom notif_days minimized {prev} -> {trigger_days}",
                                    f"{LOGNS}: Bucket Minimize"
                                )

                    bucket["advances"].append({
                        "name": adv["name"],
                        "advance_amount": adv["advance_amount"],
                        "currency": adv["currency"],
                        "posting_date": adv["posting_date"],
                        "recovery_due_date": due_date,
                        "days_until_recovery": d,               # used by templates
                        "notification_type": bucket["notification_type"],
                    })
                    frappe.log_error(
                        f"[{company.name}] Bucket {key} appended adv {adv['name']} (total now {len(bucket['advances'])})",
                        f"{LOGNS}: Bucket Append"
                    )

                # Merge tallies for this company
                emp_count = len(per_emp)
                adv_count = sum(len(v["advances"]) for v in per_emp.values())
                results["processed_companies"] += 1
                results["total_employees_notified"] += emp_count
                results["total_advances_expiring"] += adv_count
                results["employee_notifications"].update(per_emp)

                # Type breakdown for visibility
                type_counts = {"custom": 0, "urgent": 0}
                for v in per_emp.values():
                    type_counts[v["notification_type"]] += 1

                frappe.log_error(
                    f"[{company.name}] Grouped employees={emp_count}, advances={adv_count}, types={type_counts}",
                    f"{LOGNS}: Group Summary"
                )

            except Exception as e:
                msg = f"Company {company.name} processing error: {e}"
                results["errors"].append(msg)
                frappe.log_error(msg, f"{LOGNS}: Company Error")
                continue

        # Pre-send summary
        total_emp = len(results["employee_notifications"])
        total_adv = results["total_advances_expiring"]
        frappe.log_error(
            f"Pre-Send: employees={total_emp}, advances={total_adv}, processed_companies={results['processed_companies']}",
            f"{LOGNS}: Pre-Send"
        )

        # Send emails
        if results["employee_notifications"]:
            try:
                sent = send_advance_notification(results)  # your Email Template–aware sender
                if isinstance(sent, int):
                    results["notifications_sent"] = sent
                frappe.log_error(
                    f"Post-Send: notifications_sent={results['notifications_sent']}",
                    f"{LOGNS}: Post-Send"
                )
            except Exception as e:
                err = f"Send phase error: {e}"
                results["errors"].append(err)
                frappe.log_error(err, f"{LOGNS}: Send Error")
        else:
            frappe.log_error("No employee notifications to send today.", f"{LOGNS}: Pre-Send")

        # Final summary
        frappe.log_error(
            (
                f"COMPLETE processed_companies={results['processed_companies']}, "
                f"total_employees_notified={results['total_employees_notified']}, "
                f"total_advances_expiring={results['total_advances_expiring']}, "
                f"notifications_sent={results.get('notifications_sent', 0)}, "
                f"errors={len(results['errors'])}"
            ),
            f"{LOGNS}: Complete"
        )

        return results

    except Exception as e:
        err = f"Critical error in process_notify_overdue_advance: {e}"
        frappe.log_error(err, f"{LOGNS}: Critical")
        return {"status": "error", "message": err}
    
def send_advance_notification(processing_results):
    """
    Sends employee emails using Company.custom_advance_expiry_email_template if set,
    otherwise plain text. Also sends a simplified HR summary.
    """
    notifications_sent = 0
    logger = frappe.logger("advance_notify")

    # cache: company -> template doc
    company_template_cache = {}

    for employee, notification_data in processing_results.get("employee_notifications", {}).items():
        try:
            if not notification_data.get("employee_email"):
                processing_results["errors"].append(f"No email address for employee {employee}")
                continue

            employee_name = notification_data["employee_name"]
            company = notification_data["company"]
            advances = notification_data["advances"]
            notification_type = notification_data["notification_type"]
            notification_days = notification_data["notification_days"]

            total_amount = sum(flt(a["advance_amount"]) for a in advances)
            currency = advances[0]["currency"] if advances else ""

            sender = None
            if frappe.session.user not in STANDARD_USERS:
                sender = frappe.session.user

            # doc_args to feed into template
            doc_args = {
                "employee": {
                    "name": employee,
                    "full_name": employee_name,
                    "email": notification_data["employee_email"],
                },
                "company": {"name": company},
                "notification": {
                    "type": notification_type,
                    "days": notification_days,
                    "date": format_date(today()),
                    "urgency_badge": "URGENT - 1 DAY REMAINING" if notification_type == "urgent" else f"{notification_days} DAYS NOTICE",
                },
                "totals": {
                    "count": len(advances),
                    "amount": total_amount,
                    "currency": currency,
                },
                "advances": [
                    {
                        "name": a["name"],
                        "amount": a["advance_amount"],
                        "currency": a["currency"],
                        "posting_date": format_date(a["posting_date"]),
                        "recovery_due_date": format_date(a["recovery_due_date"]),
                    } for a in advances
                ],
            }

            # resolve company template
            if company not in company_template_cache:
                tmpl_name = frappe.get_cached_value("Company", company, "custom_advance_expiry_email_template")
                tmpl_doc = frappe.get_doc("Email Template", tmpl_name) if tmpl_name else None
                company_template_cache[company] = tmpl_doc

            tmpl = company_template_cache[company]

            if tmpl:
                try:
                    subject = frappe.render_template(tmpl.subject or "Advance Recovery Notice", doc_args)
                    message = frappe.render_template(tmpl.response or "", doc_args)
                except Exception as re:
                    frappe.log_error(f"Template rendering failed for {company}: {re}", "Advance Notify Template Error")
                    # --- fallback inline ---
                    notif, totals = doc_args["notification"], doc_args["totals"]
                    subject = f"Employee Advance Recovery — {notif['urgency_badge']}"
                    lines = [
                        f"Dear {doc_args['employee']['full_name']},",
                        f"This is a reminder about your outstanding employee advance(s) with {company}.",
                        f"Notice: {notif['urgency_badge']}",
                        f"Total advances: {totals['count']}",
                        f"Total amount: {totals['amount']} {totals['currency']}",
                        "",
                        "Details:",
                    ]
                    for a in doc_args["advances"]:
                        lines.append(f"- {a['name']}: {a['amount']} {a['currency']} | Issue: {a['posting_date']} | Due: {a['recovery_due_date']}")
                    lines.append("")
                    lines.append("This is an automated notice. Please contact HR if you have any questions.")
                    lines.append(f"{company} | {notif['date']}")
                    message = "\n".join(lines)
            else:
                # --- fallback inline ---
                notif, totals = doc_args["notification"], doc_args["totals"]
                subject = f"Employee Advance Recovery — {notif['urgency_badge']}"
                lines = [
                    f"Dear {doc_args['employee']['full_name']},",
                    f"This is a reminder about your outstanding employee advance(s) with {company}.",
                    f"Notice: {notif['urgency_badge']}",
                    f"Total advances: {totals['count']}",
                    f"Total amount: {totals['amount']} {totals['currency']}",
                    "",
                    "Details:",
                ]
                for a in doc_args["advances"]:
                    lines.append(f"- {a['name']}: {a['amount']} {a['currency']} | Issue: {a['posting_date']} | Due: {a['recovery_due_date']}")
                lines.append("")
                lines.append("This is an automated notice. Please contact HR if you have any questions.")
                lines.append(f"{company} | {notif['date']}")
                message = "\n".join(lines)

            frappe.sendmail(
                recipients=[notification_data["employee_email"]],
                subject=subject,
                message=message,
                sender=sender,
                delayed=True,
                reference_doctype="Employee",
                reference_name=employee,
            )

            notifications_sent += 1
            logger.info(f"Sent advance notice to {employee} <{notification_data['employee_email']}> ({len(advances)} advances)")

        except Exception as e:
            err = f"Error sending notification to {employee}: {e}"
            frappe.log_error(message=err, title="Advance Notification Send Error")
            processing_results["errors"].append(err)

    processing_results["notifications_sent"] = notifications_sent

    # --- HR summary ---
    try:
        hr_users = frappe.get_list("Has Role", filters={"role": "HR User"}, fields=["parent"])
        hr_emails = [u.email for u in frappe.get_list("User",
                          filters={"enabled": 1, "name": ["in", [x["parent"] for x in hr_users]]},
                          fields=["email"]) if u.email]
        if hr_emails:
            sub = f"Advance Notices: {notifications_sent} sent — {format_date(today())}"
            body = (
                f"<p><b>Date:</b> {format_date(today())}</p>"
                f"<p><b>Companies processed:</b> {processing_results.get('processed_companies', 0)}<br>"
                f"<b>Employees notified:</b> {processing_results.get('total_employees_notified', 0)}<br>"
                f"<b>Advances expiring soon:</b> {processing_results.get('total_advances_expiring', 0)}<br>"
                f"<b>Emails sent:</b> {notifications_sent}<br>"
                f"<b>Errors:</b> {len(processing_results.get('errors', []))}</p>"
            )
            frappe.sendmail(recipients=hr_emails, subject=sub, message=body, delayed=True)
    except Exception as e:
        frappe.log_error(message=f"Error sending HR summary: {e}", title="HR Notification Summary Error")

    return notifications_sent

@frappe.whitelist()
def get_expense_claim(
	dt, dn, claim_type, employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount, expense_items 
):
	doc = frappe.get_doc(dt, dn)

	default_payable_account = frappe.get_value(
		"Company", company, "default_expense_claim_payable_account"
	)
	#default_cost_center = frappe.get_value("Company", company, "cost_center")

	expense_claim = frappe.new_doc("Expense Claim")
	expense_claim.company = company
	expense_claim.employee = employee_name
	expense_claim.department = doc.department
	expense_claim.cost_center = doc.custom_cost_center
	expense_claim.project = doc.custom_project
	expense_claim.payable_account = default_payable_account
	expense_claim.custom_claim_type = claim_type

	if doc.mode_of_payment:
		expense_claim.mode_of_payment = doc.mode_of_payment
	else:
		default_mop = frappe.get_value('Company', company,
				'custom_default_expense_claim_mode_of_payment')
		if default_mop:
			expense_claim.mode_of_payment = default_mop

	expense_claim.is_paid = 1 if flt(paid_amount) else 0

	expense_claim.append(
		"advances",
		{
			"employee_advance": employee_advance_name,
			"posting_date": posting_date,
			"advance_paid": flt(paid_amount),
			"unclaimed_amount": flt(paid_amount) - flt(claimed_amount),
			"allocated_amount": flt(paid_amount) - flt(claimed_amount),
		},
	) 

	expense_claim_details = json.loads(expense_items)

	for item in expense_claim_details: 
		expense_claim.append(
			"expenses",
			{
			"expense_date": item['expense_date'] if 'expense_date' in item else None,
			"expense_type": item['expense_type'],
			"description": item['description'] if 'description' in item else None,
			"amount": item['amount'], 
			"cost_center": item['cost_center'] if 'cost_center' in item else None,
			"project": item['project'] if 'project' in item else None,
			"sanctioned_amount": item['sanctioned_amount'] if 'sanctioned_amount' in item else None,

			"custom_receipt_amount": item['amount'],
			"custom_receipt_date": item['expense_date'],   
			},				  
		)

	return expense_claim

@frappe.whitelist()
def get_payment_entry_for_employee(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	"""Function to make Payment Entry for Employee Advance, Gratuity, Expense Claim"""
	doc = frappe.get_doc(dt, dn)

	party_account = get_party_account(doc)
	party_account_currency = get_account_currency(party_account)
	payment_type = "Pay"
	grand_total, outstanding_amount = get_grand_total_and_outstanding_amount(
		doc, party_amount, party_account_currency
	)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = get_paid_amount_and_received_amount(
		doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
	)

	#TODO Find a way to set the title to Employee Name
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = "Employee"
	pe.party = doc.get("employee")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.letter_head = doc.get("letter_head")
	pe.paid_from = bank.account
	pe.paid_to = party_account
	pe.paid_from_account_currency = bank.account_currency
	pe.paid_to_account_currency = party_account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.reference_date = nowdate()
	
	pe.project =  doc.custom_project
	pe.cost_center = doc.custom_cost_center

	#TODO: Support Third Party Payments?
	# if (doc.custom_direct_payment):
	# pe.custom_third_party_payee = 1
	# pe.custom_payee_type = doc.custom_payee_type
	# pe.custom_account_name = doc.custom_account_name
	# pe.custom_account_no = doc.custom_account_no
	#pe.custom_payment_method = doc.custom_payment_method

	pe.custom_remarks = 1
	pe.remarks = doc.purpose

	pe.append(
		"references",
		{
			"reference_doctype": dt,
			"reference_name": dn,
			"bill_no": doc.get("bill_no"),
			"due_date": doc.get("due_date"),
			"total_amount": grand_total,
			"outstanding_amount": outstanding_amount,
			"allocated_amount": outstanding_amount,
		},
	)

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_missing_ref_details()

	if party_account and bank:
		reference_doc = None
		if dt == "Employee Advance":
			reference_doc = doc
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()

	return pe


def get_party_account(doc):
	party_account = None

	if doc.doctype == "Employee Advance":
		party_account = doc.advance_account
	elif doc.doctype in ("Expense Claim", "Gratuity"):
		party_account = doc.payable_account

	return party_account


def get_grand_total_and_outstanding_amount(doc, party_amount, party_account_currency):
	grand_total = outstanding_amount = 0

	if party_amount:
		grand_total = outstanding_amount = party_amount

	elif doc.doctype == "Expense Claim":
		grand_total = flt(doc.total_sanctioned_amount) + flt(doc.total_taxes_and_charges)
		outstanding_amount = flt(doc.grand_total) - flt(doc.total_amount_reimbursed)

	elif doc.doctype == "Employee Advance":
		grand_total = flt(doc.advance_amount)
		outstanding_amount = flt(doc.advance_amount) - flt(doc.paid_amount)
		if party_account_currency != doc.currency:
			grand_total = flt(doc.advance_amount) * flt(doc.exchange_rate)
			outstanding_amount = (flt(doc.advance_amount) - flt(doc.paid_amount)) * flt(doc.exchange_rate)

	elif doc.doctype == "Gratuity":
		grand_total = doc.amount
		outstanding_amount = flt(doc.amount) - flt(doc.paid_amount)

	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)

	return grand_total, outstanding_amount


def get_paid_amount_and_received_amount(
	doc, party_account_currency, bank, outstanding_amount, payment_type, bank_amount
):
	paid_amount = received_amount = 0

	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)

	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				received_amount = paid_amount * doc.get("exchange_rate", 1)

	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get("conversion_rate", 1)
			if doc.doctype == "Employee Advance":
				paid_amount = received_amount * doc.get("exchange_rate", 1)

	return paid_amount, received_amount