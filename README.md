# IT Help Desk — Support Ticket Management System

A desktop **IT Help Desk / Support Ticket Management System** built with Python,
Tkinter, and SQLite. Designed as a realistic, portfolio-quality application for
a small organization or university IT department, supporting three user roles
(Admin, Employee, Support Staff), full ticket lifecycle management, PDF
reporting, and a data-driven dashboard.

---

## Features

### Login
- **Role-first login** — the app opens to a role picker (Employee / Support
  Staff / Admin); no account list or demo credentials are ever shown on screen
- Login is checked against the chosen role, so an employee's credentials
  can't be used on the staff/admin login screen (and vice versa)
- **Forgot Password** — enter your username + the email on file and a new
  temporary password is generated and emailed to you
- When an Admin adds a new **Support Staff** account, no password field is
  shown at all — a secure random password is generated automatically and
  emailed to the staff member's address along with their username

### Admin
- Secure login with hashed passwords and role-based access
- Dashboard with live statistics and Matplotlib charts (status, priority, category)
- Create / edit / deactivate / delete employee, staff, and admin accounts
- Manage support staff and monitor their workload
- View, search, filter, and open any ticket in the system
- Assign tickets to staff and change priority
- Update ticket status and add notes
- Generate professional PDF reports (summary statistics, full ticket list, single ticket)
- Change account password from Settings

### Employee
- Secure login
- Submit new tickets (title, description, category, priority)
- View and filter their own tickets by status
- Track ticket progress and read staff responses
- Close a ticket once it has been marked Resolved

### Support Staff
- Secure login
- View all tickets currently assigned to them
- Filter by priority, status, and category
- Open ticket details, add troubleshooting notes, respond to the employee
- Update ticket status (In Progress → Resolved, etc.)
- See pending vs. completed ticket counts

### Ticket Workflow
```
New → Assigned → In Progress → Resolved → Closed
                                   ↑            │
                                   └── Reopened ─┘
```

### Priorities
`Low` · `Medium` · `High` · `Critical` — High/Critical tickets are visually
highlighted with colored badges throughout the interface.

### Categories
Hardware, Software, Network, Internet, Account/Login, Email, Printer, Other.

---

## Technology Stack

| Layer          | Technology                     |
|----------------|---------------------------------|
| GUI            | Tkinter (ttk styled widgets)     |
| Database       | SQLite (via `sqlite3`, parameterized queries) |
| PDF Reports    | ReportLab                       |
| Dashboard Charts | Matplotlib (embedded via `FigureCanvasTkAgg`) |
| Password Security | PBKDF2-HMAC-SHA256 with per-user salt |

---

## Project Architecture

```
IT_Help_Desk/
│
├── main.py                    # Application entry point
├── requirements.txt
├── README.md
│
├── database/
│   ├── database.py            # Connection singleton + schema creation
│   └── helpdesk.db            # Created automatically on first run
│
├── models/
│   ├── user.py                # User data model
│   ├── ticket.py               # Ticket data model
│   └── staff.py                # Support staff data model
│
├── services/
│   ├── auth_service.py        # Login, user CRUD, password hashing
│   ├── ticket_service.py      # Ticket CRUD, workflow, search, statistics
│   └── report_service.py      # PDF generation (ReportLab)
│
├── ui/
│   ├── role_select.py          # First screen — pick Employee / Staff / Admin
│   ├── login.py                # Role-aware login screen
│   ├── forgot_password.py     # "Forgot Password?" popup
│   ├── sidebar.py               # Shared sidebar navigation component
│   ├── widgets.py               # Reusable styled widgets (buttons, cards, tables)
│   ├── admin_dashboard.py     # Admin screens + shared TicketDetailWindow/UserFormWindow
│   ├── user_dashboard.py      # Employee screens
│   └── staff_dashboard.py     # Support staff screens
│
├── reports/                    # Generated PDF reports are saved here
│   └── outbox/                  # Emails saved here if SMTP isn't configured
├── assets/                     # Reserved for icons/images
└── utils/
    ├── security.py             # Password hashing (PBKDF2) + temp password generator
    ├── email_service.py        # Sends staff-welcome / password-reset emails
    ├── validators.py           # Input validation helpers
    ├── theme.py                 # Centralized colors/fonts for consistent UI
    └── seed_data.py             # Demo data seeding (users + sample tickets)
```

The application follows a **layered architecture**:

`ui/` (Tkinter screens) → `services/` (business logic) → `models/` (data objects)
→ `database/` (SQLite access)

UI code never talks to the database directly — it always goes through a
service, which keeps validation and business rules in one place and makes the
code easy to test and extend.

---

## Database Schema

| Table              | Purpose                                                        |
|---------------------|------------------------------------------------------------------|
| `users`             | All accounts (admin/employee/staff) with hashed passwords       |
| `support_staff`     | Extends a `staff` user with specialty and capacity              |
| `categories`        | Ticket categories (Hardware, Software, Network, etc.)           |
| `tickets`           | Core ticket record: user, assignee, category, priority, status  |
| `ticket_comments`   | Threaded notes/responses on a ticket                             |
| `ticket_history`    | Audit trail of status/priority/assignment changes                |

