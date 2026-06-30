from fastapi import APIRouter, Depends, HTTPException, status
from src.deadline import controller
from src.deadline.dtos import DeadlineSchema
from src.utils.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel

deadline_router = APIRouter(prefix="/deadline")

###########################################################################################

#Create a route to create a deadline
@deadline_router.post("/", status_code=status.HTTP_201_CREATED)
async def set_deadline(deadline: DeadlineSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can set ordering deadlines.")
    
    return await controller.set_deadline(deadline, db, user)

###########################################################################################

#Create a route to get a deadline
@deadline_router.get("/{week_string}")
async def get_deadline(week_string: str, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_deadline_by_week(week_string, db)

###########################################################################################

#Create a route to edit deadlines
@deadline_router.put("/edit/{id}", response_model=DeadlineSchema, status_code=status.HTTP_200_OK)
async def edit_deadline_by_id(id: int, deadline: DeadlineSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can edit ordering deadlines.")
    
    return await controller.edit_deadline_by_id(deadline, db, id, user)

###########################################################################################

#Create a route to delete a deadline
@deadline_router.delete("/delete/{id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can delete ordering deadlines.")
    
    return await controller.delete_deadline_by_id(id, db, user)
