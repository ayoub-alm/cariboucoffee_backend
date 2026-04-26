import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core import config
from app.db import session
from app.models import Audit, User, AuditAnswer
import logging

# Set up logger for cron jobs
cron_logger = logging.getLogger("cron_service")
if not cron_logger.handlers:
    handler = logging.FileHandler("cron_jobs.log")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    cron_logger.addHandler(handler)
    cron_logger.setLevel(logging.INFO)

# ──────────────────────────────────────────────
# HTML template helpers
# ──────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 85:
        return "#2e7d32"
    if score >= 70:
        return "#e65100"
    return "#c62828"

def _score_badge_bg(score: float) -> str:
    if score >= 85:
        return "#e8f5e9"
    if score >= 70:
        return "#fff3e0"
    return "#ffebee"

def _score_label(score: float) -> str:
    if score >= 85:
        return "Conforme"
    if score >= 70:
        return "Partiel"
    return "Non-conforme"

def _non_conform_count(audit: Audit) -> int:
    count = 0
    if not audit.answers:
        return 0
    for ans in audit.answers:
        correct = ans.question.correct_answer if ans.question else "oui"
        if ans.choice and ans.choice != "n/a" and ans.choice != correct:
            count += 1
    return count

# ──────────────────────────────────────────────
# HTML email body builder
# ──────────────────────────────────────────────

