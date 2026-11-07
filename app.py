


import os
import sqlite3

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory, abort
)

from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv


# LOAD ENVIRONMENT
load_dotenv()


# FLASK APPLICATION
app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "private_uploads"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# CSRF SECURITY PROTECTION
csrf = CSRFProtect(app)


# ALLOWED FILE TYPES
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt",
    "png", "jpg", "jpeg"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# DATABASE CONNECTION
def get_db_connection():

    connection = sqlite3.connect(
        os.path.join(app.root_path, "trustvault.db")
    )

    connection.row_factory = sqlite3.Row

    return connection


# DATABASE SETUP

def init_db():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            owner TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            upload_date TEXT
        )
    """)

    # Add new columns to an existing database safely
    columns = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(documents)"
        ).fetchall()
    ]

    if "category" not in columns:
        connection.execute("""
            ALTER TABLE documents
            ADD COLUMN category TEXT NOT NULL DEFAULT 'General'
        """)

    if "upload_date" not in columns:
        connection.execute("""
            ALTER TABLE documents
            ADD COLUMN upload_date TEXT
        """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            permission TEXT NOT NULL,
            UNIQUE(document_id, username),
            FOREIGN KEY(document_id)
            REFERENCES documents(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            document_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

# Initialize database when the application starts
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
init_db()

# ACTIVITY LOG FUNCTION
def log_activity(username, action, document_name=None):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO activity_logs
        (username, action, document_name)
        VALUES (?, ?, ?)
        """,
        (username, action, document_name)
    )

    connection.commit()
    connection.close()


# USER CLASS
class User(UserMixin):

    def __init__(self, username, role):

        self.id = username
        self.username = username
        self.role = role


# DEMO USERS
users = {}

for role in ["ADMIN", "OWNER", "VIEWER"]:

    username = os.getenv(f"{role}_USERNAME")
    password = os.getenv(f"{role}_PASSWORD")

    if username and password:

        users[username] = {
            "password_hash": generate_password_hash(password),
            "role": role.lower()
        }


# LOGIN MANAGER
login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# LOAD USER
@login_manager.user_loader
def load_user(username):

    if username in users:

        return User(
            username,
            users[username]["role"]
        )

    return None


# LOGIN ROUTE
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        user = users.get(username)

        if user and check_password_hash(
            user["password_hash"], password
        ):

            login_user(
                User(username, user["role"])
            )

            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")



# UPLOAD ROUTE
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if current_user.role not in ["admin", "owner"]:
        abort(403)

    if request.method == "POST":

        if "document" not in request.files:
            flash("No file selected")
            return redirect(url_for("upload"))

        file = request.files["document"]

        if file.filename == "":
            flash("Please select a file")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("File type not allowed")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)

        if not filename:
            flash("Invalid filename")
            return redirect(url_for("upload"))

        # Get document category
        category = request.form.get("category", "General")

        allowed_categories = [
            "General", "Education", "Personal",
            "Business", "Finance", "Legal"
        ]

        if category not in allowed_categories:
            flash("Invalid document category")
            return redirect(url_for("upload"))

        connection = get_db_connection()

        existing = connection.execute(
            "SELECT id FROM documents WHERE filename = ?",
            (filename,)
        ).fetchone()

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        if existing or os.path.exists(file_path):
            connection.close()
            flash("Filename already exists. Choose another file.")
            return redirect(url_for("upload"))

        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        try:
            file.save(file_path)

            connection.execute(
                """
                INSERT INTO documents
                (filename, owner, category, upload_date)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
                """,
                (filename, current_user.username, category)
            )

            connection.commit()

        except Exception:
            connection.rollback()

            if os.path.exists(file_path):
                os.remove(file_path)

            flash("Upload failed. Please try again.")
            return redirect(url_for("upload"))

        finally:
            connection.close()

        log_activity(
            current_user.username,
            "UPLOAD",
            filename
        )

        flash("Document uploaded successfully!")

        return redirect(url_for("dashboard"))

    return render_template("upload.html")




# DASHBOARD ROUTE
@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db_connection()

    if current_user.role == "admin":

        rows = connection.execute(
            """
            SELECT id, filename, owner, category, upload_date,
                    NULL AS user_permission
            FROM documents
            ORDER BY id DESC
            """
        ).fetchall()

    elif current_user.role == "owner":

        rows = connection.execute(
            """
            SELECT id, filename, owner, category, upload_date,
                     NULL AS user_permission
            FROM documents
            WHERE owner = ?
            ORDER BY id DESC
            """,
            (current_user.username,)
        ).fetchall()

    else:

        rows = connection.execute(
            """
        SELECT documents.id, documents.filename,
       documents.owner, documents.category,
       documents.upload_date,
       permissions.permission AS user_permission
FROM documents
JOIN permissions
ON documents.id = permissions.document_id
WHERE permissions.username = ?
AND permissions.permission IN ('read', 'edit')
            ORDER BY documents.id DESC
            """,
            (current_user.username,)
        ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        documents=rows
    )



