from fastapi import HTTPException, Request, BackgroundTasks
from src.staff.dtos import UserSchema, LoginSchema, UserUpdateSchema
from sqlalchemy.orm import Session
from src.staff.models import UserModel
from fastapi import status
from src.utils.settings import settings
import jwt
from jwt.exceptions import InvalidTokenError
from src.utils.mail import send_email, send_notification_email
import uuid
from markupsafe import escape
from src.utils.helpers import is_authenticated as check_user_authenticated
# import logging

# logger = logging.getLogger("foodhub")


#########################################################################################################################
#An import that allows you to add dates and time unto your code
from datetime import datetime, timedelta


#########################################################################################################################
#An IMPORT and an INSTANCE are created to enable password hashing unto the database from user inputs
from pwdlib import PasswordHash
password_hash = PasswordHash.recommended()

#A function that applies the hashing to the password
def get_password_hash(password: str):
    return password_hash.hash(password)

#A function that verifies password matches
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)
#########################################################################################################################

async def register(user: UserSchema, background_tasks: BackgroundTasks, db: Session):

    #First, Check if the full_name already exists
    db_name_and_email = db.query(UserModel).filter(UserModel.name == user.name).first()
    if db_name_and_email:
        raise HTTPException(status_code=400, detail="Name already exists")

    #Second, Check and validate email
    db_name_and_email = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_name_and_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    #Third, Hash password
    db_hashed_password = get_password_hash(user.password)

    #Fourth, Create a new user to be added to the database
    db_user = UserModel(
        staff_id = user.staff_id,
        name = user.name,
        email = user.email,
        role = user.role,
        department = user.department,
        status = user.status,
        hash_password = db_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send email to user in the background after returning response
    background_tasks.add_task(send_email, [user.email])

    return db_user
    #return {"User registered successfully"}


#########################################################################################################################

def get_all_users(db: Session, offset: int = 0, limit: int = 50):
    # Get all users from the database, excluding HR and soft-deleted/inactive employees

    # All use .all(). With 10,000+ staff/orders/menus, 
    # this loads everything into memory.
    # Add offset and limit query params to every list route:
    db_users = db.query(UserModel).filter(
        UserModel.role != "hr", 
        UserModel.status != "Inactive"
    ).offset(offset).limit(limit).all()
    
    return db_users

#########################################################################################################################

def login(user: LoginSchema, request: Request, db: Session):

    #First, Check if the user email matches
    db_login_user_email_and_password = db.query(UserModel).filter(UserModel.email == user.email).first()
    if not db_login_user_email_and_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email.")
    
    #Second, Check if the user is active
    if db_login_user_email_and_password.status.lower() == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive. Contact HR."
        )
    
    #Third, check if password matches
    if not verify_password(user.password, db_login_user_email_and_password.hash_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.") 
    
    #A variable that calculates the current time the user logs in and adds the expiry time till the user logs out automatically
    exp_time = datetime.now() + timedelta(minutes=settings.EXPIRY_TIME)
    # print(exp_time)  #Display and see time differences in the terminal
    # logger.debug("Expiration time: %s", exp_time)

    #Third, generate a token that is valid after some time
    token = jwt.encode(
        {
            #Payload data that is used to encode to make the jwt token
            "staff_id": db_login_user_email_and_password.staff_id, 
            "exp": int(exp_time.timestamp()),

            #Add more fields here if needed
            "iat": int(datetime.now().timestamp()),  # Issued at
            "jti": str(uuid.uuid4()),  # Token ID for revocation
        },
        settings.SECRET_KEY,
        settings.ALGORITHM
    )
    
    return {"Staff Token": token}

#########################################################################################################################

# def is_authenticated(request:Request, db: Session):
#     #USE TRY and CATCH or EXCEPT to implement this ogic especially when the token is invalid or expired
#     try:
#         #Get the token that was generated once the user logged in and extract or 
#         #find the value of the authorization key in the headers object
#         token = request.headers.get("authorization")

#         if not token:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found.")
        
#         #NB normally, generated tokens have the prefix "jwt" prepended to it 7
#         #so this step actually removes that and helps us validate the token alone
#         token = token.split(" ")[-1]

#         #Decode the token and verify it with the params that were used to create it
#         data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)

#         #Get the user_id and the expiry time from the decoded token
#         token_staff_id = data.get("staff_id")
#         exp_time = data.get("exp")

#         #Compare expiry time to a current time
#         current_time = datetime.now().timestamp()
#         if current_time > exp_time:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
        
#         #Check if the user_id matches the one in the database
#         user = db.query(UserModel).filter(UserModel.staff_id == token_staff_id).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff ID.")

#         #If a user is deactivated while already logged in, 
#         #their old token may still work until expiry. 
#         # To block that:
#         if user.status.lower() == "inactive":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="This account is inactive."
#             )
        
#         return user
    
#     except InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are UNAUTHORIZED")


def is_authenticated(request: Request, db: Session):
    return check_user_authenticated(request, db)

###########################################################################################

#Logic to carry out the EDIT/UPDATE User request
def edit_user_by_id(staff_id: int, user: UserUpdateSchema, user_logged: UserModel, db: Session):
    # Enforce Authorization: Must be self or HR
    if user_logged.staff_id != staff_id and user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to edit this profile.")
    
    #First, query the database for the user with the specified ID
    db_edit_user_by_id = db.query(UserModel).filter(UserModel.staff_id == staff_id).first()

    #Check if the user exists
    if db_edit_user_by_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    #Second, update the user details
    db_edit_user_by_id.name = user.name
    db_edit_user_by_id.email = user.email
    db_edit_user_by_id.role = user.role
    db_edit_user_by_id.department = user.department
    
    #Commit the changes to the database
    db.commit()
    
    #Refresh the database session to reflect the changes
    db.refresh(db_edit_user_by_id)
    
    return db_edit_user_by_id

###########################################################################################
#Logic to carry out the DEACTIVATE USER
async def deactivate_user_by_id(id: int, user_logged: UserModel, background_tasks: BackgroundTasks, db: Session):

    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can deactivate accounts.")
    
    #First, query the database for the user with the specified ID
    db_deactivate_user_by_id = db.query(UserModel).filter(UserModel.staff_id == id).first()

    #Second, get the user and apply the delete method to remove it from the database
    if db_deactivate_user_by_id is not None:
        db_deactivate_user_by_id.status = "Inactive"
        db.commit()

        if db_deactivate_user_by_id.email:
            subject = "Account Deactivation Notification"
            html_content = f"""
            <h3>Account Notice</h3>
            <p>Hello {escape(db_deactivate_user_by_id.name)},</p>
            <p>Your FoodHub account has been deactivated. You will not be able to log in or order meals.</p>
            <p>If you believe this is an error, please contact HR.</p>
            """
            background_tasks.add_task(send_notification_email, [db_deactivate_user_by_id.email], subject, html_content)

        return db_deactivate_user_by_id
    
    return None 

#Logic to carry out the ACTIVATE USER
async def activate_user_by_id(id: int, user_logged: UserModel, background_tasks: BackgroundTasks, db: Session):

    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can activate accounts.")
    
    #First, query the database for the user with the specified ID
    db_activate_user_by_id = db.query(UserModel).filter(UserModel.staff_id == id).first()

    #Second, get the user and apply the delete method to remove it from the database
    if db_activate_user_by_id is not None:
        db_activate_user_by_id.status = "Active"
        db.commit()

        if db_activate_user_by_id.email:
            subject = "Account Activation Notification"
            html_content = f"""
            <h3>Account Notice</h3>
            <p>Hello {escape(db_activate_user_by_id.name)},</p>
            <p>Your FoodHub account has been activated. You can now log in and order your meals.</p>
            """
            background_tasks.add_task(send_notification_email, [db_activate_user_by_id.email], subject, html_content)

        return db_activate_user_by_id
    
    return None 

###########################################################################################
#Logic to carry out the DELETE USER request
def delete_user_by_id(id: int, user_logged: UserModel, db: Session):
    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can permanently delete staff accounts.")
        
    #First, query the database for the user with the specified ID
    db_delete_user_by_id = db.query(UserModel).filter(UserModel.staff_id == id).first()

    #Second, get the user and apply the delete method to remove it from the database
    if db_delete_user_by_id is not None:
        db.delete(db_delete_user_by_id)
        db.commit()

        return {"Staff removed successfully"}
    
    return None 
