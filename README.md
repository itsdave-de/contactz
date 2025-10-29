# Contactz

ERPNext app for exporting contacts to various formats for CTI (Computer Telephony Integration) software.

## Features

- **Automated CSV Export**: Generates contact exports every 15 minutes
- **Static URL**: Always accessible at `/files/Telefonbuch.csv`
- **PhoneSuite Compatible**: Uses default import format for [PhoneSuite CTI](https://www.phonesuite.de/)
- **Multi-Source Support**: Exports from Customers, Suppliers, Leads, and Employees (requires HRMS)
- **International Phone Format**: Converts phone numbers to international format (e.g., 0049 XX XXXXXXX)
- **Dashboard Integration**: Includes direct links to ERPNext desk and custom dashboard
- **Selective Export**: Configure which data sources to include
- **German Translation**: Full German language support
- **Settings UI**: User-friendly settings page with real-time statistics

## Installation

1. Get the app:
```bash
bench get-app https://github.com/your-username/contactz.git
```

2. Install on site:
```bash
bench --site your-site.com install-app contactz
```

3. Configure settings:
```
Navigate to: Contactz Settings
```

## Configuration

Access **Contactz Settings** to:
- Enable/disable automatic CSV generation
- Select which data sources to include (Customer, Supplier, Lead, Employee*)
- View export statistics
- Download the latest export file
- Run manual exports

**\*Employee export requires HRMS app to be installed**

## Export Format

The CSV export includes 35 columns with:
- Contact information (name, salutation, gender)
- Personal address
- Business address
- Phone numbers (formatted internationally)
- Email addresses
- Entity links (Customer/Supplier/Lead/Employee)
- Direct links to ERPNext (desk and dashboard)

**Format Details:**
- Delimiter: Semicolon (;)
- Encoding: UTF-8
- Compatible with: PhoneSuite CTI and similar systems

## Security Notice

⚠️ **Important**: The export file is publicly accessible without authentication at `/files/Telefonbuch.csv`.

**Do not expose your ERPNext server directly to the internet** if the file contains sensitive contact information.

**Recommended protection:**
- Use firewall rules to restrict access
- Implement VPN for remote access
- Configure IP allowlists
- Use reverse proxy with authentication

## Usage

### Automatic Export
Once enabled in settings, exports run automatically every 15 minutes.

### Manual Export
Click "Run Export Now" in Contactz Settings for immediate export.

### Access the File
Static URL (never changes):
```
https://your-site.com/files/Telefonbuch.csv
```

### Configure CTI Software
Use the static URL in your CTI software (e.g., PhoneSuite) to import contacts.

## Architecture

- **Modular Design**: Base exporter class for easy format extensions
- **Utilities**: Phone formatter, link generator
- **Settings**: Single DocType for configuration
- **Scheduler**: Cron-based automatic exports
- **Translations**: Full i18n support (English, German)

## Development

### Add New Export Format

1. Create new exporter in `contactz/exporters/`:
```python
from contactz.exporters.base import BaseContactExporter

class MyExporter(BaseContactExporter):
    def get_file_name(self):
        return "my_export.xml"

    def fetch_data(self):
        # Fetch data logic

    def transform_data(self, data):
        # Transform logic

    def generate_content(self, data):
        # Generate XML/JSON/etc
```

2. Add scheduler task in `contactz/tasks.py`
3. Register in `hooks.py`

### File Structure
```
contactz/
├── contactz/
│   ├── contactz/doctype/contactz_settings/  # Settings DocType
│   ├── exporters/                            # Export format implementations
│   │   ├── base.py                           # Base exporter class
│   │   └── telefonbuch_csv.py                # CSV exporter
│   ├── templates/pages/                      # Dashboard views
│   ├── translations/                         # i18n translations
│   │   └── de.csv                            # German translations
│   ├── utils/                                # Utility functions
│   │   ├── phone_formatter.py                # Phone number formatting
│   │   └── link_generator.py                 # URL generation
│   ├── api.py                                # API endpoints
│   ├── hooks.py                              # App hooks and scheduler
│   └── tasks.py                              # Scheduled tasks
├── license.txt                               # GPL v3 license
└── README.md                                 # This file
```

## Requirements

- Frappe >= 15.0.0
- ERPNext >= 15.0.0
- HRMS >= 15.0.0 (optional, only required if exporting employees)

**Tested with ERPNext 15**

**Note:** The Employee export feature requires the HRMS app. If HRMS is not installed, simply disable "Include Active Employees" in Contactz Settings to export only Customer, Supplier, and Lead contacts.

## License

GPL v3

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-username/contactz/issues
- Documentation: See `QUICKSTART.md` and `CONTACTZ_SETTINGS_GUIDE.md`

## Credits

Developed for ERPNext to provide seamless CTI integration.
