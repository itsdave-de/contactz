"""
Contactz Settings
Single DocType for managing Contactz export settings and viewing statistics
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, cint, flt, format_datetime


class ContactzSettings(Document):
	"""Contactz Settings Controller"""

	def validate(self):
		"""Validation hook - generate statistics on load"""
		self.export_statistics = get_statistics_html()

	def on_update(self):
		"""After save - clear cache if settings changed"""
		frappe.cache().delete_value('contactz_settings_enabled')
		frappe.cache().delete_value('contactz_enabled_sources')


@frappe.whitelist()
def get_statistics_html():
	"""
	Generate HTML with export statistics and file link

	Returns:
		HTML string with statistics
	"""
	try:
		# Static file URL (always the same)
		static_file_url = "/files/Telefonbuch.csv"
		full_file_url = f"{frappe.utils.get_url()}{static_file_url}"

		# Get file information
		file_info = frappe.db.get_value(
			"File",
			{"file_name": "Telefonbuch.csv", "is_private": 0},
			["name", "file_url", "file_size", "modified", "creation"],
			as_dict=True
		)

		if not file_info:
			return f"""
			<div class="alert alert-warning">
				<strong>{_("No Export File Found")}</strong>
				<p>{_("The Telefonbuch.csv file has not been generated yet.")}</p>
				<p>{_('Click the "Run Export Now" button above or wait for the next scheduled run (every 15 minutes).')}</p>
				<br>
				<p><strong>{_("Static Download URL (will work after first export)")}:</strong></p>
				<code style="background: #f8f9fa; padding: 8px 12px; border-radius: 4px; display: inline-block;">
					{full_file_url}
				</code>
			</div>
			"""

		# Get export statistics
		stats = get_export_statistics()

		# Calculate file age
		file_age_minutes = frappe.utils.time_diff_in_seconds(now(), file_info.modified) / 60

		# Format file size
		file_size_kb = flt(file_info.file_size) / 1024
		file_size_mb = file_size_kb / 1024

		if file_size_mb > 1:
			file_size_str = f"{file_size_mb:.2f} MB"
		else:
			file_size_str = f"{file_size_kb:.2f} KB"

		# Status text with translations
		status_text = _("Current") if file_age_minutes < 20 else _("Outdated")
		status_class = 'status-success' if file_age_minutes < 20 else 'status-warning'
		minutes_ago_text = _("{0} minutes ago").format(int(file_age_minutes))

		# Generate HTML
		html = f"""
		<div class="contactz-statistics">
			<style>
				.contactz-statistics {{
					font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
				}}
				.stats-card {{
					background: #f8f9fa;
					border: 1px solid #dee2e6;
					border-radius: 8px;
					padding: 20px;
					margin-bottom: 20px;
				}}
				.stats-header {{
					font-size: 18px;
					font-weight: 600;
					color: #212529;
					margin-bottom: 15px;
					padding-bottom: 10px;
					border-bottom: 2px solid #0d6efd;
				}}
				.stats-grid {{
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
					gap: 15px;
					margin-top: 15px;
				}}
				.stat-item {{
					background: white;
					padding: 15px;
					border-radius: 6px;
					border: 1px solid #e9ecef;
				}}
				.stat-label {{
					font-size: 12px;
					color: #6c757d;
					text-transform: uppercase;
					letter-spacing: 0.5px;
					margin-bottom: 5px;
				}}
				.stat-value {{
					font-size: 24px;
					font-weight: 700;
					color: #212529;
				}}
				.file-link {{
					display: inline-block;
					padding: 12px 24px;
					background: #0d6efd;
					color: white !important;
					text-decoration: none !important;
					border-radius: 6px;
					font-weight: 500;
					transition: background 0.2s;
					margin-top: 10px;
				}}
				.file-link:hover {{
					background: #0b5ed7;
					color: white !important;
				}}
				.status-badge {{
					display: inline-block;
					padding: 4px 12px;
					border-radius: 12px;
					font-size: 12px;
					font-weight: 600;
				}}
				.status-success {{
					background: #d1e7dd;
					color: #0f5132;
				}}
				.status-warning {{
					background: #fff3cd;
					color: #664d03;
				}}
				.info-text {{
					color: #6c757d;
					font-size: 14px;
					margin-top: 10px;
				}}
			</style>

			<div class="stats-card">
				<div class="stats-header">📊 {_("Export File Information")}</div>

				<div style="margin-bottom: 20px;">
					<div style="background: #e7f5ff; border-left: 4px solid #0d6efd; padding: 12px; margin-bottom: 15px; border-radius: 4px;">
						<strong style="color: #0d6efd;">✓ {_("Static Download URL (Never Changes)")}:</strong><br>
						<code style="background: white; padding: 8px 12px; border-radius: 4px; display: inline-block; margin-top: 8px; font-size: 13px; border: 1px solid #dee2e6;">
							{full_file_url}
						</code>
					</div>
					<a href="{static_file_url}" class="file-link" target="_blank">
						📥 {_("Download Telefonbuch.csv")}
					</a>
				</div>

				<div class="stats-grid">
					<div class="stat-item">
						<div class="stat-label">{_("File Size")}</div>
						<div class="stat-value">{file_size_str}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("Last Updated")}</div>
						<div class="stat-value" style="font-size: 16px;">
							{format_datetime(file_info.modified, "dd MMM yyyy HH:mm")}
						</div>
						<div class="info-text">
							{minutes_ago_text}
						</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("Status")}</div>
						<div class="stat-value">
							<span class="status-badge {status_class}">
								{'✓ ' if file_age_minutes < 20 else '⚠ '}{status_text}
							</span>
						</div>
					</div>
				</div>
			</div>

			<div class="stats-card">
				<div class="stats-header">📈 {_("Data Statistics")}</div>

				<div class="stats-grid">
					<div class="stat-item">
						<div class="stat-label">{_("Total Contacts")}</div>
						<div class="stat-value">{stats['total_contacts']}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("With Customer")}</div>
						<div class="stat-value">{stats['contacts_with_customer']}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("With Supplier")}</div>
						<div class="stat-value">{stats['contacts_with_supplier']}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("With Lead")}</div>
						<div class="stat-value">{stats['contacts_with_lead']}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("Active Employees")}</div>
						<div class="stat-value">{stats['active_employees']}</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">{_("Total Exported")}</div>
						<div class="stat-value">{stats['total_exported']}</div>
					</div>
				</div>
			</div>

			<div class="stats-card">
				<div class="stats-header">ℹ️ {_("Information")}</div>
				<ul style="margin: 0; padding-left: 20px;">
					<li><strong>{_("Static URL")}:</strong> {_("Always use")} <code>{full_file_url}</code> - {_("this URL never changes")}</li>
					<li>{_("CSV file is generated automatically every 15 minutes when enabled")}</li>
					<li>{_('Manual export available via "Run Export Now" button above')}</li>
					<li>{_("Format")}: 35 {_("columns")}, {_("semicolon-delimited")}, UTF-8 {_("encoding")}</li>
					<li>{_("Phone numbers in international format")} (0049 XX XXXXXXX)</li>
					<li>{_("Includes direct links to ERPNext desk and custom dashboard")}</li>
					<li><strong>{_("Format Compatibility")}:</strong> {_("Uses default import format for")} <a href="https://www.phonesuite.de/de/" target="_blank">PhoneSuite CTI</a></li>
				</ul>
				<div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin-top: 15px; border-radius: 4px;">
					<strong style="color: #856404;">⚠️ {_("Security Warning")}</strong><br>
					<span style="color: #856404; font-size: 13px;">
						{_("This file is publicly accessible without authentication. Do not expose this server directly to the internet if the file contains sensitive contact information. Use firewall rules, VPN, or IP restrictions to protect access.")}
					</span>
				</div>
			</div>
		</div>
		"""

		return html

	except Exception as e:
		frappe.log_error(
			title="Contactz Statistics Generation Failed",
			message=frappe.get_traceback()
		)
		return f"""
		<div class="alert alert-danger">
			<strong>{_("Error Loading Statistics")}</strong>
			<p>{str(e)}</p>
		</div>
		"""


def get_export_statistics():
	"""
	Get statistics about contacts and exports

	Returns:
		Dictionary with statistics
	"""
	stats = {}

	# Total contacts with contact info
	stats['total_contacts'] = frappe.db.sql("""
		SELECT COUNT(*) as count
		FROM tabContact c
		WHERE c.docstatus = 0
		AND (c.email_id IS NOT NULL OR c.phone IS NOT NULL OR c.mobile_no IS NOT NULL)
	""", as_dict=True)[0].count

	# Contacts with customer link
	stats['contacts_with_customer'] = frappe.db.sql("""
		SELECT COUNT(DISTINCT c.name) as count
		FROM tabContact c
		INNER JOIN `tabDynamic Link` dl ON dl.parent = c.name AND dl.parenttype = 'Contact' AND dl.link_doctype = 'Customer'
		WHERE c.docstatus = 0
	""", as_dict=True)[0].count

	# Contacts with supplier link
	stats['contacts_with_supplier'] = frappe.db.sql("""
		SELECT COUNT(DISTINCT c.name) as count
		FROM tabContact c
		INNER JOIN `tabDynamic Link` dl ON dl.parent = c.name AND dl.parenttype = 'Contact' AND dl.link_doctype = 'Supplier'
		WHERE c.docstatus = 0
	""", as_dict=True)[0].count

	# Contacts with lead link
	stats['contacts_with_lead'] = frappe.db.sql("""
		SELECT COUNT(DISTINCT c.name) as count
		FROM tabContact c
		INNER JOIN `tabDynamic Link` dl ON dl.parent = c.name AND dl.parenttype = 'Contact' AND dl.link_doctype = 'Lead'
		WHERE c.docstatus = 0
	""", as_dict=True)[0].count

	# Active employees (requires HRMS app)
	try:
		stats['active_employees'] = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM tabEmployee e
			WHERE e.status = 'Active'
			AND (e.company_email IS NOT NULL OR e.personal_email IS NOT NULL OR e.cell_number IS NOT NULL)
		""", as_dict=True)[0].count
	except Exception as e:
		# HRMS not installed or Employee table doesn't exist
		frappe.logger().warning(f"Could not fetch employee count: {str(e)}. HRMS app may not be installed.")
		stats['active_employees'] = 0

	# Total that will be exported (approximate)
	stats['total_exported'] = stats['contacts_with_customer'] + stats['contacts_with_supplier'] + stats['contacts_with_lead'] + stats['active_employees']

	return stats


