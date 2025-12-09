"""
Contactz Scheduled Tasks
Entry points for scheduler jobs
"""

import frappe
import time
from contactz.exporters.telefonbuch_csv import TelefonbuchCSVExporter


def export_telefonbuch_csv():
    """
    Export contacts to Telefonbuch CSV format

    This function is called by the scheduler every 15 minutes
    Configured in hooks.py: scheduler_events

    Checks Contactz Settings to see if export is enabled

    Returns:
        File URL if successful, None if failed or disabled
    """
    try:
        # Check if CSV generation is enabled in settings
        from contactz.contactz.doctype.contactz_settings.contactz_settings import is_csv_generation_enabled

        if not is_csv_generation_enabled():
            frappe.logger().info("Telefonbuch CSV export skipped - disabled in Contactz Settings")
            return None

        # Run the export and track duration
        start_time = time.time()
        exporter = TelefonbuchCSVExporter()
        file_url = exporter.export()
        duration_seconds = time.time() - start_time

        # Store duration in cache for statistics display
        frappe.cache().set_value('contactz_last_export_duration', duration_seconds)

        if file_url:
            frappe.logger().info(f"Telefonbuch CSV export successful: {file_url} (took {duration_seconds:.2f}s)")
        else:
            frappe.logger().warning("Telefonbuch CSV export returned no URL")

        return file_url

    except Exception as e:
        # Error is already logged by the exporter
        frappe.logger().error(f"Telefonbuch CSV export task failed: {str(e)}")
        return None


# Additional export tasks can be added here in the future
# For example:
#
# def export_contacts_json():
#     """Export contacts to JSON format"""
#     from contactz.exporters.json_export import JSONContactExporter
#     exporter = JSONContactExporter()
#     return exporter.export()
#
# def export_contacts_vcard():
#     """Export contacts to vCard format"""
#     from contactz.exporters.vcard_export import VCardExporter
#     exporter = VCardExporter()
#     return exporter.export()
