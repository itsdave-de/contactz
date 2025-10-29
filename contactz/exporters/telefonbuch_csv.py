"""
Telefonbuch CSV Exporter - Simplified Version
Fixed version without Cartesian product issues
"""

import frappe
import csv
from io import StringIO
from contactz.exporters.base import BaseContactExporter
from contactz.utils.phone_formatter import format_phone_international
from contactz.utils.link_generator import generate_desk_link, generate_dashboard_link


class TelefonbuchCSVExporter(BaseContactExporter):
    """
    Export contacts to Telefonbuch CSV format - Simplified version
    Uses Python to combine data instead of complex SQL joins
    """

    def get_file_name(self):
        return "Telefonbuch.csv"

    def fetch_data(self):
        """
        Fetch contact data using simplified approach:
        1. Fetch all contacts with entity links (filtered by enabled sources)
        2. Fetch employees separately (if enabled)
        3. Fetch addresses separately
        4. Combine in Python
        """
        # Get enabled sources from settings
        from contactz.contactz.doctype.contactz_settings.contactz_settings import get_enabled_sources
        enabled_sources = get_enabled_sources()

        # Fetch contacts with entity links (filtered)
        contacts = self._fetch_contacts(enabled_sources)

        # Fetch employees (if enabled)
        employees = []
        if enabled_sources.get('employee'):
            employees = self._fetch_employees()

        # Combine
        all_data = contacts + employees

        frappe.logger().info(f"Telefonbuch: Fetched {len(contacts)} contacts + {len(employees)} employees = {len(all_data)} total")
        frappe.logger().info(f"Enabled sources: Customer={enabled_sources.get('customer')}, Supplier={enabled_sources.get('supplier')}, Lead={enabled_sources.get('lead')}, Employee={enabled_sources.get('employee')}")

        return all_data

    def _fetch_contacts(self, enabled_sources):
        """Fetch contacts with linked entities and ONE address per link (filtered by enabled sources)"""
        # Build list of enabled entity types
        entity_types = []
        if enabled_sources.get('customer'):
            entity_types.append('Customer')
        if enabled_sources.get('supplier'):
            entity_types.append('Supplier')
        if enabled_sources.get('lead'):
            entity_types.append('Lead')

        # If no contact sources enabled, return empty list
        if not entity_types:
            frappe.logger().info("Telefonbuch: No contact sources enabled (Customer/Supplier/Lead all disabled)")
            return []

        # Format for SQL IN clause
        entity_types_placeholders = ', '.join(['%s'] * len(entity_types))

        query = f"""
            SELECT DISTINCT
                'Contact' as source_type,
                c.name as source_id,
                COALESCE(c.first_name, '') as first_name,
                COALESCE(c.last_name, '') as last_name,
                c.salutation,
                c.gender,
                c.designation,
                c.company_name,
                c.phone,
                c.mobile_no,
                c.email_id,
                NULL as date_of_birth,
                c.modified,

                dl.link_doctype,
                dl.link_name,
                COALESCE(cust.customer_name, supp.supplier_name, lead.company_name) as entity_name,
                cust.customer_type,
                supp.supplier_type

            FROM tabContact c

            LEFT JOIN `tabDynamic Link` dl
                ON dl.parent = c.name
                AND dl.parenttype = 'Contact'
                AND dl.link_doctype IN ({entity_types_placeholders})

            LEFT JOIN tabCustomer cust
                ON dl.link_doctype = 'Customer'
                AND dl.link_name = cust.name
            LEFT JOIN tabSupplier supp
                ON dl.link_doctype = 'Supplier'
                AND dl.link_name = supp.name
            LEFT JOIN tabLead lead
                ON dl.link_doctype = 'Lead'
                AND dl.link_name = lead.name

            WHERE c.docstatus = 0
            AND (
                (COALESCE(c.first_name, '') != '' OR COALESCE(c.last_name, '') != '' OR COALESCE(c.company_name, '') != '')
                AND (c.email_id IS NOT NULL OR c.phone IS NOT NULL OR c.mobile_no IS NOT NULL)
            )
        """

        contacts = frappe.db.sql(query, tuple(entity_types), as_dict=True)

        # Get addresses for each contact (ONE address per entity)
        for contact in contacts:
            if contact['link_name']:
                # Get ONE primary address for the linked entity
                address = self._get_primary_address(contact['link_doctype'], contact['link_name'])
                contact.update(address)

        return contacts

    def _fetch_employees(self):
        """Fetch active employees (requires HRMS app)"""
        try:
            query = """
                SELECT
                    'Employee' as source_type,
                    e.name as source_id,
                    COALESCE(e.first_name, e.employee_name) as first_name,
                    COALESCE(e.last_name, '') as last_name,
                    e.salutation,
                    e.gender,
                    e.designation,
                    e.company as company_name,
                    NULL as phone,
                    e.cell_number as mobile_no,
                    COALESCE(e.company_email, e.personal_email) as email_id,
                    e.date_of_birth,
                    e.modified,

                    'Employee' as link_doctype,
                    e.name as link_name,
                    e.employee_name as entity_name,
                    NULL as customer_type,
                    NULL as supplier_type,

                    '' as personal_addr_line1,
                    '' as personal_addr_line2,
                    '' as personal_pincode,
                    '' as personal_city,
                    '' as personal_phone,
                    '' as personal_fax,
                    '' as business_addr_line1,
                    '' as business_pincode,
                    '' as business_city,
                    '' as business_phone,
                    '' as business_fax,
                    '' as business_email

                FROM tabEmployee e
                WHERE e.status = 'Active'
                AND (
                    (COALESCE(e.first_name, e.employee_name, '') != '')
                    AND (e.company_email IS NOT NULL OR e.personal_email IS NOT NULL OR e.cell_number IS NOT NULL)
                )
            """

            return frappe.db.sql(query, as_dict=True)
        except Exception as e:
            # HRMS not installed or Employee table doesn't exist
            frappe.logger().warning(f"Could not fetch employees: {str(e)}. HRMS app may not be installed.")
            return []

    def _get_primary_address(self, doctype, docname):
        """Get ONE primary address for an entity"""
        query = """
            SELECT
                addr.address_line1 as personal_addr_line1,
                addr.address_line2 as personal_addr_line2,
                addr.pincode as personal_pincode,
                addr.city as personal_city,
                addr.phone as personal_phone,
                addr.fax as personal_fax,
                CASE WHEN addr.address_type = 'Billing' THEN addr.address_line1 ELSE '' END as business_addr_line1,
                CASE WHEN addr.address_type = 'Billing' THEN addr.pincode ELSE '' END as business_pincode,
                CASE WHEN addr.address_type = 'Billing' THEN addr.city ELSE '' END as business_city,
                CASE WHEN addr.address_type = 'Billing' THEN addr.phone ELSE '' END as business_phone,
                CASE WHEN addr.address_type = 'Billing' THEN addr.fax ELSE '' END as business_fax,
                CASE WHEN addr.address_type = 'Billing' THEN addr.email_id ELSE '' END as business_email
            FROM `tabDynamic Link` dl
            INNER JOIN tabAddress addr ON addr.name = dl.parent
            WHERE dl.link_doctype = %(doctype)s
            AND dl.link_name = %(docname)s
            AND dl.parenttype = 'Address'
            ORDER BY addr.is_primary_address DESC, addr.is_shipping_address DESC
            LIMIT 1
        """

        result = frappe.db.sql(query, {"doctype": doctype, "docname": docname}, as_dict=True)

        if result:
            return result[0]
        else:
            return {
                'personal_addr_line1': '',
                'personal_addr_line2': '',
                'personal_pincode': '',
                'personal_city': '',
                'personal_phone': '',
                'personal_fax': '',
                'business_addr_line1': '',
                'business_pincode': '',
                'business_city': '',
                'business_phone': '',
                'business_fax': '',
                'business_email': ''
            }

    def transform_data(self, data):
        """Transform raw data with phone formatting and link generation"""
        transformed = []
        row_id = 1

        for row in data:
            # Add row ID
            row['ID'] = row_id
            row_id += 1

            # Determine salutation
            if row['source_type'] == 'Employee':
                if row['salutation'] == 'Ms' or row['gender'] == 'Female':
                    row['Anrede'] = 'Frau'
                elif row['salutation'] == 'Mr' or row['gender'] == 'Male':
                    row['Anrede'] = 'Herr'
                else:
                    row['Anrede'] = row.get('salutation', '')
            elif row.get('customer_type') == 'Company' or row.get('supplier_type') == 'Company':
                row['Anrede'] = 'Firma'
            elif row['salutation'] == 'Ms' or row['gender'] == 'Female':
                row['Anrede'] = 'Frau'
            elif row['salutation'] == 'Mr' or row['gender'] == 'Male':
                row['Anrede'] = 'Herr'
            else:
                row['Anrede'] = row.get('salutation', '')

            # Map fields
            row['Titel'] = ''
            row['Nachname'] = row.get('last_name', '')
            row['Vorname'] = row.get('first_name', '')
            row['Strasse'] = row.get('personal_addr_line1', '')
            row['PLZ'] = row.get('personal_pincode', '')
            row['Ort'] = row.get('personal_city', '')
            row['Tel1'] = format_phone_international(row.get('phone') or row.get('personal_phone', ''))
            row['Tel2'] = format_phone_international(row.get('mobile_no', ''))
            row['Fax'] = format_phone_international(row.get('personal_fax', ''))
            row['eMail'] = row.get('email_id', '')
            row['unben1'] = ''
            row['unben2'] = ''

            # Entity type
            if row.get('link_doctype') == 'Customer':
                row['unben3'] = 'Kunde'
            elif row.get('link_doctype') == 'Supplier':
                row['unben3'] = 'Lieferant'
            elif row.get('link_doctype') == 'Lead':
                row['unben3'] = 'Lead'
            elif row['source_type'] == 'Employee':
                row['unben3'] = 'Mitarbeiter'
            else:
                row['unben3'] = ''

            row['d_Position'] = row.get('designation', '')
            row['d_Firma'] = row.get('entity_name') or row.get('company_name', '')

            # Business address fallback
            if not row.get('personal_addr_line1'):
                row['d_Strasse'] = row.get('business_addr_line1') or row.get('personal_addr_line2', '')
                row['d_PLZ'] = row.get('business_pincode', '')
                row['d_Ort'] = row.get('business_city', '')
            else:
                row['d_Strasse'] = row.get('personal_addr_line2', '')
                row['d_PLZ'] = ''
                row['d_Ort'] = ''

            row['d_Haus'] = ''
            row['d_Raum'] = ''
            row['d_Tel1'] = format_phone_international(row.get('business_phone', ''))
            row['d_Tel2'] = ''
            row['d_Fax'] = format_phone_international(row.get('business_fax', ''))
            row['d_eMail'] = row.get('business_email', '')
            row['d_Handy'] = ''
            row['d_unben'] = ''
            row['callNotesDatei'] = ''
            row['Geburtsdatum'] = frappe.utils.formatdate(row.get('date_of_birth'), 'yyyy-MM-dd') if row.get('date_of_birth') else ''
            row['letzte_Aend'] = frappe.utils.formatdate(row.get('modified'), 'yyyy-MM-dd')

            # Tracking columns
            row['doctype'] = row['link_doctype'] if row.get('link_doctype') else row['source_type']
            row['document_name'] = row['link_name'] if row.get('link_name') else row['source_id']
            row['link_to_desk_document'] = generate_desk_link(row['doctype'], row['document_name'])
            row['link_to_dashboard'] = generate_dashboard_link(row['doctype'], row['document_name'])

            transformed.append(row)

        return transformed

    def generate_content(self, data):
        """Generate CSV content"""
        output = StringIO()

        fieldnames = [
            'ID', 'Anrede', 'Titel', 'Nachname', 'Vorname',
            'Strasse', 'PLZ', 'Ort', 'Tel1', 'Tel2', 'Fax', 'eMail',
            'unben1', 'unben2', 'unben3',
            'd_Position', 'd_Firma', 'd_Strasse', 'd_PLZ', 'd_Ort',
            'd_Haus', 'd_Raum', 'd_Tel1', 'd_Tel2', 'd_Fax', 'd_eMail', 'd_Handy',
            'd_unben', 'callNotesDatei', 'Geburtsdatum', 'letzte_Aend',
            'doctype', 'document_name', 'link_to_desk_document', 'link_to_dashboard'
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=';',
            quoting=csv.QUOTE_MINIMAL,
            extrasaction='ignore'
        )

        writer.writeheader()

        for row in data:
            writer.writerow(row)

        return output.getvalue()
