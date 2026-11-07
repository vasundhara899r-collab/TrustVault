# TrustVault – Threat Model

## 1. Project Overview
TrustVault is a secure document management system developed using Python Flask and SQLite. It allows users to upload, search, download, edit and manage documents based on user roles and permissions.

## 2. Assets to Protect
- Uploaded documents and files.
- User login credentials.
- Document ownership information.
- Read and edit permissions.
- Activity logs.
- User sessions and application data.

## 3. Possible Threats

### 3.1 Unauthorized Access
An unauthorized user may try to access private documents.

**Mitigation:** Login authentication and role-based access control are implemented.

### 3.2 Weak Password Security
Attackers may try to obtain user passwords.

**Mitigation:** Passwords are stored using password hashing instead of plain text.

### 3.3 Malicious File Upload
Users may upload unwanted or potentially harmful files.

**Mitigation:** File extensions are validated, filenames are secured, and upload size is limited.

### 3.4 Unauthorized Document Download
A viewer may try to download documents that are not shared with them.

**Mitigation:** The application checks document ownership and permissions before allowing downloads.

### 3.5 Unauthorized Editing
A read-only user may try to modify a document.

**Mitigation:** Only authorized owners, admins, and users with edit permission can edit documents.

### 3.6 Session Attacks
An attacker may try to misuse an authenticated session.

**Mitigation:** Secure session cookie settings and CSRF protection are configured.

### 3.7 Permission Misuse
A user may continue accessing a document after permission is revoked.

**Mitigation:** Permissions are checked on every protected request. Revoked users cannot access the document through old download links.

### 3.8 Activity Log Manipulation
An attacker with database access may try to modify activity records.

**Mitigation:** Important actions are recorded in the activity log. However, SQLite logs are not tamper-proof and require additional protection in production.

## 4. Security Measures Implemented
- User authentication.
- Password hashing.
- Role-based access control.
- Document-level read and edit permissions.
- File upload validation.
- Secure filename handling.
- CSRF protection.
- Unauthorized access prevention.
- Activity logging.
- Permission revocation.

## 5. Future Security Improvements
- Encrypt documents stored on the server.
- Use a tamper-resistant audit logging system.
- Add multi-factor authentication.
- Use HTTPS in production.
- Perform regular security testing.
- Implement automated database backups.

## 6. Conclusion
TrustVault provides basic security features for managing documents safely. Authentication, authorization, file validation and permission checks help protect documents from unauthorized access. Additional security improvements are recommended before production deployment.