from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import List
from src.utils.settings import settings

conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_USERNAME,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="FoodHub Operator",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# Function to send a registration email to a user
async def send_email(email: List[str]):
    html = """
    <p>Welcome to FoodHub.</p> 
    <p>Thank you for joining us. You can go ahead and start ordering meals.</p>
    """

    message = MessageSchema(
        subject="Registration - FoodHub",
        recipients=email,
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "email has been sent"}

################################################################################################

# Function to send custom notifications with a specific subject and HTML body
async def send_notification_email(recipients: List[str], subject: str, html_body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_body,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)

################################################################################################
    
    