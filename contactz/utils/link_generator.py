"""
Link Generator
Generate URLs for ERPNext desk forms and custom dashboard views
"""

import frappe
from urllib.parse import quote


def generate_desk_link(doctype, document_name):
    """
    Generate ERPNext desk form URL

    Args:
        doctype: DocType name (e.g., 'Contact', 'Employee')
        document_name: Document ID/name

    Returns:
        Full URL to ERPNext desk form

    Examples:
        >>> generate_desk_link('Contact', '-CUST-21033')
        'https://erpnext.itsdave.de/app/contact/-CUST-21033'
        >>> generate_desk_link('Employee', 'EMP/0001')
        'https://erpnext.itsdave.de/app/employee/EMP%2F0001'
    """
    if not doctype or not document_name:
        return ""

    site_url = frappe.utils.get_url()

    # URL encode the document name (handles special characters like /, -, etc.)
    encoded_name = quote(str(document_name), safe='')

    # DocType in URL should be lowercase
    doctype_lower = str(doctype).lower()

    return f"{site_url}/app/{doctype_lower}/{encoded_name}"


def generate_dashboard_link(doctype, document_name):
    """
    Generate custom dashboard URL

    Args:
        doctype: DocType name
        document_name: Document ID/name

    Returns:
        Full URL to custom dashboard view

    Examples:
        >>> generate_dashboard_link('Contact', '-CUST-21033')
        'https://erpnext.itsdave.de/contactz/view/contact/-CUST-21033'
        >>> generate_dashboard_link('Employee', 'EMP/0001')
        'https://erpnext.itsdave.de/contactz/view/employee/EMP%2F0001'
    """
    if not doctype or not document_name:
        return ""

    site_url = frappe.utils.get_url()

    # URL encode the document name
    encoded_name = quote(str(document_name), safe='')

    # DocType in URL should be lowercase
    doctype_lower = str(doctype).lower()

    return f"{site_url}/contactz/view/{doctype_lower}/{encoded_name}"


def generate_links(doctype, document_name):
    """
    Generate both desk and dashboard links at once

    Args:
        doctype: DocType name
        document_name: Document ID/name

    Returns:
        Tuple of (desk_link, dashboard_link)
    """
    return (
        generate_desk_link(doctype, document_name),
        generate_dashboard_link(doctype, document_name)
    )


def get_site_url():
    """
    Get the current site URL

    Returns:
        Site URL (e.g., 'https://erpnext.itsdave.de')
    """
    return frappe.utils.get_url()
