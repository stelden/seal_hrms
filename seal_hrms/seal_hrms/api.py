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
def get_employee_contact_details(employee):
    """The employee's Contact, for pre-filling the edit dialog."""
    contact = frappe.db.get_value("Employee", employee, "custom_contact")
    if not contact:
        return None
    return frappe.db.get_value(
        "Contact", contact,
        ["name", "first_name", "middle_name", "last_name", "full_name",
         "mobile_no", "phone", "email_id", "user"],
        as_dict=True,
    )


@frappe.whitelist()
def update_employee_contact(employee, mobile_no=None, first_name=None,
                            middle_name=None, last_name=None):
    """Edit the employee's own Contact in place.

    Addressed by the Employee, not by an email address. The previous version
    looked the Contact up by `Contact.email_id` matching the employee's
    `prefered_email`, which is blank on most records — so the dialog reported
    "No contact found with this email address" for an employee whose Contact was
    sitting right there on the form.

    Edits the linked Contact rather than searching for one, so it can never
    update somebody else's record; the same ownership rule the Employee
    controller enforces is checked again here, because this is a whitelisted
    endpoint and not only reachable from that form.

    The name matters as much as the number: `Contact.full_name` is the account
    name a mobile payment is made out to.
    """
    contact_name = frappe.db.get_value("Employee", employee, "custom_contact")
    if not contact_name:
        frappe.throw(
            _("{0} has no Contact yet. Pick the Contact belonging to their User first.")
            .format(employee),
            title=_("No Contact"),
        )

    _assert_contact_belongs_to_employee(contact_name, employee)

    contact = frappe.get_doc("Contact", contact_name)
    contact.check_permission("write")

    if mobile_no:
        _set_primary_mobile(contact, mobile_no)

    for fieldname, value in (("first_name", first_name),
                             ("middle_name", middle_name),
                             ("last_name", last_name)):
        if value is not None:
            contact.set(fieldname, value.strip())

    if not (contact.first_name or "").strip():
        frappe.throw(_("A contact needs a first name."))

    contact.save(ignore_permissions=True)
    return contact


def _assert_contact_belongs_to_employee(contact, employee):
    """Refuse to edit a Contact that is not this employee's own User's.

    `Contact.user` is not unique and Frappe adopts any Contact whose email
    matches when creating one for a User, so a Supplier's Contact can carry an
    employee's user. Editing the wrong one changes where their money goes.
    """
    user_id = frappe.db.get_value("Employee", employee, "user_id")
    owner = frappe.db.get_value("Contact", contact, "user")
    if not user_id or owner != user_id:
        frappe.throw(
            _("Contact {0} does not belong to {1}'s User.").format(contact, employee),
            title=_("Contact Belongs to Someone Else"),
        )


def _set_primary_mobile(contact, phone_number):
    """Make `phone_number` the Contact's primary mobile.

    Frappe derives the read-only `Contact.mobile_no` from whichever child row
    carries `is_primary_mobile_no`, and blanks it when none does — so the flag
    is the thing being set here, not the parent field.
    """
    normalized = normalize_kenya_mobile_no(phone_number)
    if not normalized or not is_valid_kenya_mobile_no(normalized):
        frappe.throw(_("{0} is not a valid Kenyan mobile number.").format(phone_number))

    for row in contact.phone_nos:
        row.is_primary_mobile_no = 1 if row.phone == normalized else 0

    if not any(row.phone == normalized for row in contact.phone_nos):
        contact.append("phone_nos", {"phone": normalized, "is_primary_mobile_no": 1})

@frappe.whitelist()
def bank_account_exists(account_number, party_type=None, party=None):
    """Whether a Bank Account already holds this account number.

    Scoped to the party when one is given. An unscoped match is too strict to
    block a create: joint and pooled accounts legitimately repeat a number
    across parties, and a global match would refuse the second party outright.
    """
    if not account_number:
        return False

    filters = {"bank_account_no": account_number.strip()}
    if party_type and party:
        filters.update({"party_type": party_type, "party": party})

    return bool(frappe.db.exists("Bank Account", filters))


@frappe.whitelist()
def create_bank_account(
    ref_doctype, ref_name, account_name, account_number, bank,
    iban=None, branch_code=None, company=None,
):
    """Create a party Bank Account that ERPNext's own lookups can find.

    `is_default` is what makes the record usable: ERPNext resolves a party's
    account with `get_party_bank_account`, which filters on
    `{party_type, party, is_default: 1, disabled: 0}`
    (erpnext/accounts/doctype/bank_account/bank_account.py). Without the flag the
    record exists but nothing downstream — Payment Entry, bank file generation,
    reconciliation — can resolve it, which is how employee bank details ended up
    invisible to every payment rail.

    `branch_code` is stored because domestic bank rails require it; `company`
    keeps the record scoped for multi-company sites.
    """
    if bank_account_exists(account_number, ref_doctype, ref_name):
        frappe.throw(_("{0} {1} already has a bank account with this number.").format(
            _(ref_doctype), ref_name
        ))

    # Only the first account for a party may claim the default; a later one would
    # otherwise silently displace the account existing payments already resolve to.
    has_default = frappe.db.exists("Bank Account", {
        "party_type": ref_doctype, "party": ref_name, "is_default": 1,
    })

    return frappe.get_doc({
        "doctype": "Bank Account",
        "account_name": account_name,
        "party_type": ref_doctype,
        "party": ref_name,
        "bank_account_no": account_number,
        "bank": bank,
        "iban": iban,
        "branch_code": branch_code,
        "company": company or _party_company(ref_doctype, ref_name),
        "is_default": 0 if has_default else 1,
    }).insert()


def _party_company(party_type, party):
    """The party's own Company, when its doctype carries one."""
    if not (party_type and party):
        return None
    if not frappe.get_meta(party_type).has_field("company"):
        return None
    return frappe.db.get_value(party_type, party, "company")

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
