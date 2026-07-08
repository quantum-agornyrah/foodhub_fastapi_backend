from fastapi import HTTPException
from datetime import date
from src.deadline.dtos import DeadlineSchema
from sqlalchemy.ext.asyncio import AsyncSession
from src.deadline.models import Deadline
from src.staff.models import UserModel
from sqlalchemy.future import select
from src.utils.ws_manager import ws_manager

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE WORKORDER request
async def set_deadline(deadlineItem: DeadlineSchema, db: AsyncSession, user: UserModel):
    data = deadlineItem.model_dump()
    
    stmt = select(Deadline).where(Deadline.week_string == data["week_string"])
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.deadline = data["deadline"]
    else:
        existing = Deadline(week_string=data["week_string"], deadline=data["deadline"])
        db.add(existing)
    
    await db.commit()
    await db.refresh(existing)

    #WebSocket broadcast call
    await ws_manager.broadcast({"type": "deadline_updated", "week_string": str(existing.week_string)})

    return existing

###########################################################################################
#Logic to carry out the GET REQUEST (based on the employeeID)
async def get_deadline_by_week(week_string: date, db: AsyncSession):
    stmt = select(Deadline).where(Deadline.week_string == week_string)
    result = await db.execute(stmt)
    deadline = result.scalar_one_or_none()
    
    return deadline or {"week_string": week_string, "deadline": None}

###########################################################################################
#Logic to carry out the GET REQUEST BY ID request
async def get_deadline_by_id(db: AsyncSession, id: int):

    #First, query the database for the work order with the specified ID
    stmt = select(Deadline).where(Deadline.id == id)
    result = await db.execute(stmt)
    db_deadline_by_id = result.scalar_one_or_none()
    
    if db_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)
    
    return db_deadline_by_id

###########################################################################################
#Logic to carry out the EDIT/UPDATE REQUEST
async def edit_deadline_by_id(deadlineItem: DeadlineSchema, db: AsyncSession, id: int, user: UserModel):

    stmt = select(Deadline).where(Deadline.id == id)
    result = await db.execute(stmt)
    db_edit_deadline_by_id = result.scalar_one_or_none()
    
    # 1. Raise 404 if not found
    if db_edit_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)

    # 3. Apply updates
    db_edit_deadline_by_id.deadline = deadlineItem.deadline
    
    await db.commit()
    await db.refresh(db_edit_deadline_by_id)

    #WebSocket broadcast call
    await ws_manager.broadcast({"type": "deadline_updated", "week_string": str(db_edit_deadline_by_id.week_string)})
    
    return db_edit_deadline_by_id


###########################################################################################
#Logic to carry out the DELETE WORKORDER request
async def delete_deadline_by_id(id: int, db: AsyncSession, user: UserModel):
    stmt = select(Deadline).where(Deadline.id == id)
    result = await db.execute(stmt)
    db_delete_deadline_by_id = result.scalar_one_or_none()

    # 1. Raise 404 if not found
    if db_delete_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)

    # 3. Delete from DB
    await db.delete(db_delete_deadline_by_id)
    await db.commit()

    return {"Deadline removed successfully"}