# DOCUMENT SEARCH ROUTE
@app.route("/search", methods=["GET"])
@login_required
def search_documents():

    search_query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    upload_date = request.args.get("upload_date", "").strip()

    connection = get_db_connection()

    conditions = []
    parameters = []

    if current_user.role == "admin":
        pass

    elif current_user.role == "owner":
        conditions.append("owner = ?")
        parameters.append(current_user.username)

    else:
        conditions.append("""
            id IN (
                SELECT document_id
                FROM permissions
                WHERE username = ?
                AND permission IN ('read', 'edit')
            )
        """)
        parameters.append(current_user.username)

    if search_query:
        conditions.append("(filename LIKE ? OR owner LIKE ?)")
        parameters.extend([
            f"%{search_query}%",
            f"%{search_query}%"
        ])

    if category:
        conditions.append("category = ?")
        parameters.append(category)

    if upload_date:
        conditions.append("DATE(upload_date) = ?")
        parameters.append(upload_date)

    sql = """
        SELECT filename, owner, category, upload_date
        FROM documents
    """

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY id DESC"

    rows = connection.execute(
        sql, parameters
    ).fetchall()

    connection.close()

    return render_template(
        "search.html",
        documents=rows,
        search_query=search_query,
        selected_category=category,
        selected_date=upload_date
    )


# GRANT DOCUMENT PERMISSION
@app.route("/grant-permission", methods=["GET", "POST"])
@login_required
def grant_permission():

    if current_user.role not in ["admin", "owner"]:
        abort(403)

    connection = get_db_connection()

    if request.method == "POST":

        document_id = request.form.get("document_id")

        username = request.form.get("username")

        permission = request.form.get("permission")

        if permission not in ["read", "edit"]:

            connection.close()

            abort(400)

        if username not in users:

            connection.close()

            abort(400)

        document = connection.execute(
            """
            SELECT * FROM documents
            WHERE id = ?
            """,
            (document_id,)
        ).fetchone()

        if document is None:

            connection.close()

            abort(404)

        if (
            current_user.role != "admin"
            and document["owner"] != current_user.username
        ):

            connection.close()

            abort(403)

        connection.execute(
            """
            INSERT INTO permissions
            (document_id, username, permission)
            VALUES (?, ?, ?)
            ON CONFLICT(document_id, username)
            DO UPDATE SET permission = excluded.permission
            """,
            (document_id, username, permission)
        )

        filename = document["filename"]

        connection.commit()
        connection.close()

        log_activity(
            current_user.username,
            "GRANT_PERMISSION",
            filename
        )

        flash("Permission granted successfully!")

        return redirect(url_for("dashboard"))

    if current_user.role == "admin":

        documents = connection.execute(
            """
            SELECT id, filename, owner
            FROM documents
            ORDER BY id DESC
            """
        ).fetchall()

    else:

        documents = connection.execute(
            """
            SELECT id, filename, owner
            FROM documents
            WHERE owner = ?
            ORDER BY id DESC
            """,
            (current_user.username,)
        ).fetchall()

    connection.close()

    return render_template(
        "grant_permission.html",
        documents=documents,
        users=users
    )

# REVOKE DOCUMENT PERMISSION ROUTE

@app.route("/revoke-permission", methods=["GET", "POST"])
@login_required
def revoke_permission():

    connection = get_db_connection()

    if request.method == "POST":

        permission_id = request.form.get("permission_id", type=int)

        permission = connection.execute(
            """
            SELECT permissions.id, documents.filename, documents.owner
            FROM permissions
            JOIN documents
            ON permissions.document_id = documents.id
            WHERE permissions.id = ?
            """,
            (permission_id,)
        ).fetchone()

        if permission is None:
            connection.close()
            abort(404)

        if current_user.role != "admin" and not (
            current_user.role == "owner"
            and permission["owner"] == current_user.username
        ):
            connection.close()
            abort(403)

        connection.execute(
            "DELETE FROM permissions WHERE id = ?",
            (permission_id,)
        )

        connection.commit()
        connection.close()

        log_activity(
            current_user.username,
            "REVOKE_PERMISSION",
            permission["filename"]
        )

        flash("Permission revoked successfully!")

        return redirect(url_for("revoke_permission"))

    if current_user.role == "admin":

        permissions = connection.execute(
            """
            SELECT permissions.id, permissions.username,
                   permissions.permission, documents.filename,
                   documents.owner
            FROM permissions
            JOIN documents
            ON permissions.document_id = documents.id
            ORDER BY permissions.id DESC
            """
        ).fetchall()

    elif current_user.role == "owner":

        permissions = connection.execute(
            """
            SELECT permissions.id, permissions.username,
                   permissions.permission, documents.filename,
                   documents.owner
            FROM permissions
            JOIN documents
            ON permissions.document_id = documents.id
            WHERE documents.owner = ?
            ORDER BY permissions.id DESC
            """,
            (current_user.username,)
        ).fetchall()

    else:
        connection.close()
        abort(403)

    connection.close()

    return render_template(
        "revoke_permission.html",
        permissions=permissions
    )



