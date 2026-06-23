from fastapi import HTTPException
from src.deadline.dtos import DeadlineSchema
from sqlalchemy.orm import Session
from src.deadline.models import Deadline
from src.staff.models import UserModel

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE WORKORDER request
def set_deadline(deadlineItem: DeadlineSchema, db: Session, user: UserModel):
    data = deadlineItem.model_dump()
    existing = db.query(Deadline).filter(Deadline.week_string == data["week_string"]).first()
    if existing:
        existing.deadline = data["deadline"]
    else:
        existing = Deadline(week_string=data["week_string"], deadline=data["deadline"])
        db.add(existing)
    db.commit()
    return existing

###########################################################################################
#Logic to carry out the GET REQUEST (based on the employeeID)
def get_deadline_by_week(week_string: str, db: Session):
    deadline = db.query(Deadline).filter(Deadline.week_string == week_string).first()
    return deadline or {"week_string": week_string, "deadline": None}

###########################################################################################
#Logic to carry out the GET REQUEST BY ID request
def get_deadline_by_id(db: Session, id: int):

    #First, query the database for the work order with the specified ID
    db_deadline_by_id = db.query(Deadline).filter(Deadline.id == id).first()
    
    if db_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)
    
    return db_deadline_by_id
    #return {"Work fetched": db_getworkOrder_by_id}

###########################################################################################
#Logic to carry out the EDIT/UPDATE REQUEST
async def edit_deadline_by_id(deadlineItem: DeadlineSchema, db: Session, id: int, user: UserModel):

    db_edit_deadline_by_id: Deadline = db.query(Deadline).filter(Deadline.id == id).first()
    
    # 1. Raise 404 if not found
    if db_edit_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)
    
    # 2. Check authorization
    # if db_edit_menu_by_id.staff_id != user.staff_id and user.role != "hr":
    #     raise HTTPException(status_code=403, detail="You are not authorized to edit this menu", headers=None)

    # 3. Apply updates
    db_edit_deadline_by_id.deadline = deadlineItem.deadline

    # OR USE THE ARRAY METHOD after converting the pydantic model to a dictionary
    # deadlineItem.model_dump()
    # db_edit_deadline_by_id.deadline = deadlineItem["deadline"]
    
    db.commit()
    
    return db_edit_deadline_by_id


###########################################################################################
#Logic to carry out the DELETE WORKORDER request
def delete_deadline_by_id(id: int, db: Session, user: UserModel):
    db_delete_deadline_by_id = db.query(Deadline).filter(Deadline.id == id).first()

    # 1. Raise 404 if not found
    if db_delete_deadline_by_id is None:
        raise HTTPException(status_code=404, detail="Deadline ID NOT FOUND", headers=None)

    # 2. Check authorization
    # if db_delete_menu_by_id.staff_id != user.staff_id and user.role != "hr":
    #     raise HTTPException(status_code=403, detail="You are not authorized to delete this menu", headers=None)

    # 3. Delete from DB
    db.delete(db_delete_deadline_by_id)
    db.commit()

    return {"Deadline removed successfully"}
