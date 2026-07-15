from fastapi import HTTPException, BackgroundTasks
from datetime import date
from src.deadline.dtos import DeadlineSchema
from sqlalchemy.ext.asyncio import AsyncSession
from src.deadline.models import Deadline
from src.utils.mail import send_deadline_reminder
from src.staff.models import UserModel
from sqlalchemy.future import select
from src.utils.ws_manager import ws_manager

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE WORKORDER request
async def set_deadline(deadlineItem: DeadlineSchema, db: AsyncSession, user: UserModel, background_tasks: BackgroundTasks):
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

    # WebSocket broadcast call
    await ws_manager.broadcast({"type": "deadline_updated", "week_string": str(existing.week_string)})

    # Email Implementation
    stmt = select(UserModel.email, UserModel.name).where(
        UserModel.status == "Active",
        UserModel.role != "hr"
    )

    result = await db.execute(stmt)
    staff_data = result.all()

    if staff_data:
        staff_emails = [email for (email, name) in staff_data if email]
        
        if staff_emails:
            # Format the deadline nicely
            deadline_str = str(existing.deadline)  # e.g., "2024-01-15 17:00:00"
            deadline_parts = deadline_str.split()
            deadline_date = deadline_parts[0] if len(deadline_parts) > 0 else "N/A"
            deadline_time = deadline_parts[1] if len(deadline_parts) > 1 else "N/A"
            
            # Send email in background
            background_tasks.add_task(send_deadline_reminder, staff_emails, deadline_date, deadline_time, str(existing.week_string))

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
async def edit_deadline_by_id(deadlineItem: DeadlineSchema, db: AsyncSession, id: int, user: UserModel, background_tasks: BackgroundTasks):

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

    # WebSocket broadcast call
    await ws_manager.broadcast({"type": "deadline_updated", "week_string": str(db_edit_deadline_by_id.week_string)})

    # Email implementation
    stmt = select(UserModel.email).where(
        UserModel.status == "Active",
        UserModel.role != "hr"
    )
    result = await db.execute(stmt)
    staff_emails = [email for (email,) in result.all() if email]
    
    if staff_emails:
        deadline_str = str(db_edit_deadline_by_id.deadline)
        deadline_parts = deadline_str.split()
        deadline_date = deadline_parts[0] if len(deadline_parts) > 0 else "N/A"
        deadline_time = deadline_parts[1] if len(deadline_parts) > 1 else "N/A"
        
        background_tasks.add_task(send_deadline_reminder, staff_emails, deadline_date, deadline_time, str(db_edit_deadline_by_id.week_string))
    
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
