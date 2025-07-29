import frappe
from frappe import _
from frappe.utils.data import today
from frappe.utils import validate_email_address
from seal_common.seal_common.mno import normalize_kenya_mobile_no, is_valid_kenya_mobile_no

@frappe.whitelist()
def get_current_user_full_name():
    user = frappe.session.user
    return frappe.utils.get_fullname(user)

@frappe.whitelist()
def get_user_for_employee(employee_id):
    if employee_id:
        employee = frappe.get_doc('Employee', employee_id)
        
        user_id = employee.user_id
        
        if user_id:
            user = frappe.get_doc('User', user_id)
            
            return user
        

@frappe.whitelist()
def get_employee_contacts(doctype, txt, searchfield, start, page_len, filters):
    email = filters.get('email')
    
    if not email:
        return []
    
    return frappe.db.sql("""
        SELECT name, full_name, email_id, mobile_no, phone
        FROM `tabContact`
        WHERE email_id = %s AND (mobile_no != '' OR phone != '')
        ORDER BY
            IF(LENGTH(first_name) > 0, 1, 0) DESC,
            first_name ASC
        LIMIT 0, 20        
    """, (email,)) #, as_dict=True


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_contacts_with_mobile(doctype, txt, searchfield, start, page_len, filters):
    link_doctype = filters.get("link_doctype")
    link_name = filters.get("link_name")

    if not link_doctype or not link_name:
        return []

    return frappe.db.sql(f"""
        SELECT
            contact.name, contact.full_name
        FROM
            `tabContact` contact
        INNER JOIN
            `tabDynamic Link` link ON link.parent = contact.name
        WHERE
            link.link_doctype = %s
            AND link.link_name = %s
            AND (contact.mobile_no IS NOT NULL AND contact.mobile_no != '')
            AND contact.{searchfield} LIKE %s
        ORDER BY
            contact.name ASC
        LIMIT %s OFFSET %s
    """, (link_doctype, link_name, f"%{txt}%", page_len, start))

@frappe.whitelist()
def contact_exists(phone_number=None, email_id=None):
    phone_number = phone_number.strip() if phone_number else None
    email_id = email_id.strip().lower() if email_id else None

    if not phone_number and not email_id:
        return False

    phone_match = email_match = False

    if phone_number:
        phone_match = frappe.db.exists("Contact Phone", {"phone": phone_number})

    if email_id:
        email_match = frappe.db.exists("Contact Email", {"email_id": email_id})

    return bool(phone_match or email_match)


@frappe.whitelist()
def create_contact(ref_doctype, ref_name, contact_name, phone_number, email_id=None):
    normalized = normalize_kenya_mobile_no(phone_number)

    if not normalized or not is_valid_kenya_mobile_no(normalized):
        frappe.throw(_("Invalid Kenyan mobile number."))

    if email_id and not validate_email_address(email_id):
        frappe.throw(_("Invalid email address."))

    if contact_exists(normalized):
        frappe.throw(_("A contact with this phone number already exists."))

    first_name, middle_name, last_name = split_name(contact_name)

    contact_doc = {
        "doctype": "Contact",
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "is_billing_contact": 1,
        "is_primary_contact": 1,
        "phone_nos": [{
            "phone": normalized,
            "is_primary_mobile_no": 1
        }]
    }

    # Only add link if not Employee
    if ref_doctype.lower() != "employee":
        contact_doc["links"] = [{
            "link_doctype": ref_doctype,
            "link_name": ref_name
        }]

    if email_id:
        contact_doc["email_ids"] = [{
            "email_id": email_id,
            "is_primary": 1
        }]

    contact = frappe.get_doc(contact_doc).insert()

    return contact

# def create_contact(ref_doctype, ref_name, contact_name, phone_number, email_id=None):
#     normalized = normalize_kenya_mobile_no(phone_number)

#     if not normalized or not is_valid_kenya_mobile_no(normalized):
#         frappe.throw(_("Invalid Kenyan mobile number."))

#     if email_id and not validate_email_address(email_id):
#         frappe.throw(_("Invalid email address."))

#     if contact_exists(normalized):
#         frappe.throw(_("A contact with this phone number already exists."))

#     first_name, middle_name, last_name = split_name(contact_name)

#     contact_doc = {
#         "doctype": "Contact",
#         "first_name": first_name,
#         "middle_name": middle_name,
#         "last_name": last_name,
#         "is_billing_contact": 1,
#         "is_primary_contact": 1,
#         "links": [{
#             "link_doctype": ref_doctype,
#             "link_name": ref_name
#         }],
#         "phone_nos": [{
#             "phone": normalized,
#             "is_primary_mobile_no": 1
#         }]
#     }

#     if email_id:
#         contact_doc["email_ids"] = [{
#             "email_id": email_id,
#             "is_primary": 1
#         }]

#     contact = frappe.get_doc(contact_doc).insert()
    
