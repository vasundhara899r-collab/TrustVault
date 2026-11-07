
# TrustVault - API Documentation

## 1. Project Overview

TrustVault is a Secure Document Management System
developed using Python Flask and SQLite.

It allows users to securely upload, download, search,
edit and manage documents based on user roles
and permissions.

## 2. Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Flask-Login
- Flask-WTF

## 3. Authentication Routes

### Login
- URL: /
- Method: GET, POST
- Description: Allows registered users to log in.
- Input: Username and Password.
- Access: Public.

### Logout
- URL: /logout
- Method: POST
- Description: Logs out the current user.
- Access: Authenticated users.

## 4. Dashboard Route

### Dashboard
- URL: /dashboard
- Method: GET
- Description: Displays uploaded documents
  according to the logged-in user's role.
- Access: Authenticated users.

## 5. Document Management Routes

### Upload Document
- URL: /upload
- Method: GET, POST
- Description: Uploads a document with its
  category and owner details.
- Access: Admin and Owner.

### Download Document
- URL: /download/<filename>
- Method: GET
- Description: Downloads a document after
  checking access permissions.
- Access: Admin, Owner and authorized Viewer.

### Edit Document
- URL: /edit/<document_id>
- Method: GET, POST
- Description: Allows authorized users to edit
  document details.
- Access: Admin, Owner and users with edit permission.

### Search Documents
- URL: /search
- Method: GET
- Description: Searches documents using
  filename, category, owner and upload date.
- Access: Authenticated users.

## 6. Permission Management Routes

### Grant Permission
- URL: /grant-permission
- Method: GET, POST
- Description: Grants read or edit permission
  to another user.
- Access: Admin and document Owner.

### Revoke Permission
- URL: /revoke-permission
- Method: GET, POST
- Description: Removes previously granted
  document access.
- Access: Admin and document Owner.

## 7. Activity Logs Route

### View Activity Logs
- URL: /activity-logs
- Method: GET
- Description: Displays user activities such as
  upload, download and other recorded actions.
- Access: Admin only.

## 8. Security Features

- Role-Based Access Control
- Secure User Authentication
- Password Hashing
- CSRF Protection
- File Extension Validation
- Secure Filename Handling
- File Size Restrictions
- Document Read/Edit Permissions
- Activity Logging

## 9. Error Handling

- 403 Forbidden: Unauthorized access.
- 404 Not Found: Requested resource not found.
- 500 Internal Server Error: Server-side error.

## 10. Live Deployment

Live URL:
https://trustvault-d7ys.onrender.com

## 11. Conclusion

TrustVault provides secure document storage,
access control, document management and
activity tracking through a Flask-based web application.
