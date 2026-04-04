import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_registration_password(email_to: str, plain_password: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP не настроен. Заполните SMTP_* переменные в .env.")

    message = EmailMessage()
    message["From"] = settings.SMTP_USERNAME
    message["To"] = email_to
    message["Subject"] = "Eco Monitoring: пароль для входа"
    message.set_content(
        "Ваш аккаунт в Eco Monitoring создан.\n\n"
        f"Email: {email_to}\n"
        f"Пароль: {plain_password}\n\n"
        "Сохраните пароль в безопасном месте."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
