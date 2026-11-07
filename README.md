# TrustVault – Secure Document Management System

## 1. Project Overview
TrustVault is a web-based Secure Document Management System developed using Python Flask and SQLite. It helps users securely upload, search, download, edit and manage documents with role-based access permissions.

## 2. Technologies Used
- Python
- Flask
- SQLite
- HTML
- CSS
- Flask-Login
- Flask-WTF
- Werkzeug

## 3. Main Features
- User Login and Logout
- Admin, Owner and Viewer roles
- Secure Document Upload
- Document Download
- Document Editing
- Category-based Document Organization
- Search by Filename and Owner
- Search by Category and Upload Date
- Read and Edit Permissions
- Grant and Revoke Permissions
- Activity Logs
- CSRF Protection
- File Upload Validation

## 4. Project Structure

```text
trustvault/
│
├── app.py
├── test_app.py
├── .env
├── .gitignore
├── README.md
├── THREATS.md
├── PROMPTS.md
├── trustvault.db
│
├── private_uploads/
│
└── templates/
    ├── login.html
    ├── dashboard.html
    ├── upload.html
    ├── edit_document.html
    ├── search.html
    ├── activity_logs.html
    ├── grant_permission.html
    └── revoke_permission.html
```

## 5. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd trustvault
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
```

### Step 3: Activate Virtual Environment

Windows:

```bash
.venv\Scripts\activate
```

### Step 4: Install Required Packages

```bash
pip install flask flask-login flask-wtf python-dotenv
```

### Step 5: Configure Environment Variables

Create a `.env` file and configure:

```env
SECRET_KEY=your-secure-random-secret-key

ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password

OWNER_USERNAME=owner
OWNER_PASSWORD=your-owner-password

VIEWER_USERNAME=viewer
VIEWER_PASSWORD=your-viewer-password
```

Use strong passwords and never upload `.env` to GitHub.

### Step 6: Run the Application

```bash
python app.py
```

Open the browser:

```text
http://localhost:5000
```

## 6. Run Automated Tests

```bash
python -m unittest test_app.py
```

The project includes 11 automated test cases covering authentication, document access, permissions, uploads and activity logs.

## 7. User Roles

| Role | Access |
|---|---|
| Admin | Manage and view all documents and activity logs |
| Owner | Upload, edit and manage own documents and permissions |
| Viewer | Access documents shared with them |

## 8. Security Features
- Password hashing
- Role-based access control
- Secure filename validation
- File type and size validation
- CSRF protection
- Server-side permission checks
- Access revocation
- Activity logging

## 9. Future Enhancements
- Document encryption
- Multi-factor authentication
- Cloud storage integration
- Email notifications
- Tamper-resistant audit logs
- Advanced user management

## 10. Conclusion
TrustVault provides a secure and organized way to manage documents. It uses authentication, role-based authorization and document-level permissions to prevent unauthorized access.

## 11. Project Status
Core application features have been implemented and tested locally. Deployment and additional production security improvements are future tasks.