# EDIT DOCUMENT ROUTE
@app.route("/edit/<int:document_id>", methods=["GET", "POST"])
@login_required
def edit_document(document_id):

    connection = get_db_connection()

    document = connection.execute(
        "SELECT * FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()

    if document is None:
        connection.close()
        abort(404)

    permission = connection.execute(
        """
        SELECT permission FROM permissions
        WHERE document_id = ? AND username = ?
        """,
        (document_id, current_user.username)
    ).fetchone()

    is_owner = document["owner"] == current_user.username
    is_admin = current_user.role == "admin"

    has_edit_permission = (
        permission is not None
        and permission["permission"] == "edit"
    )

    if not (is_owner or is_admin or has_edit_permission):
        connection.close()
        abort(403)

    if request.method == "POST":

        file = request.files.get("document")

        if not file or not file.filename:
            connection.close()
            flash("Please select an updated file")
            return redirect(request.url)

        if not allowed_file(file.filename):
            connection.close()
            flash("Invalid file type")
            return redirect(request.url)

        old_filename = document["filename"]

        old_ext = old_filename.rsplit(".", 1)[-1].lower()
        new_ext = file.filename.rsplit(".", 1)[-1].lower()

        if old_ext != new_ext:
            connection.close()
            flash("Please upload the same file type")
            return redirect(request.url)

        old_path = os.path.join(
            app.config["UPLOAD_FOLDER"], old_filename
        )

        temp_path = old_path + ".tmp"

        try:
            file.save(temp_path)

            if not os.path.isfile(temp_path):
                raise Exception("File was not saved")

            os.replace(temp_path, old_path)

            connection.execute(
                """
                UPDATE documents
                SET upload_date = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (document_id,)
            )

            connection.commit()

        except Exception:
            connection.rollback()

            if os.path.exists(temp_path):
                os.remove(temp_path)

            connection.close()
            flash("Document update failed")
            return redirect(request.url)

        connection.close()

        log_activity(
            current_user.username,
            "EDIT_DOCUMENT",
            old_filename
        )

        flash("Document updated successfully!")
        return redirect(url_for("dashboard"))

    connection.close()

    return render_template(
        "edit_document.html",
        document=document
    )



# DOWNLOAD ROUTE
@app.route("/download/<filename>")
@login_required
def download(filename):

    safe_name = secure_filename(filename)

    if not safe_name or safe_name != filename:
        abort(404)

    connection = get_db_connection()

    document = connection.execute(
        """
        SELECT * FROM documents
        WHERE filename = ?
        """,
        (safe_name,)
    ).fetchone()

    if document is None:

        connection.close()

        abort(404)

    is_owner = (
        document["owner"] == current_user.username
    )

    is_admin = (
        current_user.role == "admin"
    )

    permission = connection.execute(
        """
        SELECT permission FROM permissions
        WHERE document_id = ?
        AND username = ?
        """,
        (document["id"], current_user.username)
    ).fetchone()

    connection.close()

    has_read_permission = (
        permission is not None
        and permission["permission"] in ["read", "edit"]
    )

    if not (
        is_owner
        or is_admin
        or has_read_permission
    ):

        log_activity(
            current_user.username,
            "DENIED_DOWNLOAD",
            safe_name
        )

        abort(403)

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        safe_name
    )

    if not os.path.isfile(file_path):
        abort(404)

    log_activity(
        current_user.username,
        "DOWNLOAD",
        safe_name
    )

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        safe_name,
        as_attachment=True
    )


# ADMIN ACTIVITY LOGS ROUTE
@app.route("/activity-logs")
@login_required
def activity_logs():

    if current_user.role != "admin":
        abort(403)

    connection = get_db_connection()

    logs = connection.execute(
        """
        SELECT username, action,
               document_name, timestamp
        FROM activity_logs
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "activity_logs.html",
        logs=logs
    )


# LOGOUT ROUTE
@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    session.clear()

    return redirect(url_for("login"))


# RUN APPLICATION
if __name__ == "__main__":

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    init_db()

    app.run(debug=True)
