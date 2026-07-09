from fastapi import HTTPException, Request, BackgroundTasks
from src.staff.dtos import UserSchema, LoginSchema, UserUpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from src.staff.models import UserModel
from fastapi import status
from src.utils.settings import settings
import jwt
from jwt.exceptions import InvalidTokenError
from src.utils.mail import send_email, send_notification_email
import uuid
from markupsafe import escape
from src.utils.helpers import is_authenticated as check_user_authenticated
from sqlalchemy.future import select
from src.utils.redis import redis_client

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

async def register(user: UserSchema, background_tasks: BackgroundTasks, db: AsyncSession):

    #First, Check if the full_name already exists
    stmt = select(UserModel).where(UserModel.name == user.name)
    result = await db.execute(stmt)
    db_name_and_email = result.scalar_one_or_none()
    
    if db_name_and_email:
        raise HTTPException(status_code=400, detail="Name already exists")

    #Second, Check and validate email
    stmt = select(UserModel).where(UserModel.email == user.email)
    result = await db.execute(stmt)
    db_name_and_email = result.scalar_one_or_none()
    
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
    await db.commit()
    await db.refresh(db_user)

    # Send email to user in the background after returning response
    background_tasks.add_task(send_email, [user.email])

    return db_user


#########################################################################################################################

async def get_all_users(db: AsyncSession, offset: int = 0, limit: int = 50):
    # Get all users from the database, excluding HR and soft-deleted/inactive employees
    
    stmt = select(UserModel).where(
        UserModel.role != "hr", 
        UserModel.status != "Inactive"
    ).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    db_users = result.scalars().all()
    
    return db_users

#########################################################################################################################

async def login(user: LoginSchema, request: Request, db: AsyncSession):

    #First, Check if the user email matches
    stmt = select(UserModel).where(UserModel.email == user.email)
    result = await db.execute(stmt)
    db_login_user_email_and_password = result.scalar_one_or_none()
    
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

def is_authenticated(request: Request, db: AsyncSession):
    return check_user_authenticated(request, db)

#########################################################################################################################

async def logout(request: Request):
    token = request.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token not provided.")
    
    token = token.split(" ")[-1]
    try:
        # Decode the token (without verification checks, or verifying if preferred)
        data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
        jti = data.get("jti")
        exp = data.get("exp")
        
        if jti and exp:
            current_time = int(datetime.now().timestamp())
            remaining_ttl = exp - current_time
            
            # If the token is still active, add it to Redis blacklist with a TTL
            if remaining_ttl > 0:
                await redis_client.setex(f"blacklist:{jti}", remaining_ttl, "true")
                
        return {"detail": "Successfully logged out."}
    except Exception:
        # Return success anyway, as an invalid/malformed token is effectively unusable
        return {"detail": "Successfully logged out."}

###########################################################################################

#Logic to carry out the EDIT/UPDATE User request
async def edit_user_by_id(staff_id: int, user: UserUpdateSchema, user_logged: UserModel, db: AsyncSession):
    # Enforce Authorization: Must be self or HR
    if user_logged.staff_id != staff_id and user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to edit this profile.")
    
    #First, query the database for the user with the specified ID
    stmt = select(UserModel).where(UserModel.staff_id == staff_id)
    result = await db.execute(stmt)
    db_edit_user_by_id = result.scalar_one_or_none()

    #Check if the user exists
    if db_edit_user_by_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    #Second, update the user details
    db_edit_user_by_id.name = user.name
    db_edit_user_by_id.email = user.email
    db_edit_user_by_id.role = user.role
    db_edit_user_by_id.department = user.department
    
    #Commit the changes to the database
    await db.commit()
    
    #Refresh the database session to reflect the changes
    await db.refresh(db_edit_user_by_id)
    
    return db_edit_user_by_id

###########################################################################################
#Logic to carry out the DEACTIVATE USER
async def deactivate_user_by_id(id: int, user_logged: UserModel, background_tasks: BackgroundTasks, db: AsyncSession):

    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can deactivate accounts.")
    
    #First, query the database for the user with the specified ID
    stmt = select(UserModel).where(UserModel.staff_id == id)
    result = await db.execute(stmt)
    db_deactivate_user_by_id = result.scalar_one_or_none()

    #Second, get the user and apply the delete method to remove it from the database
    if db_deactivate_user_by_id is not None:
        db_deactivate_user_by_id.status = "Inactive"
        await db.commit()

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
async def activate_user_by_id(id: int, user_logged: UserModel, background_tasks: BackgroundTasks, db: AsyncSession):

    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can activate accounts.")
    
    #First, query the database for the user with the specified ID
    stmt = select(UserModel).where(UserModel.staff_id == id)
    result = await db.execute(stmt)
    db_activate_user_by_id = result.scalar_one_or_none()

    #Second, get the user and apply the delete method to remove it from the database
    if db_activate_user_by_id is not None:
        db_activate_user_by_id.status = "Active"
        await db.commit()

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
async def delete_user_by_id(id: int, user_logged: UserModel, db: AsyncSession):
    # Enforce Authorization: Must be HR
    if user_logged.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can permanently delete staff accounts.")
        
    #First, query the database for the user with the specified ID
    stmt = select(UserModel).where(UserModel.staff_id == id)
    result = await db.execute(stmt)
    db_delete_user_by_id = result.scalar_one_or_none()

    #Second, get the user and apply the delete method to remove it from the database
    if db_delete_user_by_id is not None:
        await db.delete(db_delete_user_by_id)
        await db.commit()

        return {"Staff removed successfully"}
    
    return None