def _build_html(audits: List[Audit], period_label: str, now: datetime) -> str:
    total = len(audits)
    avg_score = (sum(a.score for a in audits) / total) if total else 0
    conformes  = sum(1 for a in audits if a.score >= 85)
    total_nc_questions = sum(_non_conform_count(a) for a in audits)

    # ── Audit rows ──
    rows_html = ""
    for a in sorted(audits, key=lambda x: x.created_at, reverse=True):
        nc = _non_conform_count(a)
        score_c  = _score_color(a.score)
        score_bg = _score_badge_bg(a.score)
        score_lbl = _score_label(a.score)
        coffee   = a.coffee.name if a.coffee else "—"
        auditor  = (a.auditor.full_name or a.auditor.email) if a.auditor else "—"
        date_str = a.created_at.strftime("%d/%m/%Y %H:%M") if a.created_at else "—"
        link     = f"{config.settings.FRONTEND_URL}/audits/{a.id}"
        shift    = a.shift or "—"

        nc_cell = (
            f'<span style="color:#c62828;font-weight:700;white-space:nowrap;">{nc} NC</span>'
            if nc > 0 else
            '<span style="color:#006241;white-space:nowrap;">✔ OK</span>'
        )

        rows_html += f"""
        <tr style="border-bottom:1px solid #f0f0f0;">
          <td style="padding:12px 14px;">
            <div style="font-weight:600;color:#212121;">{coffee}</div>
            <div style="font-size:12px;color:#757575;">Shift {shift}</div>
          </td>
          <td style="padding:12px 14px;color:#424242;">{auditor}</td>
          <td style="padding:12px 14px;color:#616161;font-size:13px;white-space:nowrap;">{date_str}</td>
          <td style="padding:12px 14px;text-align:center;">
            <span style="background:{score_bg};color:{score_c};font-weight:700;
                         padding:4px 10px;border-radius:6px;font-size:13px;white-space:nowrap;">
              {a.score:.0f}% — {score_lbl}
            </span>
          </td>
          <td style="padding:12px 14px;text-align:center;white-space:nowrap;">{nc_cell}</td>
          <td style="padding:12px 14px;text-align:center;white-space:nowrap;">
            <a href="{link}"
               style="background:#006241;color:#fff;padding:6px 14px;border-radius:6px;
                      text-decoration:none;font-size:12px;font-weight:600;white-space:nowrap;display:inline-block;">
              Voir →
            </a>
          </td>
        </tr>
        """

    empty_msg = ""
    if not audits:
        empty_msg = """
        <tr>
          <td colspan="6" style="padding:32px;text-align:center;color:#9e9e9e;font-style:italic;">
            Aucun audit enregistré sur cette période.
          </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Rapport d'Audit Caribou Coffee</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
    <tr><td align="center">
      <table width="680" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#006241 0%,#004d33 100%);padding:36px 40px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#fff;letter-spacing:-0.5px;">☕ Caribou Coffee</div>
            <div style="font-size:15px;color:rgba(255,255,255,0.85);margin-top:6px;">Rapport d'Audit — {period_label}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.6);margin-top:4px;">Généré le {now.strftime("%d/%m/%Y à %H:%M")}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px 16px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#f8f9fa;border-radius:10px;">
                  <div style="font-size:32px;font-weight:800;color:#006241;">{total}</div>
                  <div style="font-size:12px;color:#757575;text-transform:uppercase;">Total audits</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:{_score_badge_bg(avg_score)};border-radius:10px;">
                  <div style="font-size:32px;font-weight:800;color:{_score_color(avg_score)};">{avg_score:.0f}%</div>
                  <div style="font-size:12px;color:#757575;text-transform:uppercase;">Score moyen</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#e8f5e9;border-radius:10px;">
                  <div style="font-size:32px;font-weight:800;color:#2e7d32;">{conformes}</div>
                  <div style="font-size:12px;color:#757575;text-transform:uppercase;">✔ Conformes</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#ffebee;border-radius:10px;">
                  <div style="font-size:32px;font-weight:800;color:#c62828;">{total_nc_questions}</div>
                  <div style="font-size:12px;color:#757575;text-transform:uppercase;">✗ Questions NC</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px 8px;">
            <div style="font-size:16px;font-weight:700;color:#212121;margin-bottom:14px;border-left:4px solid #006241;padding-left:12px;">Détail des audits</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8eaed;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background:#f8f9fa;">
                  <th style="padding:11px 14px;text-align:left;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">Établissement</th>
                  <th style="padding:11px 14px;text-align:left;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">Auditeur</th>
                  <th style="padding:11px 14px;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">Date</th>
                  <th style="padding:11px 14px;text-align:center;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">Score</th>
                  <th style="padding:11px 18px;text-align:center;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">NC</th>
                  <th style="padding:11px 18px;text-align:center;font-size:12px;color:#5f6368;font-weight:600;text-transform:uppercase;">Action</th>
                </tr>
              </thead>
              <tbody>{rows_html or empty_msg}</tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 40px;text-align:center;">
            <a href="{config.settings.FRONTEND_URL}/audits" style="background:linear-gradient(135deg,#006241,#004d33);color:#fff;padding:14px 36px;border-radius:8px;text-decoration:none;font-size:15px;font-weight:700;display:inline-block;">Ouvrir le tableau de bord →</a>
          </td>
        </tr>
        <tr>
          <td style="background:#f8f9fa;padding:20px 40px;border-top:1px solid #e8eaed;text-align:center;">
            <div style="font-size:12px;color:#9e9e9e;">Caribou Coffee — Système de gestion des audits qualité<br>Cet email a été généré automatiquement. Ne pas répondre directement.</div>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

# ──────────────────────────────────────────────
# Async Email Logic
# ──────────────────────────────────────────────

async def _send_async_email(subject: str, recipients: List[User], html_body: str, plain_body: str):
    """Sends email asynchronously to a list of recipients."""
    if not recipients:
        return

    errors = []
    for user in recipients:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{config.settings.EMAILS_FROM_NAME} <{config.settings.EMAILS_FROM_EMAIL}>"
            message["To"] = user.email

            message.attach(MIMEText(plain_body, "plain", "utf-8"))
            message.attach(MIMEText(html_body, "html", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=config.settings.SMTP_HOST,
                port=config.settings.SMTP_PORT,
                username=config.settings.SMTP_USER,
                password=config.settings.SMTP_PASSWORD,
                use_tls=False,
                start_tls=True,
                timeout=10
            )
            cron_logger.info(f"Email sent successfully to {user.email}")
        except Exception as e:
            cron_logger.error(f"Failed to send email to {user.email}: {e}")
            errors.append(str(e))
    
    if errors:
        print(f"Total email errors: {len(errors)}")

async def _get_report_data(db, days: int):
    """Fetch audits for the last N days."""
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    result = await db.execute(
        select(Audit)
        .options(
            selectinload(Audit.coffee),
            selectinload(Audit.auditor),
            selectinload(Audit.answers).selectinload(AuditAnswer.question),
        )
        .where(Audit.created_at >= start_date)
        .order_by(Audit.created_at.desc())
    )
    return result.scalars().all(), start_date, now

# ──────────────────────────────────────────────
# Public Service Functions
# ──────────────────────────────────────────────

async def send_daily_report():
    """Automated daily report trigger."""
    cron_logger.info("Starting Daily Report task...")
    async with session.SessionLocal() as db:
        audits, start, now = await _get_report_data(db, 1)
        recipients_result = await db.execute(
            select(User).where(User.receive_daily_report == True, User.is_active == True)
        )
        recipients = recipients_result.scalars().all()
        
        if not recipients: return

        period_label = f"Journalier ({start.strftime('%d/%m/%Y')})"
        subject = f"[Caribou Coffee] Rapport d'audit journalier — {start.strftime('%d/%m/%Y')}"
        html_body = _build_html(audits, period_label, now)
        plain_body = f"Rapport journalier Caribou Coffee: {len(audits)} audits."
        
        await _send_async_email(subject, recipients, html_body, plain_body)

async def send_weekly_report():
    """Automated weekly report trigger."""
    cron_logger.info("Starting Weekly Report task...")
    async with session.SessionLocal() as db:
        audits, start, now = await _get_report_data(db, 7)
        recipients_result = await db.execute(
            select(User).where(User.receive_weekly_report == True, User.is_active == True)
        )
        recipients = recipients_result.scalars().all()
        
        if not recipients: return

        period_label = f"Hebdomadaire ({start.strftime('%d/%m/%Y')} – {now.strftime('%d/%m/%Y')})"
        subject = f"[Caribou Coffee] Rapport d'audit hebdomadaire — {period_label}"
        html_body = _build_html(audits, period_label, now)
        plain_body = f"Rapport hebdomadaire Caribou Coffee: {len(audits)} audits."
        
        await _send_async_email(subject, recipients, html_body, plain_body)

async def send_monthly_report():
    """Automated monthly report trigger."""
    async with session.SessionLocal() as db:
        audits, start, now = await _get_report_data(db, 30)
        recipients_result = await db.execute(
            select(User).where(User.receive_monthly_report == True, User.is_active == True)
        )
        recipients = recipients_result.scalars().all()
        
        if not recipients: return

        period_label = f"Mensuel ({start.strftime('%B %Y')})"
        subject = f"[Caribou Coffee] Rapport d'audit mensuel — {start.strftime('%B %Y')}"
        html_body = _build_html(audits, period_label, now)
        plain_body = f"Rapport mensuel Caribou Coffee: {len(audits)} audits."
        
        await _send_async_email(subject, recipients, html_body, plain_body)

async def send_user_report(user_id: int, days: int):
    """Manual trigger for a specific user (used by API)."""
    async with session.SessionLocal() as db:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if not user or not user.is_active: return

        audits, start, now = await _get_report_data(db, days)
        
        label_map = {1: "Journalier", 7: "Hebdomadaire", 30: "Mensuel"}
        period_type = label_map.get(days, f"Derniers {days} jours")
        period_label = f"{period_type} ({start.strftime('%d/%m/%Y')} – {now.strftime('%d/%m/%Y')})"
        
        subject = f"[Caribou Coffee] Rapport d'audit {period_type.lower()} — {start.strftime('%d/%m/%Y')}"
        html_body = _build_html(audits, period_label, now)
        plain_body = f"Rapport {period_type.lower()} Caribou Coffee."
        
        await _send_async_email(subject, [user], html_body, plain_body)
