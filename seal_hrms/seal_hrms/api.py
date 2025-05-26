import frappe
from frappe import _
from frappe.utils.data import today

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
def bank_account_exists(account_number):
    if not account_number:
        return False

    account_number = account_number.strip()

    account_exists = frappe.db.exists("Bank Account", {"bank_account_no": account_number})

    return bool(account_exists)

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