def is_csv_generation_enabled():
	"""
	Check if CSV generation is enabled in settings

	Returns:
		Boolean
	"""
	# Try cache first
	enabled = frappe.cache().get_value('contactz_settings_enabled')

	if enabled is None:
		# Check database
		try:
			settings = frappe.get_single('Contactz Settings')
			enabled = cint(settings.enable_csv_generation)
		except:
			# Default to enabled if settings don't exist yet
			enabled = 1

		# Cache for 5 minutes
		frappe.cache().set_value('contactz_settings_enabled', enabled, expires_in_sec=300)

	return cint(enabled)


def get_enabled_sources():
	"""
	Get list of enabled data sources from settings

	Returns:
		Dictionary with boolean flags for each source
	"""
	# Try cache first
	cache_key = 'contactz_enabled_sources'
	sources = frappe.cache().get_value(cache_key)

	if sources is None:
		try:
			settings = frappe.get_single('Contactz Settings')
			sources = {
				'customer': cint(settings.include_contacts_with_customer),
				'supplier': cint(settings.include_contacts_with_supplier),
				'lead': cint(settings.include_contacts_with_lead),
				'employee': cint(settings.include_employees)
			}
		except:
			# Default: all enabled
			sources = {
				'customer': 1,
				'supplier': 1,
				'lead': 1,
				'employee': 1
			}

		# Cache for 5 minutes
		frappe.cache().set_value(cache_key, sources, expires_in_sec=300)

	return sources


@frappe.whitelist()
def trigger_export_now():
	"""
	Trigger the Telefonbuch CSV export immediately

	Runs the export synchronously and returns results immediately

	Returns:
		Dictionary with status and message
	"""
	try:
		# Check if export is enabled
		if not is_csv_generation_enabled():
			return {
				'status': 'warning',
				'message': _('CSV generation is currently disabled in settings. Please enable it first.')
			}

		# Run the export directly
		from contactz.tasks import export_telefonbuch_csv
		file_url = export_telefonbuch_csv()

		if file_url:
			return {
				'status': 'success',
				'message': _('Export completed successfully! File available at {0}').format(file_url)
			}
		else:
			return {
				'status': 'error',
				'message': _('Export completed but no file URL was returned. Check the Error Log for details.')
			}

	except Exception as e:
		frappe.log_error(
			title="Manual Export Trigger Failed",
			message=frappe.get_traceback()
		)
		return {
			'status': 'error',
			'message': _('Failed to trigger export: {0}').format(str(e))
		}
