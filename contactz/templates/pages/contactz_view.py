"""
Contactz Dashboard View
Custom public/authenticated view for contacts
URL: /contactz/view/{doctype}/{document_name}
"""

import frappe
from frappe import _
from contactz.utils.phone_formatter import format_phone_international


def get_context(context):
	"""
	Build context for contact dashboard page

	Args:
		context: Page context object

	Returns:
		Context dict with contact information
	"""
	# Get URL parameters
	doctype = frappe.form_dict.get('doctype')
	document_name = frappe.form_dict.get('document_name')

	# Validate inputs
	if not doctype or not document_name:
		frappe.throw(_("Invalid URL: Missing doctype or document name"))

	# Validate doctype
	allowed_doctypes = ['Contact', 'Employee', 'Customer', 'Supplier', 'Lead']
	if doctype.title() not in allowed_doctypes:
		frappe.throw(_("Invalid doctype: {0}").format(doctype))

	doctype = doctype.title()  # Normalize to title case

	# Check if document exists
	if not frappe.db.exists(doctype, document_name):
		frappe.throw(_("{0} not found: {1}").format(doctype, document_name))

	try:
		# Get document
		doc = frappe.get_doc(doctype, document_name)

		# Optional: Check permissions (comment out for public access)
		# if not frappe.has_permission(doctype, 'read', doc):
		#     frappe.throw(_("Insufficient permissions"))

		# Build base context
		context.doc = doc
		context.doctype = doctype
		context.document_name = document_name
		context.format_phone = format_phone_international

		# Add doctype-specific data
		if doctype == 'Contact':
			_add_contact_context(context, doc, document_name)

		elif doctype == 'Employee':
			_add_employee_context(context, doc)

		elif doctype == 'Customer':
			_add_customer_context(context, doc, document_name)

		elif doctype == 'Supplier':
			_add_supplier_context(context, doc, document_name)

		elif doctype == 'Lead':
			_add_lead_context(context, doc)

		# Add common context
		context.title = f"{doctype}: {document_name}"
		context.no_cache = 1

	except Exception as e:
		frappe.log_error(
			title=f"Contactz Dashboard Error: {doctype}/{document_name}",
			message=frappe.get_traceback()
		)
		frappe.throw(_("Error loading contact information: {0}").format(str(e)))

	return context


def _add_contact_context(context, doc, document_name):
	"""Add Contact-specific context"""
	# Get linked entities (Customer, Supplier, Lead)
	links = frappe.get_all(
		'Dynamic Link',
		filters={'parent': document_name, 'parenttype': 'Contact'},
		fields=['link_doctype', 'link_name', 'link_title']
	)
	context.linked_entities = links

	# Get addresses
	addresses = frappe.get_all(
		'Dynamic Link',
		filters={'link_doctype': 'Contact', 'link_name': document_name, 'parenttype': 'Address'},
		fields=['parent as address_name']
	)

	address_details = []
	for addr in addresses:
		addr_doc = frappe.get_doc('Address', addr.address_name)
		address_details.append(addr_doc)

	context.addresses = address_details


def _add_employee_context(context, doc):
	"""Add Employee-specific context"""
	context.employee_name = doc.employee_name
	context.department = doc.department
	context.designation = doc.designation
	context.company = doc.company


def _add_customer_context(context, doc, document_name):
	"""Add Customer-specific context"""
	# Get linked contacts
	contacts = frappe.get_all(
		'Dynamic Link',
		filters={'link_doctype': 'Customer', 'link_name': document_name, 'parenttype': 'Contact'},
		fields=['parent as contact_name']
	)

	contact_details = []
	for cont in contacts:
		try:
			cont_doc = frappe.get_doc('Contact', cont.contact_name)
			contact_details.append(cont_doc)
		except:
			pass

	context.contacts = contact_details


def _add_supplier_context(context, doc, document_name):
	"""Add Supplier-specific context"""
	# Get linked contacts
	contacts = frappe.get_all(
		'Dynamic Link',
		filters={'link_doctype': 'Supplier', 'link_name': document_name, 'parenttype': 'Contact'},
		fields=['parent as contact_name']
	)

	contact_details = []
	for cont in contacts:
		try:
			cont_doc = frappe.get_doc('Contact', cont.contact_name)
			contact_details.append(cont_doc)
		except:
			pass

	context.contacts = contact_details


def _add_lead_context(context, doc):
	"""Add Lead-specific context"""
	context.lead_name = doc.lead_name
	context.company_name = doc.company_name
	context.status = doc.status
