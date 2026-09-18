"""
ticket_service.py
Business logic for ticket creation, assignment, status transitions, comments,
history tracking, search/filtering, and dashboard statistics.
"""

from database.database import get_db, now_str
from models.ticket import Ticket, STATUS_FLOW, PRIORITIES
from utils.validators import is_non_empty, ValidationError


class TicketService:
    def __init__(self):
        self.db = get_db()

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    def create_ticket(self, user_id, category_id, title, description, priority,
                       attachment_path=None):
        if not is_non_empty(title):
            raise ValidationError("Ticket title is required.")
        if not is_non_empty(description):
            raise ValidationError("Ticket description is required.")
        if priority not in PRIORITIES:
            raise ValidationError("Invalid priority.")

        ts = now_str()
        cur = self.db.execute(
            """INSERT INTO tickets
               (user_id, assigned_staff_id, category_id, title, description,
                priority, status, attachment_path, created_at, updated_at, resolved_at)
               VALUES (?, NULL, ?, ?, ?, ?, 'New', ?, ?, ?, NULL)""",
            (user_id, category_id, title.strip(), description.strip(), priority,
             attachment_path, ts, ts),
        )
        ticket_id = cur.lastrowid
        self._log_history(ticket_id, user_id, "status", None, "New")
        return ticket_id

    # ------------------------------------------------------------------
    # Assignment & transitions
    # ------------------------------------------------------------------
    def assign_ticket(self, ticket_id, staff_id, changed_by_user_id):
        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise ValidationError("Ticket not found.")
        self.db.execute(
            "UPDATE tickets SET assigned_staff_id = ?, status = 'Assigned', updated_at = ? WHERE ticket_id = ?",
            (staff_id, now_str(), ticket_id),
        )
        self._log_history(ticket_id, changed_by_user_id, "assigned_staff_id",
                           str(ticket.assigned_staff_id), str(staff_id))
        self._log_history(ticket_id, changed_by_user_id, "status", ticket.status, "Assigned")

    def update_status(self, ticket_id, new_status, changed_by_user_id):
        if new_status not in STATUS_FLOW + ["Reopened"]:
            raise ValidationError("Invalid status.")
        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise ValidationError("Ticket not found.")

        resolved_at = ticket.resolved_at
        if new_status == "Resolved":
            resolved_at = now_str()
        elif new_status == "Reopened":
            resolved_at = None

        self.db.execute(
            "UPDATE tickets SET status = ?, updated_at = ?, resolved_at = ? WHERE ticket_id = ?",
            (new_status, now_str(), resolved_at, ticket_id),
        )
        self._log_history(ticket_id, changed_by_user_id, "status", ticket.status, new_status)

    def update_priority(self, ticket_id, new_priority, changed_by_user_id):
        if new_priority not in PRIORITIES:
            raise ValidationError("Invalid priority.")
        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise ValidationError("Ticket not found.")
        self.db.execute(
            "UPDATE tickets SET priority = ?, updated_at = ? WHERE ticket_id = ?",
            (new_priority, now_str(), ticket_id),
        )
        self._log_history(ticket_id, changed_by_user_id, "priority", ticket.priority, new_priority)

    def close_ticket(self, ticket_id, changed_by_user_id):
        self.update_status(ticket_id, "Closed", changed_by_user_id)

    def reopen_ticket(self, ticket_id, changed_by_user_id):
        self.update_status(ticket_id, "Reopened", changed_by_user_id)

    def delete_ticket(self, ticket_id, requesting_user_id=None, requesting_role=None):
        """Deletes a ticket permanently (comments and history cascade with
        it). If requesting_user_id/role are given, only the ticket's own
        submitter or an admin may delete it — a defense-in-depth check on
        top of whatever the UI already restricts."""
        ticket = self.get_ticket(ticket_id)
        if ticket is None:
            raise ValidationError("Ticket not found.")
        if requesting_role and requesting_role != "admin" and ticket.user_id != requesting_user_id:
            raise ValidationError("You can only delete your own tickets.")
        self.db.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    def add_comment(self, ticket_id, author_user_id, comment):
        if not is_non_empty(comment):
            raise ValidationError("Comment cannot be empty.")
        self.db.execute(
            "INSERT INTO ticket_comments (ticket_id, author_user_id, comment, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author_user_id, comment.strip(), now_str()),
        )
        self.db.execute("UPDATE tickets SET updated_at = ? WHERE ticket_id = ?",
                         (now_str(), ticket_id))

    def get_comments(self, ticket_id):
        return self.db.fetchall("""
            SELECT c.*, u.full_name AS author_name, u.role AS author_role
            FROM ticket_comments c
            JOIN users u ON u.user_id = c.author_user_id
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC
        """, (ticket_id,))

    def get_history(self, ticket_id):
        return self.db.fetchall("""
            SELECT h.*, u.full_name AS changed_by_name
            FROM ticket_history h
            LEFT JOIN users u ON u.user_id = h.changed_by_user_id
            WHERE h.ticket_id = ?
            ORDER BY h.changed_at ASC
        """, (ticket_id,))

    def _log_history(self, ticket_id, changed_by_user_id, field, old_value, new_value):
        self.db.execute(
            """INSERT INTO ticket_history
               (ticket_id, changed_by_user_id, field_changed, old_value, new_value, changed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ticket_id, changed_by_user_id, field, old_value, new_value, now_str()),
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def get_ticket(self, ticket_id):
        row = self.db.fetchone("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
        return Ticket.from_row(row)

    def get_ticket_detail(self, ticket_id):
        """Returns a joined row with user, staff, and category names."""
        return self.db.fetchone("""
            SELECT t.*, u.full_name AS user_name, u.email AS user_email,
                   c.name AS category_name,
                   su.full_name AS staff_name
            FROM tickets t
            JOIN users u ON u.user_id = t.user_id
            JOIN categories c ON c.category_id = t.category_id
            LEFT JOIN support_staff s ON s.staff_id = t.assigned_staff_id
            LEFT JOIN users su ON su.user_id = s.user_id
            WHERE t.ticket_id = ?
        """, (ticket_id,))

    def search_tickets(self, ticket_id=None, user_keyword=None, category_id=None,
                        priority=None, status=None, date_from=None, date_to=None,
                        assigned_staff_id=None, for_user_id=None, for_staff_id=None):
        """Flexible search/filter across all ticket fields."""
        query = """
            SELECT t.*, u.full_name AS user_name, c.name AS category_name,
                   su.full_name AS staff_name
            FROM tickets t
            JOIN users u ON u.user_id = t.user_id
            JOIN categories c ON c.category_id = t.category_id
            LEFT JOIN support_staff s ON s.staff_id = t.assigned_staff_id
            LEFT JOIN users su ON su.user_id = s.user_id
            WHERE 1=1
        """
        params = []

        if ticket_id:
            query += " AND t.ticket_id = ?"
            params.append(ticket_id)
        if user_keyword:
            query += " AND (u.full_name LIKE ? OR u.username LIKE ?)"
            params.extend([f"%{user_keyword}%", f"%{user_keyword}%"])
        if category_id:
            query += " AND t.category_id = ?"
            params.append(category_id)
        if priority:
            query += " AND t.priority = ?"
            params.append(priority)
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if date_from:
            query += " AND date(t.created_at) >= date(?)"
            params.append(date_from)
        if date_to:
            query += " AND date(t.created_at) <= date(?)"
            params.append(date_to)
        if assigned_staff_id:
            query += " AND t.assigned_staff_id = ?"
            params.append(assigned_staff_id)
        if for_user_id:
            query += " AND t.user_id = ?"
            params.append(for_user_id)
        if for_staff_id:
            query += " AND t.assigned_staff_id = ?"
            params.append(for_staff_id)

        query += " ORDER BY t.created_at DESC"
        return self.db.fetchall(query, params)

    def list_categories(self):
        return self.db.fetchall("SELECT * FROM categories ORDER BY name ASC")

    # ------------------------------------------------------------------
    # Dashboard statistics
    # ------------------------------------------------------------------
    def get_dashboard_stats(self):
        stats = {}
        stats["total_tickets"] = self.db.fetchone("SELECT COUNT(*) c FROM tickets")["c"]
        stats["new_tickets"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE status = 'New'")["c"]
        stats["in_progress_tickets"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE status = 'In Progress'")["c"]
        stats["resolved_tickets"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE status = 'Resolved'")["c"]
        stats["closed_tickets"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE status = 'Closed'")["c"]
        stats["critical_tickets"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE priority = 'Critical' AND status NOT IN ('Closed','Resolved')")["c"]
        stats["total_users"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM users WHERE role = 'employee'")["c"]
        stats["total_staff"] = self.db.fetchone(
            "SELECT COUNT(*) c FROM users WHERE role = 'staff'")["c"]
        return stats

    def get_status_distribution(self):
        rows = self.db.fetchall(
            "SELECT status, COUNT(*) c FROM tickets GROUP BY status")
        return {r["status"]: r["c"] for r in rows}

    def get_priority_distribution(self):
        rows = self.db.fetchall(
            "SELECT priority, COUNT(*) c FROM tickets GROUP BY priority")
        return {r["priority"]: r["c"] for r in rows}

    def get_category_distribution(self):
        rows = self.db.fetchall("""
            SELECT c.name, COUNT(t.ticket_id) c
            FROM categories c
            LEFT JOIN tickets t ON t.category_id = c.category_id
            GROUP BY c.name
        """)
        return {r["name"]: r["c"] for r in rows}

    def get_staff_workload(self, staff_id):
        pending = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE assigned_staff_id = ? AND status IN ('Assigned','In Progress','Reopened')",
            (staff_id,))["c"]
        completed = self.db.fetchone(
            "SELECT COUNT(*) c FROM tickets WHERE assigned_staff_id = ? AND status IN ('Resolved','Closed')",
            (staff_id,))["c"]
        return {"pending": pending, "completed": completed}