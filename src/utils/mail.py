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
################################################################################################
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
# Function to send a deadline reminder email to a user
async def send_deadline_reminder(recipients: List[str], deadline_date: str, deadline_time: str, week_string: str):
    try:
        html = f"""
        <div style="margin: 0 auto;">
            <h2>Order Deadline Reminder</h2>
            <p>Hi there, this is a reminder to submit your food order for the upcoming week.</p>
            
            <div>
                <p style="margin: 5px 0;"><strong>Week:</strong> {week_string}</p>
                <p style="margin: 5px 0;"><strong>Deadline:</strong> {deadline_date} at {deadline_time}</p>
            </div>
            
            <p>Don't miss out on your meals! Log in to FoodHub now to place your order.</p>
        </div>
        """

        message = MessageSchema(
            subject=f"FoodHub Deadline Reminder - Week of {week_string}",
            recipients=recipients,
            body=html,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        return {"message": "email has been sent"}

    except Exception as e:
        print(f"Failed to send deadline reminder email: {e}")
        return {"message": "email failed", "error": str(e)}

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
    
    