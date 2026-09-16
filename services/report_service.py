"""
report_service.py
Generates professional PDF reports (individual ticket reports and summary
statistics reports) using ReportLab.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.enums import TA_CENTER

from services.ticket_service import TicketService
from utils.paths import get_app_dir

REPORTS_DIR = os.path.join(get_app_dir(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportService:
    def __init__(self):
        self.ticket_service = TicketService()
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="TitleCentered", parent=self.styles["Title"],
            alignment=TA_CENTER, textColor=colors.HexColor("#1E3A5F")
        ))

    # ------------------------------------------------------------------
    def generate_ticket_list_report(self, tickets, filename=None):
        """tickets: list of sqlite3.Row from search_tickets()/joined query."""
        if filename is None:
            filename = f"ticket_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                 topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        elements = []

        elements.append(Paragraph("IT Help Desk — Ticket Report", self.styles["TitleCentered"]))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles["Normal"]))
        elements.append(Spacer(1, 0.5 * cm))

        data = [["Ticket ID", "User", "Category", "Priority", "Assigned Staff",
                 "Status", "Created", "Resolved"]]

        for t in tickets:
            data.append([
                str(t["ticket_id"]),
                t["user_name"],
                t["category_name"],
                t["priority"],
                t["staff_name"] if t["staff_name"] else "Unassigned",
                t["status"],
                str(t["created_at"])[:16],
                str(t["resolved_at"])[:16] if t["resolved_at"] else "-",
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9DEE4")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F8")]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        doc.build(elements)
        return filepath

    # ------------------------------------------------------------------
    def generate_summary_report(self, filename=None):
        if filename is None:
            filename = f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        stats = self.ticket_service.get_dashboard_stats()
        status_dist = self.ticket_service.get_status_distribution()
        priority_dist = self.ticket_service.get_priority_distribution()
        category_dist = self.ticket_service.get_category_distribution()

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                 topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        elements = []

        elements.append(Paragraph("IT Help Desk — Summary Report", self.styles["TitleCentered"]))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles["Normal"]))
        elements.append(Spacer(1, 0.6 * cm))

        elements.append(Paragraph("Overview", self.styles["Heading2"]))
        overview_data = [["Metric", "Count"]] + [
            ["Total Tickets", stats["total_tickets"]],
            ["New Tickets", stats["new_tickets"]],
            ["In Progress", stats["in_progress_tickets"]],
            ["Resolved", stats["resolved_tickets"]],
            ["Closed", stats["closed_tickets"]],
            ["Critical (open)", stats["critical_tickets"]],
            ["Total Employees", stats["total_users"]],
            ["Total Support Staff", stats["total_staff"]],
        ]
        elements.append(self._styled_table(overview_data))
        elements.append(Spacer(1, 0.5 * cm))

        elements.append(Paragraph("Tickets by Status", self.styles["Heading2"]))
        elements.append(self._styled_table([["Status", "Count"]] + [[k, v] for k, v in status_dist.items()]))
        elements.append(Spacer(1, 0.5 * cm))

        elements.append(Paragraph("Tickets by Priority", self.styles["Heading2"]))
        elements.append(self._styled_table([["Priority", "Count"]] + [[k, v] for k, v in priority_dist.items()]))
        elements.append(Spacer(1, 0.5 * cm))

        elements.append(Paragraph("Tickets by Category", self.styles["Heading2"]))
        elements.append(self._styled_table([["Category", "Count"]] + [[k, v] for k, v in category_dist.items()]))

        doc.build(elements)
        return filepath

    def _styled_table(self, data):
        table = Table(data, hAlign="LEFT", colWidths=[8 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9DEE4")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F8")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    # ------------------------------------------------------------------
    def generate_single_ticket_pdf(self, ticket_id, filename=None):
        t = self.ticket_service.get_ticket_detail(ticket_id)
        if t is None:
            raise ValueError("Ticket not found")

        if filename is None:
            filename = f"ticket_{ticket_id}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                 topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        elements = []
        elements.append(Paragraph(f"Support Ticket #{t['ticket_id']}", self.styles["TitleCentered"]))
        elements.append(Spacer(1, 0.5 * cm))

        info = [
            ["Title", t["title"]],
            ["User", f"{t['user_name']} ({t['user_email']})"],
            ["Category", t["category_name"]],
            ["Priority", t["priority"]],
            ["Status", t["status"]],
            ["Assigned Staff", t["staff_name"] or "Unassigned"],
            ["Created", t["created_at"]],
            ["Last Updated", t["updated_at"]],
            ["Resolved", t["resolved_at"] or "-"],
        ]
        elements.append(self._styled_table(info))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("Description", self.styles["Heading3"]))
        elements.append(Paragraph(t["description"], self.styles["Normal"]))

        doc.build(elements)
        return filepath