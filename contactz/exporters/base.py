"""
Base Contact Exporter
Abstract base class for all contact export formats
"""

import frappe
from abc import ABC, abstractmethod
from datetime import datetime


class BaseContactExporter(ABC):
    """
    Abstract base class for contact exporters

    Subclasses must implement:
    - fetch_data(): Fetch contact data
    - transform_data(data): Transform data to export format
    - generate_content(data): Generate export content (CSV, JSON, XML, etc.)
    - get_file_name(): Return the output filename
    """

    def __init__(self):
        """Initialize exporter"""
        self.site_url = frappe.utils.get_url()
        self.export_timestamp = datetime.now()

    @abstractmethod
    def fetch_data(self):
        """
        Fetch contact data from database

        Returns:
            List of dictionaries containing contact data
        """
        raise NotImplementedError("Subclasses must implement fetch_data()")

    @abstractmethod
    def transform_data(self, data):
        """
        Transform raw data to export format

        Args:
            data: Raw data from fetch_data()

        Returns:
            Transformed data ready for export
        """
        raise NotImplementedError("Subclasses must implement transform_data()")

    @abstractmethod
    def generate_content(self, data):
        """
        Generate export file content

        Args:
            data: Transformed data

        Returns:
            String content ready to write to file
        """
        raise NotImplementedError("Subclasses must implement generate_content()")

    @abstractmethod
    def get_file_name(self):
        """
        Get the output filename

        Returns:
            Filename string (e.g., 'Telefonbuch.csv')
        """
        raise NotImplementedError("Subclasses must implement get_file_name()")

    def get_encoding(self):
        """
        Get the file encoding for export

        Override in subclass to change encoding.
        Default is UTF-8.

        Returns:
            Encoding string (e.g., 'utf-8', 'cp1252', 'iso-8859-1')
        """
        return 'utf-8'

    def export(self):
        """
        Main export method - orchestrates the export process

        Returns:
            File URL if successful, None if failed
        """
        try:
            # Step 1: Fetch data
            frappe.logger().info(f"{self.__class__.__name__}: Fetching data...")
            raw_data = self.fetch_data()

            if not raw_data:
                frappe.logger().warning(f"{self.__class__.__name__}: No data to export")
                return None

            frappe.logger().info(f"{self.__class__.__name__}: Fetched {len(raw_data)} records")

            # Step 2: Transform data
            frappe.logger().info(f"{self.__class__.__name__}: Transforming data...")
            transformed_data = self.transform_data(raw_data)

            # Step 3: Generate content
            frappe.logger().info(f"{self.__class__.__name__}: Generating export content...")
            content = self.generate_content(transformed_data)

            # Step 4: Save to file
            frappe.logger().info(f"{self.__class__.__name__}: Saving to file...")
            file_url = self.save_to_file(content)

            frappe.logger().info(f"{self.__class__.__name__}: Export successful - {file_url}")
            return file_url

        except Exception as e:
            self.handle_error(e)
            return None

    def save_to_file(self, content):
        """
        Save content to File document in ERPNext
        Always uses the same static filename and URL

        Args:
            content: Content to save (string or bytes)

        Returns:
            File URL (static, always the same)
        """
        import os
        file_name = self.get_file_name()

        # Convert string to bytes if needed
        if isinstance(content, str):
            encoding = self.get_encoding()
            content_bytes = content.encode(encoding, errors='replace')
        else:
            content_bytes = content

        # Get site path
        site_path = frappe.get_site_path()
        public_files_path = os.path.join(site_path, "public", "files")
        file_path = os.path.join(public_files_path, file_name)

        # Write directly to file system
        with open(file_path, 'wb') as f:
            f.write(content_bytes)

        frappe.logger().info(f"Wrote file to: {file_path}")

        # Clean up old File doctypes with similar names (e.g., Telefonbuch*.csv)
        base_name = file_name.rsplit('.', 1)[0]  # e.g., "Telefonbuch"
        extension = file_name.rsplit('.', 1)[1] if '.' in file_name else ''  # e.g., "csv"

        # Find all File documents matching pattern
        if extension:
            pattern = f"{base_name}%.{extension}"
        else:
            pattern = f"{base_name}%"

        old_files = frappe.get_all("File", filters={
            "file_name": ["like", pattern],
            "is_private": 0
        })

        # Delete all old File records
        for old_file in old_files:
            try:
                frappe.delete_doc("File", old_file.name, ignore_permissions=True, force=True)
                frappe.logger().info(f"Deleted old File record: {old_file.name}")
            except:
                pass

        # Delete orphaned files from filesystem (files with random suffixes)
        try:
            for filename in os.listdir(public_files_path):
                if filename.startswith(base_name) and filename != file_name and filename.endswith(f".{extension}"):
                    orphan_path = os.path.join(public_files_path, filename)
                    os.remove(orphan_path)
                    frappe.logger().info(f"Deleted orphaned file: {filename}")
        except Exception as e:
            frappe.logger().warning(f"Could not clean orphaned files: {str(e)}")

        # Create new File document with static name
        file_url = f"/files/{file_name}"

        # Get file size
        file_size = os.path.getsize(file_path)

        # Insert directly into database to avoid File controller creating a new file
        file_doc_name = frappe.generate_hash(length=10)
        frappe.db.sql("""
            INSERT INTO `tabFile`
            (name, creation, modified, modified_by, owner, docstatus, file_name, file_url, file_size, is_private, folder)
            VALUES (%s, NOW(), NOW(), %s, %s, 0, %s, %s, %s, 0, 'Home')
        """, (file_doc_name, frappe.session.user, frappe.session.user, file_name, file_url, file_size))

        frappe.logger().info(f"Created File record: {file_name} at {file_url}")

        frappe.db.commit()
        return file_url

    def handle_error(self, error):
        """
        Handle export errors - log to Error Log and keep old file

        Args:
            error: Exception object
        """
        error_title = f"{self.__class__.__name__} Export Failed"

        error_message = f"""
Export Type: {self.__class__.__name__}
Timestamp: {self.export_timestamp}
File Name: {self.get_file_name()}

Error Message:
{str(error)}

Traceback:
{frappe.get_traceback()}
"""

        # Log to Error Log doctype
        frappe.log_error(
            title=error_title,
            message=error_message
        )

        frappe.logger().error(f"{error_title}: {str(error)}")

        # Note: We do NOT overwrite the existing file on error
        # The old file remains accessible

    def get_row_count(self):
        """
        Get count of records that will be exported
        Useful for logging and monitoring

        Returns:
            Integer count
        """
        try:
            data = self.fetch_data()
            return len(data) if data else 0
        except:
            return 0
