// Copyright (c) 2025, itsdave GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Contactz Settings', {
	refresh: function(frm) {
		// Load statistics on form load
		frm.trigger('load_statistics');

		// Set up button click handlers (use .off() to prevent duplicate handlers)
		frm.fields_dict.refresh_statistics.$input.off('click').on('click', function() {
			frm.trigger('load_statistics');
		});

		frm.fields_dict.run_export_now.$input.off('click').on('click', function() {
			frm.trigger('run_export_now');
		});
	},

	load_statistics: function(frm) {
		// Show loading message
		frm.set_df_property('export_statistics', 'options', '<p>Loading statistics...</p>');

		// Call server method to get statistics
		frappe.call({
			method: 'contactz.contactz.doctype.contactz_settings.contactz_settings.get_statistics_html',
			callback: function(r) {
				if (r.message) {
					frm.set_df_property('export_statistics', 'options', r.message);
					frm.refresh_field('export_statistics');
				}
			}
		});
	},

	enable_csv_generation: function(frm) {
		// Show message when toggling
		if (frm.doc.enable_csv_generation) {
			frappe.show_alert({
				message: __('CSV generation enabled. Export will run every 15 minutes.'),
				indicator: 'green'
			}, 5);
		} else {
			frappe.show_alert({
				message: __('CSV generation disabled. Scheduled exports will be skipped.'),
				indicator: 'orange'
			}, 5);
		}
	},

	run_export_now: function(frm) {
		// Disable the button and show progress
		frm.fields_dict.run_export_now.$input.prop('disabled', true);

		frappe.show_alert({
			message: __('Running export... Please wait.'),
			indicator: 'blue'
		}, 5);

		// Call server method to trigger export
		frappe.call({
			method: 'contactz.contactz.doctype.contactz_settings.contactz_settings.trigger_export_now',
			callback: function(r) {
				// Re-enable the button
				frm.fields_dict.run_export_now.$input.prop('disabled', false);

				if (r.message) {
					let indicator = 'green';
					if (r.message.status === 'warning') {
						indicator = 'orange';
					} else if (r.message.status === 'error') {
						indicator = 'red';
					}

					frappe.show_alert({
						message: __(r.message.message),
						indicator: indicator
					}, 10);

					// Reload statistics immediately if successful
					if (r.message.status === 'success') {
						frm.trigger('load_statistics');
					}
				}
			},
			error: function(r) {
				// Re-enable the button
				frm.fields_dict.run_export_now.$input.prop('disabled', false);

				frappe.show_alert({
					message: __('Failed to trigger export. Please check the error log.'),
					indicator: 'red'
				}, 10);
			}
		});
	}
});
