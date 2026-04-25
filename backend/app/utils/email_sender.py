from email.message import EmailMessage
import smtplib

from fastapi import HTTPException, status

from app.config import get_settings


def send_email_code(email: str, code: str, purpose: str) -> None:
    settings = get_settings()
    if not settings.smtp_enabled:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP is not configured on the server",
        )

    subject = "港澳台考研刷题验证码"
    if purpose == "reset_password":
        intro = "你正在重置登录密码。"
    else:
        intro = "你正在注册港澳台考研刷题账号。"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = email
    message.set_content(
        f"{intro}\n\n你的验证码是：{code}\n\n验证码 10 分钟内有效，请勿泄露给他人。"
    )

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
