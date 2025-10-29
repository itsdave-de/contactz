"""
Contactz API
Public API endpoints for manual triggers and dashboard access
"""

import frappe
from contactz.tasks import export_telefonbuch_csv


@frappe.whitelist()
def trigger_telefonbuch_export():
    """
    Manual trigger for Telefonbuch CSV export

    Accessible via: /api/method/contactz.api.trigger_telefonbuch_export

    Returns:
        dict: Status and file URL or error message
    """
    # Check permissions
    if not frappe.has_permission("File", "write"):
        frappe.throw("Insufficient permissions to trigger export")

    try:
        file_url = export_telefonbuch_csv()

        if file_url:
            return {
                "status": "success",
                "message": "Telefonbuch.csv generated successfully",
                "file_url": file_url,
                "timestamp": frappe.utils.now()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to generate Telefonbuch.csv. Check Error Log for details.",
                "timestamp": frappe.utils.now()
            }

    except Exception as e:
        frappe.log_error(
            title="Manual Telefonbuch Export Failed",
            message=frappe.get_traceback()
        )

        return {
            "status": "error",
            "message": str(e),
            "timestamp": frappe.utils.now()
        }


@frappe.whitelist()
def get_export_status():
    """
    Get status of last Telefonbuch export

    Returns:
        dict: File information and last export time
    """
    try:
        # Get the Telefonbuch.csv file
        file_info = frappe.db.get_value(
            "File",
            {"file_name": "Telefonbuch.csv", "is_private": 0},
            ["name", "file_url", "file_size", "modified"],
            as_dict=True
        )

        if file_info:
            return {
                "status": "success",
                "file_exists": True,
                "file_name": "Telefonbuch.csv",
                "file_url": file_info.file_url,
                "file_size": file_info.file_size,
                "last_updated": file_info.modified
            }
        else:
            return {
                "status": "success",
                "file_exists": False,
                "message": "Telefonbuch.csv has not been generated yet"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_contact_view(doctype, document_name):
    """
    Get contact information for dashboard view
    This can be made public (allow_guest=True) or restricted

    Args:
        doctype: DocType name (Contact, Employee, Customer, etc.)
        document_name: Document ID

    Returns:
        dict: Contact information
    """
    try:
        # Validate doctype
        allowed_doctypes = ['Contact', 'Employee', 'Customer', 'Supplier', 'Lead']
        if doctype not in allowed_doctypes:
            frappe.throw(f"Invalid doctype: {doctype}")

        # Check if document exists
        if not frappe.db.exists(doctype, document_name):
            frappe.throw(f"{doctype} {document_name} not found")

        # Get document
        doc = frappe.get_doc(doctype, document_name)

        # Check permissions (optional - comment out for public access)
        # if not frappe.has_permission(doctype, 'read', doc):
        #     frappe.throw("Insufficient permissions")

        # Build response based on doctype
        response = {
            "status": "success",
            "doctype": doctype,
            "document_name": document_name
        }

        if doctype == "Contact":
            response.update({
                "first_name": doc.first_name,
                "last_name": doc.last_name,
                "email": doc.email_id,
                "phone": doc.phone,
                "mobile": doc.mobile_no,
                "designation": doc.designation,
                "company_name": doc.company_name
            })

            # Get linked entities
            links = frappe.get_all(
                'Dynamic Link',
                filters={'parent': document_name, 'parenttype': 'Contact'},
                fields=['link_doctype', 'link_name', 'link_title']
            )
            response["linked_entities"] = links

        elif doctype == "Employee":
            response.update({
                "employee_name": doc.employee_name,
                "first_name": doc.first_name,
                "last_name": doc.last_name,
                "email": doc.company_email or doc.personal_email,
                "mobile": doc.cell_number,
                "designation": doc.designation,
                "department": doc.department,
                "company": doc.company
            })

        elif doctype in ["Customer", "Supplier"]:
            name_field = "customer_name" if doctype == "Customer" else "supplier_name"
            response.update({
                "name": doc.get(name_field),
                "type": doc.get(f"{doctype.lower()}_type")
            })

        return response

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
