"""
seed_data.py
Populates the database with demo users, staff, and sample tickets so the
application can be explored immediately after installation.
Safe to run multiple times — it checks for existing data first.
"""

from database.database import get_db
from services.auth_service import AuthService
from services.ticket_service import TicketService


def seed():
    db = get_db()
    auth = AuthService()
    ticket_service = TicketService()

    existing = db.fetchone("SELECT COUNT(*) c FROM users")["c"]
    if existing > 0:
        return  # Already seeded

    # --- Admin ---
    auth.create_user("System Administrator", "admin@helpdesk.local", "admin",
                      "admin123", "admin", department="IT Administration")

    # --- Support staff ---
    auth.create_user("Alex Rivera", "alex.rivera@helpdesk.local", "staff1",
                      "staff123", "staff", department="Network & Hardware")
    auth.create_user("Priya Nair", "priya.nair@helpdesk.local", "staff2",
                      "staff123", "staff", department="Software & Accounts")

    # --- Employees ---
    auth.create_user("John Carter", "john.carter@company.local", "emp1",
                      "emp123", "employee", department="Finance")
    auth.create_user("Maria Gomez", "maria.gomez@company.local", "emp2",
                      "emp123", "employee", department="Marketing")
    auth.create_user("David Chen", "david.chen@company.local", "emp3",
                      "emp123", "employee", department="Operations")

    categories = {c["name"]: c["category_id"] for c in ticket_service.list_categories()}
    emp1 = auth.search_users(keyword="emp1")[0]
    emp2 = auth.search_users(keyword="emp2")[0]
    emp3 = auth.search_users(keyword="emp3")[0]
    staff_list = auth.list_staff()
    staff1, staff2 = staff_list[0], staff_list[1]
    admin = auth.search_users(keyword="admin")[0]

    sample_tickets = [
        (emp1.user_id, categories["Printer"], "Office printer not responding",
         "The 3rd floor printer shows an offline error and won't print any documents.",
         "Medium"),
        (emp2.user_id, categories["Software"], "Excel crashes on large files",
         "Excel crashes whenever I open the quarterly budget spreadsheet.",
         "High"),
        (emp3.user_id, categories["Network"], "Cannot connect to VPN",
         "VPN client fails to connect from home network, error code 809.",
         "Critical"),
        (emp1.user_id, categories["Account/Login"], "Locked out of email account",
         "Entered my password incorrectly too many times and now I'm locked out.",
         "High"),
        (emp2.user_id, categories["Hardware"], "Laptop battery not charging",
         "The laptop battery stays at 1% even when plugged in overnight.",
         "Medium"),
        (emp3.user_id, categories["Internet"], "Slow internet in conference room B",
         "Video calls keep freezing due to slow internet in conference room B.",
         "Low"),
        (emp1.user_id, categories["Email"], "Not receiving external emails",
         "I haven't received any emails from outside the company since yesterday.",
         "High"),
    ]

    ticket_ids = []
    for user_id, cat_id, title, desc, priority in sample_tickets:
        tid = ticket_service.create_ticket(user_id, cat_id, title, desc, priority)
        ticket_ids.append(tid)

    # Assign and progress a few tickets to show a realistic workflow
    ticket_service.assign_ticket(ticket_ids[0], staff1.staff_id, admin.user_id)
    ticket_service.update_status(ticket_ids[0], "In Progress", staff1.user_id)
    ticket_service.add_comment(ticket_ids[0], admin.user_id, "Assigning to hardware team.")

    ticket_service.assign_ticket(ticket_ids[1], staff2.staff_id, admin.user_id)
    ticket_service.update_status(ticket_ids[1], "Resolved", admin.user_id)
    ticket_service.add_comment(ticket_ids[1], admin.user_id,
                                "Reinstalled Office and cleared the temp cache — issue resolved.")

    ticket_service.assign_ticket(ticket_ids[2], staff1.staff_id, admin.user_id)
    ticket_service.update_status(ticket_ids[2], "In Progress", admin.user_id)

    ticket_service.assign_ticket(ticket_ids[4], staff1.staff_id, admin.user_id)
    ticket_service.update_status(ticket_ids[4], "Resolved", admin.user_id)
    ticket_service.update_status(ticket_ids[4], "Closed", admin.user_id)

    print("Demo data seeded successfully.")
