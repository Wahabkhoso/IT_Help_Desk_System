"""
user.py
User model representing admins, employees, and support staff accounts.
"""


class User:
    def __init__(self, user_id, full_name, email, username, password_hash,
                 salt, role, department=None, phone=None, is_active=1,
                 created_at=None):
        self.user_id = user_id
        self.full_name = full_name
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.role = role
        self.department = department
        self.phone = phone
        self.is_active = is_active
        self.created_at = created_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return User(
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            role=row["role"],
            department=row["department"],
            phone=row["phone"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
