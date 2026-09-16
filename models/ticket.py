"""
ticket.py
Ticket model representing a support ticket and its lifecycle.
"""

STATUS_FLOW = ["New", "Assigned", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]


class Ticket:
    def __init__(self, ticket_id, user_id, assigned_staff_id, category_id,
                 title, description, priority, status, attachment_path,
                 created_at, updated_at, resolved_at=None):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.assigned_staff_id = assigned_staff_id
        self.category_id = category_id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status
        self.attachment_path = attachment_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.resolved_at = resolved_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Ticket(
            ticket_id=row["ticket_id"],
            user_id=row["user_id"],
            assigned_staff_id=row["assigned_staff_id"],
            category_id=row["category_id"],
            title=row["title"],
            description=row["description"],
            priority=row["priority"],
            status=row["status"],
            attachment_path=row["attachment_path"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
        )

    def is_high_priority(self):
        return self.priority in ("High", "Critical")

    def __repr__(self):
        return f"<Ticket #{self.ticket_id} [{self.status}] {self.title}>"
