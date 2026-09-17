"""
auth_service.py
Handles authentication and user account management (create/edit/delete/search),
including role-based access helpers.
"""

from database.database import get_db, now_str
from models.user import User
from utils.security import generate_salt, hash_password, verify_password, generate_temp_password
from utils.validators import is_valid_email, is_non_empty, is_valid_username, ValidationError


class AuthService:
    def __init__(self):
        self.db = get_db()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def login(self, username: str, password: str, expected_role: str = None):
        """Returns a User object on success, or raises ValidationError.
        If expected_role is given (e.g. 'admin'/'employee'/'staff'), the
        account must match that role — this backs the role-first login flow
        where the person picks their role before entering credentials."""
        if not is_non_empty(username) or not is_non_empty(password):
            raise ValidationError("Username and password are required.")

        row = self.db.fetchone(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        )
        if row is None:
            raise ValidationError("Invalid username or password.")

        user = User.from_row(row)
        if not user.is_active:
            raise ValidationError("This account has been deactivated.")

        if not verify_password(password, user.salt, user.password_hash):
            raise ValidationError("Invalid username or password.")

        if expected_role and user.role != expected_role:
            raise ValidationError(f"This account is not registered as {expected_role}.")

        return user

    # ------------------------------------------------------------------
    # User management (Admin)
    # ------------------------------------------------------------------
    def create_user(self, full_name, email, username, password, role,
                     department=None, phone=None):
        """Creates a user account with an admin-chosen password. Returns
        the new user_id."""
        if not is_non_empty(full_name):
            raise ValidationError("Full name is required.")
        if not is_valid_email(email):
            raise ValidationError("A valid email is required.")
        if not is_valid_username(username):
            raise ValidationError("Username must be 3-30 chars (letters, numbers, _ or .).")
        if not password or len(password) < 6:
            raise ValidationError("Password must be at least 6 characters.")

        if role not in ("admin", "employee", "staff"):
            raise ValidationError("Invalid role.")

        existing = self.db.fetchone(
            "SELECT user_id FROM users WHERE username = ? OR email = ?",
            (username.strip(), email.strip()),
        )
        if existing:
            raise ValidationError("A user with that username or email already exists.")

        salt = generate_salt()
        pwd_hash = hash_password(password, salt)

        cur = self.db.execute(
            """INSERT INTO users
               (full_name, email, username, password_hash, salt, role,
                department, phone, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (full_name.strip(), email.strip(), username.strip(), pwd_hash, salt,
             role, department, phone, now_str()),
        )
        user_id = cur.lastrowid

        if role == "staff":
            self.db.execute(
                "INSERT INTO support_staff (user_id, specialty) VALUES (?, ?)",
                (user_id, department or "General"),
            )

        return user_id

    def update_user(self, user_id, full_name=None, email=None, department=None,
                     phone=None, is_active=None):
        fields, params = [], []
        if full_name is not None:
            if not is_non_empty(full_name):
                raise ValidationError("Full name cannot be empty.")
            fields.append("full_name = ?")
            params.append(full_name.strip())
        if email is not None:
            if not is_valid_email(email):
                raise ValidationError("A valid email is required.")
            fields.append("email = ?")
            params.append(email.strip())
        if department is not None:
            fields.append("department = ?")
            params.append(department)
        if phone is not None:
            fields.append("phone = ?")
            params.append(phone)
        if is_active is not None:
            fields.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not fields:
            return
        params.append(user_id)
        self.db.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", params)

    def reset_password(self, user_id, new_password):
        if not new_password or len(new_password) < 6:
            raise ValidationError("Password must be at least 6 characters.")
        salt = generate_salt()
        pwd_hash = hash_password(new_password, salt)
        self.db.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?",
            (pwd_hash, salt, user_id),
        )

    def delete_user(self, user_id):
        self.db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def get_user_by_id(self, user_id):
        row = self.db.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return User.from_row(row)

    def find_for_password_reset(self, username, email, role=None):
        """Used by the Forgot Password flow. Matches on username + email
        (and optionally role) so a reset can't be triggered by guessing a
        username alone. Returns a User or None."""
        query = "SELECT * FROM users WHERE username = ? AND email = ?"
        params = [username.strip(), email.strip()]
        if role:
            query += " AND role = ?"
            params.append(role)
        row = self.db.fetchone(query, params)
        return User.from_row(row)

    def reset_password_and_generate(self, user_id):
        """Generates a new temporary password, saves its hash, and returns
        the plain-text password so it can be emailed to the user."""
        new_password = generate_temp_password()
        self.reset_password(user_id, new_password)
        return new_password

    def search_users(self, keyword="", role=None):
        query = "SELECT * FROM users WHERE (full_name LIKE ? OR email LIKE ? OR username LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY full_name ASC"
        rows = self.db.fetchall(query, params)
        return [User.from_row(r) for r in rows]

    def list_users(self, role=None):
        return self.search_users(keyword="", role=role)

    def list_staff(self):
        rows = self.db.fetchall("""
            SELECT s.staff_id, s.user_id, s.specialty, s.max_active_tickets,
                   u.full_name, u.username, u.email
            FROM support_staff s
            JOIN users u ON u.user_id = s.user_id
            WHERE u.is_active = 1
            ORDER BY u.full_name ASC
        """)
        from models.staff import Staff
        return [Staff.from_row(r) for r in rows]