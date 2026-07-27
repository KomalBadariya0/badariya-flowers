"""
Minimal SMTP mailer — stdlib only (smtplib + email), no extra dependency.

Used only for the admin login OTP email right now, but written generically
enough (send_email) that other transactional emails could reuse it later.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to_email: str, subject: str, html_body: str, text_body: str | None = None) -> None:
    """Sends a single HTML email over SMTP (STARTTLS if configured).

    Raises on failure — callers decide how to surface that (e.g. the OTP
    route turns it into a friendly "couldn't send the code" message
    instead of a raw 500).
    """
    from_email = settings.MAIL_FROM_EMAIL or settings.SMTP_USERNAME
    from_name = settings.MAIL_FROM_NAME

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email

    if text_body:
        message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(from_email, [to_email], message.as_string())


def send_otp_email(to_email: str, otp_code: str, expiry_minutes: int) -> None:
    subject = f"{otp_code} is your Badariya Flowers admin login code"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 420px; margin: auto;
                border: 1px solid #eee; border-radius: 12px; padding: 32px;">
      <h2 style="color:#5B3A29; margin-bottom: 4px;">Badariya Flowers</h2>
      <p style="color:#555; margin-top:0;">Admin panel login verification</p>
      <p>Use the code below to complete your login. It expires in
        <strong>{expiry_minutes} minutes</strong>.</p>
      <div style="font-size: 32px; letter-spacing: 8px; font-weight: 700;
                  background:#F7F1EA; color:#5B3A29; text-align:center;
                  padding: 16px; border-radius: 10px; margin: 24px 0;">
        {otp_code}
      </div>
      <p style="color:#888; font-size: 13px;">
        If you didn't try to log in, you can safely ignore this email —
        your account is still protected by your password.
      </p>
    </div>
    """
    text_body = (
        f"Your Badariya Flowers admin login code is: {otp_code}\n"
        f"It expires in {expiry_minutes} minutes.\n"
        "If you didn't try to log in, you can ignore this email."
    )

    send_email(to_email, subject, html_body, text_body)


def send_email_change_otp_email(to_email: str, otp_code: str, expiry_minutes: int) -> None:
    """Sent to the NEW email address an admin is trying to switch their
    login email to — proves they actually own/control that inbox before
    the switch is allowed to go through. Deliberately separate from
    send_otp_email (different subject/copy) so nobody confuses a login
    code with an email-change confirmation code."""
    subject = f"{otp_code} is your Badariya Flowers email change code"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 420px; margin: auto;
                border: 1px solid #eee; border-radius: 12px; padding: 32px;">
      <h2 style="color:#5B3A29; margin-bottom: 4px;">Badariya Flowers</h2>
      <p style="color:#555; margin-top:0;">Confirm your new admin login email</p>
      <p>Someone requested to change the admin login email to this address.
        Use the code below to confirm it. It expires in
        <strong>{expiry_minutes} minutes</strong>.</p>
      <div style="font-size: 32px; letter-spacing: 8px; font-weight: 700;
                  background:#F7F1EA; color:#5B3A29; text-align:center;
                  padding: 16px; border-radius: 10px; margin: 24px 0;">
        {otp_code}
      </div>
      <p style="color:#888; font-size: 13px;">
        If you didn't request this change, you can safely ignore this
        email — your login email will stay the same.
      </p>
    </div>
    """
    text_body = (
        f"Your Badariya Flowers email change code is: {otp_code}\n"
        f"It expires in {expiry_minutes} minutes.\n"
        "If you didn't request this change, you can ignore this email."
    )

    send_email(to_email, subject, html_body, text_body)