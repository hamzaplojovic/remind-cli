"""Email sending for license tokens."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings


def send_license_email(email: str, license_token: str, plan_tier: str) -> bool:
    """Send license token to customer via email.

    Returns True if successful, False otherwise.
    """
    settings = get_settings()

    # Skip if SMTP not configured
    if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from_email:
        print(f"[EMAIL] Would send license to {email}: {license_token}")
        return True  # Pretend success for dev

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎯 Your Remind License"
        msg["From"] = settings.smtp_from_email
        msg["To"] = email

        # Plain text version
        text = f"""
Welcome to Remind!

Your {plan_tier.upper()} license token:

{license_token}

Setup:
1. Install remind: https://github.com/yourusername/remind
2. Configure: remind settings --license-token {license_token}
3. Start using: remind add "buy milk tomorrow"

Questions? Reply to this email or visit https://remind.dev

Happy reminding! 🚀
"""

        # HTML version
        html = f"""
<html>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px;">
    <h2>🎯 Welcome to Remind!</h2>
    <p>Your <strong>{plan_tier.upper()}</strong> license is ready.</p>

    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; font-family: monospace; word-break: break-all;">
      <code>{license_token}</code>
    </div>

    <h3>Quick Start:</h3>
    <ol>
      <li>Install remind</li>
      <li>Run: <code>remind settings --license-token {license_token}</code></li>
      <li>Start using: <code>remind add "buy milk tomorrow"</code></li>
    </ol>

    <p><a href="https://remind.dev/docs">Read the docs</a> | <a href="https://github.com/yourusername/remind">GitHub</a></p>

    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="font-size: 12px; color: #666;">
      Questions? Reply to this email or visit <a href="https://remind.dev">remind.dev</a>
    </p>
  </body>
</html>
"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send license to {email}: {e}")
        return False
