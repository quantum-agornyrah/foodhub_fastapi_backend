from fastapi import HTTPException
from src.menu.dtos import MenuSchema, BulkMenuCreateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from src.menu.models import Menu
from datetime import date
from src.staff.models import UserModel
from sqlalchemy.future import select
from src.utils.ws_manager import ws_manager
import json
from src.utils.redis import redis_client

# Helper function to serialize Menu objects to standard dictionaries
def menu_to_dict(menu: Menu) -> dict:
    return {
        "id": menu.id,
        "week_string": menu.week_string.isoformat() if menu.week_string else None,
        "date": menu.date.isoformat() if menu.date else None,
        "day": menu.day,
        "title": menu.title,
        "description": menu.description,
        "image_url": menu.image_url,
        "type": menu.type,
        "status": menu.status
    }

# Helper to scan and delete all menu cache keys when updates happen
async def invalidate_menu_cache():
    try:
        async for key in redis_client.scan_iter("menu:*"):
            await redis_client.delete(key)
    except Exception:
        # Fallback if Redis is temporarily unreachable
        pass

#NB: model_dump() converts a data from pydantic class/schema to a dictionary

###########################################################################################
#Logic to carry out the CREATE MENUITEM request
async def create_menu(menuItem: MenuSchema, db: AsyncSession, user: UserModel):

    #First receive and validate data
    new_menu = menuItem.model_dump()

    #Second, add data to databse by unpacking the data and using the database model as a blueprint
    db_new_menu = Menu(
            week_string = new_menu["week_string"],
            date = new_menu["date"],
            day = new_menu["day"],
            title = new_menu["title"],
            description = new_menu["description"],
            image_url = new_menu["image_url"],
            type = new_menu["type"],
            status = new_menu["status"],
            ) 

    #Third, add the unpacked data to the database and save changes(commit)
    db.add(db_new_menu)
    await db.commit()
    await db.refresh(db_new_menu)

    #To make sure users don't see outdated menus, INVALIDATE CACHE
    await invalidate_menu_cache()

    #WebSocket broadcast call
    await ws_manager.broadcast({"type": "menu_updated", "week_string": str(db_new_menu.week_string)})
        
    #Improving endpoints for production:
    #This class is a performance format or practise to make the response more readable
    return db_new_menu

###########################################################################################
#Logic to carry out the BULK - CREATE MENUITEM request
async def bulk_create_menu(menuItem: BulkMenuCreateSchema, db: AsyncSession, user: UserModel):
    #First, check if a menu item already exists
    if not menuItem.items:
        raise HTTPException(status_code=400, detail="No menu items provided")
    
    #Second, create an array instance to get all newly added bulk menu items
    db_bulk_items = []

    #Validate data and convert them to schema format before adding them to the database array
    for bulk_item in menuItem.items:

        #Reject items where status is off_day or holiday
        if bulk_item.status in ("off_day", "holiday"):
            raise HTTPException(status_code=400, detail="Bulk food add cannot create off-day markers.")

        new_bulk_menu = bulk_item.model_dump()
        db_bulk_items.append(Menu(**new_bulk_menu))

    db.add_all(db_bulk_items)
    
    await db.commit()

    for item in db_bulk_items:
        await db.refresh(item)

    #To make sure users don't see outdated menus, INVALIDATE CACHE
    await invalidate_menu_cache()

    #WebSocket broadcast call
    if db_bulk_items:
        await ws_manager.broadcast({"type": "menu_updated", "week_string": str(db_bulk_items[0].week_string)})
        
    #Improving endpoints for production:
    #This class is a performance format or practise to make the response more readable
    return db_bulk_items

