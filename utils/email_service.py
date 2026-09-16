"""
email_service.py
Sends account-credential and password-reset emails to users.

Configuration is read from environment variables so real SMTP credentials
are never hard-coded into the project:

    HELPDESK_SMTP_HOST
    HELPDESK_SMTP_PORT      (default 587)
    HELPDESK_SMTP_USER
    HELPDESK_SMTP_PASSWORD
    HELPDESK_FROM_EMAIL     (default: same as HELPDESK_SMTP_USER)

If these are not configured (e.g. while developing/demoing locally), emails
are instead written to the reports/outbox/ folder so the flow can still be
tested end-to-end without a real mail server.
"""

import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

SMTP_HOST = os.environ.get("HELPDESK_SMTP_HOST")
SMTP_PORT = int(os.environ.get("HELPDESK_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("HELPDESK_SMTP_USER")
SMTP_PASSWORD = os.environ.get("HELPDESK_SMTP_PASSWORD")
FROM_EMAIL = os.environ.get("HELPDESK_FROM_EMAIL", SMTP_USER or "helpdesk@example.local")

from utils.paths import get_app_dir

BASE_DIR = get_app_dir()
OUTBOX_DIR = os.path.join(BASE_DIR, "reports", "outbox")
os.makedirs(OUTBOX_DIR, exist_ok=True)


def _is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _write_to_outbox(to_email: str, subject: str, body: str) -> str:
    """Fallback used when SMTP isn't configured, so the app is still fully
    testable end-to-end. Returns the path of the saved file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_email = to_email.replace("@", "_at_").replace(".", "_")
    filepath = os.path.join(OUTBOX_DIR, f"{timestamp}_{safe_email}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"To: {to_email}\nSubject: {subject}\n\n{body}\n")
    return filepath


def send_email(to_email: str, subject: str, body: str):
    """
    Attempts to send a real email via SMTP. Falls back to saving the
    message locally (reports/outbox/) if SMTP is not configured or fails,
    so the feature can still be demonstrated without a live mail server.

    Returns (sent: bool, message: str)
    """
    if not _is_configured():
        path = _write_to_outbox(to_email, subject, body)
        return False, f"SMTP is not configured — email saved to {path}"

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        return True, f"Email sent to {to_email}."
    except Exception as e:
        path = _write_to_outbox(to_email, subject, body)
        return False, f"Could not send email ({e}) — saved to {path} instead."


def send_staff_welcome_email(to_email: str, full_name: str, username: str, password: str):
    subject = "Your IT Help Desk Support Staff Account"
    body = (
        f"Hello {full_name},\n\n"
        f"An IT Help Desk support staff account has been created for you.\n\n"
        f"Username: {username}\n"
        f"Temporary Password: {password}\n\n"
        f"Please log in and change your password as soon as possible.\n\n"
        f"— IT Help Desk System"
    )
    return send_email(to_email, subject, body)


def send_password_reset_email(to_email: str, full_name: str, username: str, new_password: str):
    subject = "Your IT Help Desk Password Has Been Reset"
    body = (
        f"Hello {full_name},\n\n"
        f"Your password was reset as requested.\n\n"
        f"Username: {username}\n"
        f"New Temporary Password: {new_password}\n\n"
        f"Please log in and change your password as soon as possible.\n"
        f"If you did not request this, please contact your IT administrator immediately.\n\n"
        f"— IT Help Desk System"
    )
    return send_email(to_email, subject, body)