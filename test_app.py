
import os
import sqlite3
import tempfile
import unittest
from io import BytesIO

import app as trustvault


class TrustVaultTests(unittest.TestCase):

    def setUp(self):
        # Temporary test folder and database
        self.temp_dir = tempfile.TemporaryDirectory()

        self.test_db = os.path.join(
            self.temp_dir.name, "test_trustvault.db"
        )

        self.test_uploads = os.path.join(
            self.temp_dir.name, "uploads"
        )

        os.makedirs(self.test_uploads, exist_ok=True)

        # Save original settings
        self.original_db_function = trustvault.get_db_connection
        self.original_upload_folder = trustvault.app.config["UPLOAD_FOLDER"]
        self.original_testing = trustvault.app.config["TESTING"]

        # Disable CSRF only during automated tests
        trustvault.app.config["WTF_CSRF_ENABLED"] = False

        # Use temporary database during testing
        def test_db_connection():
            connection = sqlite3.connect(self.test_db)
            connection.row_factory = sqlite3.Row
            return connection

        trustvault.get_db_connection = test_db_connection
        trustvault.app.config["UPLOAD_FOLDER"] = self.test_uploads
        trustvault.app.config["TESTING"] = True
        trustvault.app.config["SECRET_KEY"] = "test-secret-key"

        # Create test users
        self.test_users = {
            "test_admin": {
                "password_hash": trustvault.generate_password_hash(
                    "AdminTest123"
                ),
                "role": "admin"
            },
            "test_owner": {
                "password_hash": trustvault.generate_password_hash(
                    "OwnerTest123"
                ),
                "role": "owner"
            },
            "test_viewer": {
                "password_hash": trustvault.generate_password_hash(
                    "ViewerTest123"
                ),
                "role": "viewer"
            }
        }

        trustvault.users.update(self.test_users)

        # Initialize temporary database
        trustvault.init_db()

        # Create test documents
        connection = trustvault.get_db_connection()

        connection.execute(
            """
            INSERT INTO documents
            (id, filename, owner, category, upload_date)
            VALUES (1, 'admin_test.pdf', 'test_admin',
                    'General', '2026-11-07')
            """
        )

        connection.execute(
            """
            INSERT INTO documents
            (id, filename, owner, category, upload_date)
            VALUES (2, 'owner_test.pdf', 'test_owner',
                    'Education', '2026-11-07')
            """
        )

        # Viewer receives read permission
        connection.execute(
            """
            INSERT INTO permissions
            (document_id, username, permission)
            VALUES (2, 'test_viewer', 'read')
            """
        )

        connection.commit()
        connection.close()

        # Create sample files
        with open(
            os.path.join(self.test_uploads, "admin_test.pdf"), "wb"
        ) as file:
            file.write(b"Admin test document")

        with open(
            os.path.join(self.test_uploads, "owner_test.pdf"), "wb"
        ) as file:
            file.write(b"Owner test document")

        self.client = trustvault.app.test_client()

    def tearDown(self):
        # Restore original application settings
        trustvault.get_db_connection = self.original_db_function
        trustvault.app.config["UPLOAD_FOLDER"] = self.original_upload_folder
        trustvault.app.config["TESTING"] = self.original_testing

        for username in self.test_users:
            trustvault.users.pop(username, None)

        self.temp_dir.cleanup()

    def login(self, username, password):
        return self.client.post(
            "/login",
            data={
                "username": username,
                "password": password
            },
            follow_redirects=True
        )

    def test_valid_login(self):
        response = self.login("test_admin", "AdminTest123")
        self.assertEqual(response.status_code, 200)

    def test_invalid_login(self):
        response = self.client.post(
            "/login",
            data={
                "username": "test_admin",
                "password": "wrongpassword"
            }
        )

        self.assertIn(
            b"Invalid username or password",
            response.data
        )

    def test_owner_sees_only_own_documents(self):
        self.login("test_owner", "OwnerTest123")

        response = self.client.get("/dashboard")

        self.assertIn(b"owner_test.pdf", response.data)
        self.assertNotIn(b"admin_test.pdf", response.data)

    def test_viewer_can_download_read_document(self):
        self.login("test_viewer", "ViewerTest123")

        response = self.client.get(
            "/download/owner_test.pdf"
        )

        try:
            self.assertEqual(response.status_code, 200)
        finally:
            # Close downloaded file response
            response.close()

    def test_viewer_cannot_download_unshared_document(self):
        self.login("test_viewer", "ViewerTest123")

        response = self.client.get(
            "/download/admin_test.pdf"
        )

        self.assertEqual(response.status_code, 403)

    def test_read_permission_cannot_edit(self):
        self.login("test_viewer", "ViewerTest123")

        response = self.client.get("/edit/2")

        self.assertEqual(response.status_code, 403)

    def test_edit_permission_allows_edit_page(self):
        connection = trustvault.get_db_connection()

        connection.execute(
            """
            UPDATE permissions
            SET permission = 'edit'
            WHERE document_id = 2
            AND username = 'test_viewer'
            """
        )

        connection.commit()
        connection.close()

        self.login("test_viewer", "ViewerTest123")

        response = self.client.get("/edit/2")

        self.assertEqual(response.status_code, 200)

    def test_revoked_permission_blocks_download(self):
        connection = trustvault.get_db_connection()

        connection.execute(
            """
            DELETE FROM permissions
            WHERE document_id = 2
            AND username = 'test_viewer'
            """
        )

        connection.commit()
        connection.close()

        self.login("test_viewer", "ViewerTest123")

        response = self.client.get(
            "/download/owner_test.pdf"
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_upload_document(self):
        self.login("test_owner", "OwnerTest123")

        response = self.client.post(
            "/upload",
            data={
                "category": "Education",
                "document": (
                    BytesIO(b"New test PDF content"),
                    "new_test.pdf"
                )
            },
            content_type="multipart/form-data"
        )

        self.assertEqual(response.status_code, 302)

        connection = trustvault.get_db_connection()

        document = connection.execute(
            """
            SELECT filename, owner, category
            FROM documents
            WHERE filename = 'new_test.pdf'
            """
        ).fetchone()

        connection.close()

        self.assertIsNotNone(document)
        self.assertEqual(document["owner"], "test_owner")
        self.assertEqual(document["category"], "Education")

    def test_only_admin_can_view_activity_logs(self):
        self.login("test_viewer", "ViewerTest123")

        response = self.client.get("/activity-logs")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_activity_logs(self):
        self.login("test_admin", "AdminTest123")

        response = self.client.get("/activity-logs")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
