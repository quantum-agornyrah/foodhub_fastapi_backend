from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.settings import settings
from src.staff.models import UserModel
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime
from src.utils.db import get_db
from sqlalchemy.future import select


#Creating protected routes by making this fuction a dependent function
async def is_authenticated(request: Request, db: AsyncSession = Depends(get_db)): 

    #USE TRY and CATCH or EXCEPT to implement this logic especially when the token is invalid or expired
    try:
        #Get the token that was generated once the user logged in and extract or 
        #find the value of the authorization key in the headers object
        token = request.headers.get("authorization")

        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token NOT FOUND.")
        
        #NB normally, generated tokens have the prefix "jwt" prepended to it 
        #so this step actually removes that and helps us validate the token alone
        token = token.split(" ")[-1]

        #Decode the token and verify it with the params that were used to create it
        data = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)

        #Get the user_id and the expiry time from the decoded token
        token_staff_id = data.get("staff_id")
        exp_time = data.get("exp")

        #Compare expiry time to a current time
        current_time = datetime.now().timestamp()
        if current_time > exp_time:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
        
        #Check if the user_id matches the one in the database (ASYNC QUERY)
        stmt = select(UserModel).where(UserModel.staff_id == token_staff_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff ID.")

        #If a user is deactivated while already logged in, 
        #their old token may still work until expiry. 
        # To block that:
        if user.status.lower() == "inactive":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is inactive."
            )
        
        return user
    
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are UNAUTHORIZED")