###########################################################################################
#Logic to carry out the GET REQUEST (based on the employeeID)
async def get_menus(db: AsyncSession, user: UserModel, offset: int = 0, limit: int = 100, week_string: date = None):
    # Generate a unique cache key based on query filters
    week_str = week_string.isoformat() if week_string else "all"
    cache_key = f"menu:list:week_string:{week_str}:offset:{offset}:limit:{limit}"

    # Fetch menus from Redis first / Check if data exists in cache first
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass

    # When data doesnt exist in Redis / Cache miss? Query the database instead

    # All use .all(). With 10,000+ staff/orders/menus, 
    # this loads everything into memory.
    # Add offset and limit query params to every list route:
    
    stmt = select(Menu)

    # Group menu by weeks
    if week_string:
        stmt = stmt.where(Menu.week_string == week_string)

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    db_all_menus = result.scalars().all()

    # Store fetched data from the database unto redis for at least an hour
    try:
        serialized_menus = [menu_to_dict(m) for m in db_all_menus]
        await redis_client.setex(cache_key, 3600, json.dumps(serialized_menus))
    except Exception:
        pass

    return db_all_menus

###########################################################################################
#Logic to carry out the GET REQUEST BY ID request
async def get_menu_by_id(db: AsyncSession, id: int):
    cache_key = f"menu:id:{id}"
    #Fetch from Redis first
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception:
        pass

    #After cache miss? Query the database for the work order with the specified ID
    stmt = select(Menu).where(Menu.id == id)
    result = await db.execute(stmt)
    db_menu_by_id = result.scalar_one_or_none()
    
    if db_menu_by_id is None:
        raise HTTPException(status_code=404, detail="Menu ID NOT FOUND", headers=None)

    #Store fetched data from the database unto redis for at least an hour
    try:
        serialized_menus = menu_to_dict(db_menu_by_id)
        await redis_client.setex(cache_key, 3600, json.dumps(serialized_menus))
    except Exception:
        pass
    
    return db_menu_by_id

###########################################################################################
#Logic to carry out the EDIT/UPDATE REQUEST
async def edit_menu_by_id(menuItem: MenuSchema, db: AsyncSession, id: int, user: UserModel):
    stmt = select(Menu).where(Menu.id == id)
    result = await db.execute(stmt)
    db_edit_menu = result.scalar_one_or_none()
    
    if db_edit_menu is None:
        raise HTTPException(status_code=404, detail="Menu ID NOT FOUND")
    
    update_data = menuItem.model_dump()
    db_edit_menu.week_string = update_data["week_string"]
    db_edit_menu.date = update_data["date"]
    db_edit_menu.day = update_data["day"]
    db_edit_menu.title = update_data["title"]
    db_edit_menu.description = update_data["description"]
    db_edit_menu.image_url = update_data["image_url"]
    db_edit_menu.type = update_data["type"]
    db_edit_menu.status = update_data["status"]
    
    await db.commit()
    await db.refresh(db_edit_menu)

    #To make sure users don't see outdated menus, INVALIDATE CACHE
    await invalidate_menu_cache()

    #WebSocket broadcast call
    await ws_manager.broadcast({"type": "menu_updated", "week_string": str(db_edit_menu.week_string)})
    
    return db_edit_menu


###########################################################################################
#Logic to carry out the DELETE  request
async def delete_menu_by_id(id: int, db: AsyncSession, user: UserModel):
    stmt = select(Menu).where(Menu.id == id)
    result = await db.execute(stmt)
    db_delete_menu_by_id = result.scalar_one_or_none()

    # 1. Raise 404 if not found
    if db_delete_menu_by_id is None:
        raise HTTPException(status_code=404, detail="Menu ID NOT FOUND", headers=None)

    # 3. Delete from DB
    await db.delete(db_delete_menu_by_id)
    await db.commit()

    #To make sure users don't see outdated menus, INVALIDATE CACHE
    await invalidate_menu_cache()

    #WebSocket broadcast call
    await ws_manager.broadcast({"type": "menu_updated", "week_string": str(db_delete_menu_by_id.week_string)})

    return {"Menu removed successfully"}
