# Copyright (c) 2024, Stelden EA Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def on_submit(doc, method=None):
    """
    Validate expense claim receipt requirements based on company settings
    """
    if not doc.company:
        return
    
    # Fetch company receipt requirement settings
    try:
        company = frappe.get_doc("Company", doc.company)
        company_settings = {
            'receipt_doc': getattr(company, 'custom_require_ec_receipt_doc', 0),
            'receipt_date': getattr(company, 'custom_require_ec_receipt_date', 0),
            'receipt_no': getattr(company, 'custom_require_ec_receipt_no', 0),
            'receipt_amount': getattr(company, 'custom_require_ec_receipt_amount', 0)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching company settings for {doc.company}: {str(e)}")
        company_settings = {
            'receipt_doc': 0,
            'receipt_date': 0,
            'receipt_no': 0,
            'receipt_amount': 0
        }
    
    # If no receipt requirements are set, skip validation
    if not any(company_settings.values()):
        return
    
    # Validate receipt requirements for each expense detail row
    missing_fields = []
    
    for idx, expense_detail in enumerate(doc.expenses, 1):  # Using 1-based indexing for user-friendly row numbers
        row_missing_fields = validate_expense_detail(expense_detail, company_settings, idx)
        if row_missing_fields:
            missing_fields.extend(row_missing_fields)
    
    # If any required fields are missing, throw validation error
    if missing_fields:
        error_message = get_error_message(missing_fields)
        frappe.throw(msg=error_message, title=_("Required Receipt Information"))

def validate_expense_detail(expense_detail, settings, row_no):
    """
    Validate a single expense detail row against company requirements
    Returns list of missing field information
    """
    missing_fields = []
    
    # Field mapping: company_setting -> (child_table_field, display_name)
    field_mappings = {
        'receipt_doc': ('custom_receipt', 'Receipt Document'),
        'receipt_date': ('custom_receipt_date', 'Receipt Date'),
        'receipt_no': ('custom_receipt_no', 'Receipt Number'),
        'receipt_amount': ('custom_receipt_amount', 'Receipt Amount')
    }
    
    for setting_key, (field_name, display_name) in field_mappings.items():
        # If company requires this field
        if settings.get(setting_key):
            field_value = getattr(expense_detail, field_name, None)
            
            # Check if field is empty/missing
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                missing_fields.append({
                    'row': row_no,
                    'field': display_name,
                    'field_name': field_name
                })
    
    return missing_fields

def get_error_message(missing_fields):
    """
    User-friendly error message for missing required receipt fields
    """
    if not missing_fields:
        return ""
    
    # Group missing fields by row for better readability
    rows_with_missing_fields = {}
    for field_info in missing_fields:
        row = field_info['row']
        if row not in rows_with_missing_fields:
            rows_with_missing_fields[row] = []
        rows_with_missing_fields[row].append(field_info['field'])
    
    # Build error message
    error_lines = [_("The following required receipt information is missing:")]
    error_lines.append("")
    error_lines.append("")
    
    for row, fields in sorted(rows_with_missing_fields.items()):
        field_list = ", ".join(fields)
        error_lines.append(_("Row {0}: {1}").format(row, field_list))
    
    error_lines.append("")
    error_lines.append("")
    error_lines.append(_("Please provide all required receipt information before submitting."))
    
    return "\n".join(error_lines)