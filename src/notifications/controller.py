from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from src.notifications.models import Notification
from src.notifications.manager import manager
from src.staff.models import UserModel

#Function to create a notification
async def create_notification(message: str, db: AsyncSession, staff_id: int = 0):
    if staff_id == 0:
        # First, fetch all active staff ids from the database
        stmt = select(UserModel.staff_id).where(UserModel.status == "Active")
        result = await db.execute(stmt)
        staff_ids = result.scalars().all()
        
        # Insert all active staff collected into the new database notification array
        db_notifications = []
        for sid in staff_ids:
            db_notifications.append(Notification(staff_id=sid, message=message))
        
        db.add_all(db_notifications)
        await db.commit()
        
        # Real-time WebSocket broadcast
        await manager.broadcast({"type": "notification", "message": message})
    else:
        # Private notification
        db_notification = Notification(staff_id=staff_id, message=message)
        db.add(db_notification)
        await db.commit()
        
        # Real-time WebSocket private message
        await manager.send_private_payload(staff_id, {"type": "notification", "message": message})
        
    return True

###########################################################################################
#Function to get an individual users notification
async def get_user_notifications(staff_id: int, db: AsyncSession):
    # Query the notification for a specific staff and direct to the staff page and list in descending order with a 100 pagination list
    stmt = select(Notification).where(Notification.staff_id == staff_id).order_by(Notification.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    return result.scalars().all()

###########################################################################################
#Function to mark or read or view ALL notifications
async def mark_all_as_read(staff_id: int, db: AsyncSession):
    # Query ALL notification for a staff to edit it from unread to read.
    stmt = update(Notification).where(Notification.staff_id == staff_id, Notification.is_read == False).values(is_read=True)
    await db.execute(stmt)
    await db.commit()

    return {"message": "All notifications marked as read"}

###########################################################################################
#Function to mark or read or view a specific notifications
async def mark_as_read(id: int, staff_id: int, db: AsyncSession):
    # Query the specific notifications for a specific staff to edit it from unread to read.
    stmt = select(Notification).where(Notification.id == id, Notification.staff_id == staff_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()

    if notification:
        notification.is_read = True
        await db.commit()
        
    return notification

###########################################################################################
#Function to delete notifications
async def delete_notification(id: int, staff_id: int, db: AsyncSession):
    stmt = delete(Notification).where(Notification.id == id, Notification.staff_id == staff_id)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Notification deleted"}