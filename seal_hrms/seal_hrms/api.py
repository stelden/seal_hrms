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

    if contact_exists(phone_number=normalized):
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


@frappe.whitelist()
def update_contact(phone_number, email_id):
    # Validate inputs
    normalized = normalize_kenya_mobile_no(phone_number)
    if not normalized or not is_valid_kenya_mobile_no(normalized):
        frappe.throw(_("Invalid Kenyan mobile number."))
    
    if email_id and not validate_email_address(email_id):
        frappe.throw(_("Invalid email address."))
    
    if not contact_exists(email_id=email_id):
        frappe.throw(_("No contact found with this email address."))
    
    # Fetch the most recently modified contact with the given email. We expect only one
    contacts = frappe.get_all("Contact", filters={"email_id": email_id}, order_by="modified desc", limit=1)
    
    contact = contacts and frappe.get_doc("Contact", contacts[0].name) or None

    if contact:
        existing_phones = [phone.phone for phone in contact.phone_nos]

        if normalized not in existing_phones:
            # If adding a new phone, mark all existing as non-primary
            for phone in contact.phone_nos:
                phone.is_primary_mobile_no = 0

            contact.append("phone_nos", {
                "phone": normalized,
                "is_primary_mobile_no": 1
            })
        else:
            # If the phone already exists, ensure it's marked as primary
            for phone in contact.phone_nos:
                if phone.phone == normalized:
                    phone.is_primary_mobile_no = 1
                else:
                    phone.is_primary_mobile_no = 0

        contact.save(ignore_permissions=True)
                
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
