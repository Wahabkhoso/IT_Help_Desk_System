"""
staff.py
Support staff model — extends a user account with staff-specific attributes.
"""


class Staff:
    def __init__(self, staff_id, user_id, specialty=None, max_active_tickets=10,
                 full_name=None, username=None, email=None):
        self.staff_id = staff_id
        self.user_id = user_id
        self.specialty = specialty
        self.max_active_tickets = max_active_tickets
        # Denormalized convenience fields, populated when joined with users
        self.full_name = full_name
        self.username = username
        self.email = email

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        keys = row.keys()
        return Staff(
            staff_id=row["staff_id"],
            user_id=row["user_id"],
            specialty=row["specialty"] if "specialty" in keys else None,
            max_active_tickets=row["max_active_tickets"] if "max_active_tickets" in keys else 10,
            full_name=row["full_name"] if "full_name" in keys else None,
            username=row["username"] if "username" in keys else None,
            email=row["email"] if "email" in keys else None,
        )

    def __repr__(self):
        return f"<Staff {self.full_name or self.staff_id}>"
