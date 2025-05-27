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
def contact_exists(phone_number):
    if not phone_number:
        return False

    phone_number = phone_number.strip()

    mobile_exists = frappe.db.exists("Contact", {"mobile_no": phone_number})
    phone_exists = frappe.db.exists("Contact", {"phone": phone_number})

    return bool(mobile_exists or phone_exists)


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
        "links": [{
            "link_doctype": ref_doctype,
            "link_name": ref_name
        }],
        "phone_nos": [{
            "phone": normalized,
            "is_primary_mobile_no": 1
        }]
    }

    if email_id:
        contact_doc["email_ids"] = [{
            "email_id": email_id,
            "is_primary": 1
        }]

    contact = frappe.get_doc(contact_doc).insert()
    
    return contact

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

def get_field_values(source_doc, field_map):
    return {
        "custom_account_name": source_doc.get(field_map.get("account_name")),
        "custom_account_no": source_doc.get(field_map.get("account_no")),
        "custom_account_provider": source_doc.get(field_map.get("account_provider"))
    }

@frappe.whitelist()
def get_payee_account_details(mop_type: str, doctype: str, docname: str):
    doc = frappe.get_doc(doctype, docname)

    if not mop_type or not doctype or not docname:
        frappe.throw(_("Required parameters are missing: mop_type, doctype, or docname"))

    # Map of fields based on Doctype and MoP Type
    field_configs = {
        "Employee": {
            "Phone": {
                "account_name": "employee_name",
                "account_no": "cell_number",
                "account_provider": "custom_cell_number_provider"
            },
            "Bank": {
                "account_name": "employee_name",
                "account_no": "bank_ac_no",
                "account_provider": "bank_name"
            },
        },
        "Supplier": {
            "Phone": {
                "account_name": "custom_payment_contact_name",
                "account_no": "custom_payment_contact_no",
                "account_provider": "custom_custom_payment_contact_no_provider"
            },
            "Bank": {
                "account_name": "custom_payment_bank_account_name",
                "account_no": "custom_payment_bank_account_no",
                "account_provider": "custom_payment_bank_name"
            },
        }
    }

    if mop_type == "Cash" or mop_type == "General":
        return {
            "custom_account_name": doc.get("employee_name" if doctype == "Employee" else doc.get("supplier_name")),
            "custom_account_no": doc.get("custom_national_id") or doc.get("custom_passport_no"),
            "custom_account_provider": "Cashier"
        }

    config = field_configs.get(doctype, {}).get(mop_type)
    if not config:
        frappe.throw(_(f"Unsupported Mode of Payment Type '{mop_type}' for doctype '{doctype}'"))

    result = get_field_values(doc, config)

    if not all(result.values()):
        missing = [k for k, v in result.items() if not v]
        frappe.throw(_(f"Missing required field(s) for disbursement: {', '.join(missing)}"))

    return result



# @frappe.whitelist()
# def get_preferred_payment_method(custom_payee_type, custom_payee):
#     if not custom_payee_type or not custom_payee:
#         return None

#     custom_preferred_payment_method = None
#     contact_name = None
#     bank_account_name = None

#     if custom_payee_type == 'Supplier':
#         payee_doc = frappe.get_doc('Supplier', custom_payee, ['custom_preferred_payment_method', 'custom_mpesa_contact', 'custom_bank_account'])
#         custom_preferred_payment_method = payee_doc.get('custom_preferred_payment_method')
#         contact_name = payee_doc.get('custom_mpesa_contact')
#         bank_account_name = payee_doc.get('custom_bank_account')

#     elif custom_payee_type == 'Employee':
#         payee_doc = frappe.get_doc('Employee', custom_payee, ['custom_preferred_payment_method', 'custom_mpesa_contact', 'custom_bank_account'])
#         custom_preferred_payment_method = payee_doc.get('custom_preferred_payment_method')
#         contact_name = payee_doc.get('custom_mpesa_contact')
#         bank_account_name = payee_doc.get('custom_bank_account')

#     if not custom_preferred_payment_method:
#         return None

#     if custom_preferred_payment_method == 'Mpesa' and contact_name:
#         contact_doc = frappe.get_doc('Contact', contact_name)

#         if contact_doc.full_name and (contact_doc.mobile_no or contact_doc.phone):
#             return contact_doc.as_dict()
#         else:
#             frappe.throw(frappe._(
#             "Contact '{0}' for {1} '{2}' has no Name or valid phone number."
#             ).format(contact_name, custom_payee_type, custom_payee))

#     elif custom_preferred_payment_method == 'Cheque' and bank_account_name:
#         bank_account_doc = frappe.get_doc('Bank Account', bank_account_name)
#         if not bank_account_doc.account_name or not bank_account_doc.bank_account_no:
#             frappe.throw(frappe._(
#                 "Bank Account '{0}' for {1} '{2}' has no Account Name or Account Number."
#             ).format(bank_account_name, custom_payee_type, custom_payee))
        
#         return bank_account_doc.as_dict()

#     return None