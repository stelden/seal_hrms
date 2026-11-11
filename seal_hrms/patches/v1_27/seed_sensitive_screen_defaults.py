# Copyright (c) 2026, Stelden EA Ltd and contributors
# For license information, please see license.txt

"""Write the "Confirm It Is You" defaults into SEAL HRMS Settings on sites that predate them.

A Check added to an existing Single reads 0 until the Single is saved, so without this the
form would show payslips as not asking while the server asks (it reads a never-saved switch
as its default), and the first save of the form would quietly turn the checks off. Only
values the site has never saved are written.
"""

from seal_hrms.seal_hrms.sensitive import seed_defaults


def execute():
	seed_defaults()