#     return contact

@frappe.whitelist()
def bank_account_exists(account_number):
    if not account_number:
        return False

    account_number = account_number.strip()

    account_exists = frappe.db.exists("Bank Account", {"bank_account_no": account_number})

    return bool(account_exists)

@frappe.whitelist()
def create_bank_account(ref_doctype, ref_name, account_name, account_number, bank, iban=None):
    if bank_account_exists(account_number):
        frappe.throw(_("A bank account with this number already exists."))

    bank_account = frappe.get_doc({
        "doctype": "Bank Account",
        "account_name": account_name,
        "party_type": ref_doctype,
        "party": ref_name,
        "bank_account_no": account_number,
        "bank": bank,
        "iban": iban
    }).insert()

    return bank_account

def split_name(full_name: str):
    parts = full_name.strip().split()

    if len(parts) == 0:
        return '', '', ''
    elif len(parts) == 1:
        return parts[0], '', ''
    elif len(parts) == 2:
        return parts[0], '', parts[1]
    else:
        return parts[0], ' '.join(parts[1:-1]), parts[-1]

@frappe.whitelist()
def get_payee_account_details(moptype: str, doctype: str, docname: str):
    def get_field_label(fieldname: str, meta) -> str:
        """Helper function to get proper field label from fieldname"""
        # Try to get label from meta first
        df = meta.get_field(fieldname)
        if df and df.label:
            return df.label
        
        # Clean up custom field names
        if fieldname.startswith('custom_'):
            fieldname = fieldname[7:]  # Remove 'custom_' prefix
        
        # Convert to title case with spaces
        return fieldname.replace('_', ' ').title()

    # Validate input parameters
    if not moptype or not doctype or not docname:
        frappe.throw(_("Missing required parameters: moptype, doctype, or docname"))
    
    if moptype not in ("Bank", "Phone", "Cash"):
        frappe.throw(_("Unsupported Mode of Payment Type: {0}. Must be 'Bank', 'Phone', or 'Cash'").format(moptype))
    
    if doctype not in ("Employee", "Supplier"):
        frappe.throw(_("Unsupported DocType: {0}. Must be 'Employee' or 'Supplier'").format(doctype))
    
    # Get the payee document
    try:
        payee_doc = frappe.get_doc(doctype, docname)
    except frappe.DoesNotExistError:
        frappe.throw(_("{0} {1} not found").format(doctype, docname))
    
    # Define field mapping based on doctype and mode of payment
    field_mapping = {
        "Employee": {
            "Bank": {
                "account_name": "employee_name",
                "account_no": "bank_ac_no",
                "account_provider": "bank_name"
            },
            "Phone": {
                "account_name": "employee_name",
                "account_no": "cell_number",
                "account_provider": "custom_cell_number_provider"
            },
            "Cash": {
                "account_name": "employee_name",
                "account_no": "custom_national_id",
                "account_provider": "Cashier"
            }
        },
        "Supplier": {
            "Bank": {
                "account_name": "custom_payment_bank_account_name",
                "account_no": "custom_payment_bank_account_no",
                "account_provider": "custom_payment_bank_name"
            },
            "Phone": {
                "account_name": "custom_payment_contact_name",
                "account_no": "custom_payment_contact_no",
                "account_provider": "custom_custom_payment_contact_no_provider"
            },
            "Cash": {
                "account_name": "supplier_name",
                "account_no": "tax_id",
                "account_provider": "Cashier"
            }
        }
    }
    
    # Get the field names for the specific doctype and mop_type
    fields = field_mapping.get(doctype, {}).get(moptype, {})
    if not fields:
        frappe.throw(_("No field mapping found for {0} with Mode of Payment {1}").format(doctype, moptype))

    # Prepare result and track missing fields
    result = {}
    missing_fields = []
    meta = frappe.get_meta(doctype)
    
    # Get field values
    for target_field, source_field in fields.items():
        if source_field == "Cashier":  # Static value
            result[target_field] = "Cashier"
            continue
            
        # Check if field exists in the doctype
        if not meta.has_field(source_field):
            field_label = get_field_label(source_field, meta)
            missing_fields.append(field_label)
            continue
            
        value = payee_doc.get(source_field)
        if value is None or value == "":
            field_label = get_field_label(source_field, meta)
            missing_fields.append(field_label)
            continue
            
        result[target_field] = value
    
    # Check for missing fields
    if missing_fields:
        frappe.throw(_("{0} <b>{1}</b> is missing the following required for <b>{2}</b> disbursement:<br><br><b>{3}</b><br><br>Please update the {4} record.").format(
            doctype, docname, moptype, "<br>".join(missing_fields), doctype
        ))
    
    # Return the result in the expected format
    return {
        "custom_account_name": result.get("account_name"),
        "custom_account_no": result.get("account_no"),
        "custom_account_provider": result.get("account_provider")
    }