Key relationships:
- `tickets.user_id` → `users.user_id` (who submitted it)
- `tickets.assigned_staff_id` → `support_staff.staff_id` (who's working it)
- `tickets.category_id` → `categories.category_id`
- `ticket_comments.ticket_id` / `ticket_history.ticket_id` → `tickets.ticket_id`

All queries use **parameterized SQL** to prevent injection, and foreign keys
are enforced (`PRAGMA foreign_keys = ON`).

---

## Application Screens

1. **Login** — role-aware authentication
2. **Admin → Dashboard** — stat cards + status/priority/category charts
3. **Admin → All Tickets** — searchable/filterable ticket table with assignment
4. **Admin → Manage Users** — create/edit/delete employee & admin accounts
5. **Admin → Manage Staff** — support staff list with live workload counts
6. **Admin → Reports** — generate summary & full ticket-list PDFs
7. **Admin → Settings** — change password, system info
8. **Employee → My Tickets** — filterable list of the employee's own tickets
9. **Employee → New Ticket** — submission form
10. **Staff → Assigned to Me / Pending / Completed** — staff's working queue
11. **Ticket Detail (popup)** — shared by all roles; shows info, comments,
    history-driven status/priority/assignment controls (role-gated), and PDF export

---

## User Workflow

1. Employee logs in and submits a new ticket (category + priority selected).
2. Ticket enters the system with status **New**.
3. Admin reviews the ticket, assigns it to a Support Staff member → status
   becomes **Assigned**.
4. Support Staff opens the ticket, adds troubleshooting notes, and updates
   status to **In Progress**.
5. Once solved, staff marks it **Resolved** and adds a resolution comment.
6. Employee reviews the resolution and **Closes** the ticket — or **Reopens**
   it if the issue persists.
7. Every status/priority/assignment change is recorded in `ticket_history`
   for auditing.
8. Admin can generate PDF reports at any time from the Reports screen.

---

## Installation & Running

### Requirements
- Python 3.9+
- Tkinter (bundled with most Python installs; on Linux install via
  `sudo apt install python3-tk` if missing)

### Setup
```bash
# 1. Navigate into the project folder
cd IT_Help_Desk

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

On first run, the SQLite database (`database/helpdesk.db`) and demo data are
created automatically.

### Demo Logins

The app no longer displays demo credentials on screen. For testing, the
seeded accounts are:

| Role      | Username | Password  |
|-----------|----------|-----------|
| Admin     | `admin`  | `admin123`|
| Support Staff | `staff1` / `staff2` | `staff123` |
| Employee  | `emp1` / `emp2` / `emp3` | `emp123` |

### Sending Real Emails (optional)

By default, "Forgot Password" resets and new-staff welcome emails are saved
to `reports/outbox/` as `.txt` files instead of being delivered, so the
feature works out of the box without any mail server. To send real emails,
set these environment variables before running the app (e.g. a Gmail
account with an [App Password](https://myaccount.google.com/apppasswords)):

```bash
export HELPDESK_SMTP_HOST="smtp.gmail.com"
export HELPDESK_SMTP_PORT="587"
export HELPDESK_SMTP_USER="your-email@gmail.com"
export HELPDESK_SMTP_PASSWORD="your-app-password"
export HELPDESK_FROM_EMAIL="your-email@gmail.com"

python main.py
```

If sending fails for any reason (wrong credentials, no internet), the app
automatically falls back to saving the email in `reports/outbox/` so nothing
is lost.

---

## Security Notes

- Passwords are never stored in plain text — each password is hashed with
  **PBKDF2-HMAC-SHA256** (200,000 iterations) using a unique random salt per user.
- All database access uses parameterized queries.
- Role-based access is enforced at the UI routing layer (`main.py`) and again
  inside each service method where relevant (e.g., only admins can assign tickets).
- Input validation runs in the service layer before any database write.

---

## Building a Standalone Windows .exe (Desktop App)

You can package this into a single `.exe` file that runs on any Windows
computer without needing Python installed.

### Quick way

1. Open a terminal inside the `IT_Help_Desk` folder
2. Double-click `build.bat` (or run it from the terminal: `build.bat`)
3. Wait for it to finish — this can take a minute or two
4. Your app is now at `dist\IT_Help_Desk.exe`

### Manual way

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "IT_Help_Desk" --clean main.py
```

The finished `.exe` will be in the `dist` folder.

### Important notes

- The first time you run the `.exe`, it will automatically create a
  `database` folder and a `reports` folder **right next to the .exe** —
  this is where your data lives, so keep the `.exe` in its own folder
  rather than a shared/temporary one.
- To share the app with someone else, copy the whole folder containing
  the `.exe` (once it has run at least once, that folder also has the
  `database` and `reports` subfolders inside it).
- To give it a custom icon, add an `.ico` file to `assets/` and rebuild
  with: `pyinstaller --onefile --windowed --icon assets/youricon.ico --name "IT_Help_Desk" main.py`
- A reusable `IT_Help_Desk.spec` file is also included in the project —
  after the first build, you can just run `pyinstaller IT_Help_Desk.spec`
  to rebuild with the same settings.
- Windows Defender or antivirus software sometimes flags freshly-built
  PyInstaller `.exe` files as suspicious (a known false-positive with
  this tool, not a real issue with your code) — this is normal for
  unsigned executables built this way.

---

## Extending the Project

Some natural next steps if you want to keep building this out:
- File attachment upload/download support (the schema already has an
  `attachment_path` column ready to use)
- Email notifications on ticket assignment/resolution
- Multi-admin audit log viewer using `ticket_history`

---

## License

This project was built as an educational/portfolio system and is free to use,
modify, and extend.