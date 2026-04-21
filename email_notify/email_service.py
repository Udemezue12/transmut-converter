
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


import httpx

from email.utils import getaddresses, parseaddr
from typing import Optional
from core.email_breaker import email_breaker as breaker
from core.settings import settings

BREVO_API_KEY = settings.BREVO_API_KEY
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_SERVER = settings.EMAIL_SERVER
EMAIL_USE_TLS = settings.EMAIL_USE_TLS
EMAIL_USER = settings.EMAIL_USER
FRONTEND_URL = settings.FRONTEND_URL
CONFIG_ERROR_MESSAGE = "EMAIL_USER and EMAIL_PASSWORD must be configured"


BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def sync_brevo_send(message, name: Optional[str] = None):
    if not BREVO_API_KEY:
        raise ValueError("BREVO_API_KEY is not configured")

    def brevo_operation():
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:

            to_list = []
            addresses = getaddresses(message.get_all("To", []))

            for display_name, email in addresses:
                if not email:
                    continue

                to_list.append({
                    "email": email,
                    "name": name or display_name or "User",
                })

            if not to_list:
                raise ValueError("No valid recipients found")

            sender_name, sender_email = parseaddr(message.get("From"))

            sender = {
                "name": sender_name or "Sender",
                "email": sender_email,
            }

            html_content = None
            text_content = None

            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition", ""))

                    if "attachment" in disposition:
                        continue

                    if content_type == "text/html":
                        html_content = part.get_payload(
                            decode=True).decode(errors="ignore")

                    elif content_type == "text/plain":
                        text_content = part.get_payload(
                            decode=True).decode(errors="ignore")
            else:
                content_type = message.get_content_type()
                payload = message.get_payload(decode=True)

                if payload:
                    decoded = payload.decode(errors="ignore")

                    if content_type == "text/html":
                        html_content = decoded
                    else:
                        text_content = decoded

            payload = {
                "sender": sender,
                "to": to_list,
                "subject": message.get("Subject") or "No Subject",
            }

            if html_content:
                payload["htmlContent"] = html_content

            if text_content:
                payload["textContent"] = text_content

            with httpx.Client(timeout=15) as client:
                response = client.post(
                    BREVO_URL, json=payload, headers=headers)

            if 200 <= response.status_code < 300:
                return response.json()

            elif 400 <= response.status_code < 500:

                print("Brevo Client Error (No Retry)")
                print("Status:", response.status_code)
                print("Response:", response.text)
                return None

            else:

                print("Brevo Server Error (Retry Allowed)")
                print("Status:", response.status_code)
                print("Response:", response.text)
                response.raise_for_status()

        except httpx.TimeoutException:
            print("Brevo Timeout Error")
            raise

        except httpx.RequestError as e:
            print("Network Error:", str(e))
            raise

        except Exception as e:
            print("Unexpected Brevo Error:", str(e))
            raise

    return breaker.sync_call(brevo_operation)


def sync_send(message: MIMEMultipart):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise ValueError(CONFIG_ERROR_MESSAGE)

    def smtp_operation():
        with smtplib.SMTP(
            host=EMAIL_SERVER,
            port=EMAIL_PORT,
            timeout=30,
        ) as server:
            server.ehlo()
            if EMAIL_USE_TLS:
                server.starttls()

            server.login(
                EMAIL_USER,
                EMAIL_PASSWORD,
            )

            server.send_message(message)
            return True

    return breaker.sync_call(smtp_operation)


def send_verification_email(email: str, otp: str, token: str, name: str):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise ValueError(CONFIG_ERROR_MESSAGE)

    verify_link = f"{FRONTEND_URL}/verify-email.html?token={token}"
    text_content = f"""Hello {name},
    
    Your OTP is: {otp}
    
    Verify your email using this link:
{verify_link}
 This link expires in 1 hour.

If you did not request this, please ignore.
"""

    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Verify Your Email</h2>
            <p>Hello,</p>
            <p>Your one-time password (OTP) is:</p>
            <h3 style="color:#007bff;">{otp}</h3>
            <p>You can also verify your email by clicking the link below:</p>
            <a href="{verify_link}" style="display:inline-block;background:#28a745;color:white;padding:10px 20px;
               text-decoration:none;border-radius:4px;">Verify Email</a>
            <p>This link will expire in 1 hour.</p>
            <hr>
            <p>If you did not request this, please ignore this message.</p>
            <p>Best regards,<br>Your Support Team</p>
        </body>
        </html>
        """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify Your Email"
    message["From"] = EMAIL_USER
    message["To"] = email
    message.attach(MIMEText(html_content, "html"))
    message.attach(MIMEText(text_content, "plain"))

    try:
        sync_brevo_send(message=message, name=name)
    except Exception as e:
        print(f"Error sending verification email: {e}")
        raise


def send_password_reset_email(email: str, otp: str, token: str, name: str | None):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        raise ValueError(CONFIG_ERROR_MESSAGE)

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    text_content = f"""Hello {name},
    
    Your Password OTP is: {otp}
    
    Verify your email using this link:{reset_link}, This link expires in 1 hour. If you did not request this, please ignore. """

    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Password Reset Request</h2>
            <p>Hello,</p>
            <p>Your password reset OTP is:</p>
            <h3 style="color:#dc3545;">{otp}</h3>
            <p>Alternatively, click below to reset your password:</p>
            <a href="{reset_link}" style="display:inline-block;background:#007bff;color:white;padding:10px 20px;
               text-decoration:none;border-radius:4px;">Reset Password</a>
            <p>This link will expire in 1 hour.</p>
            <hr>
            <p>If you didn’t request this, please ignore this email.</p>
            <p>Best regards,<br>Your Support Team</p>
        </body>
        </html>
        """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset Your Password"
    message["From"] = EMAIL_USER
    message["To"] = email
    message.attach(MIMEText(html_content, "html"))
    message.attach(MIMEText(text_content, "plain"))

    try:
        sync_brevo_send(message=message, name=name)
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        raise
