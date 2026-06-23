from fastapi import HTTPException
from src.menu.dtos import MenuSchema
from sqlalchemy.orm import Session
from src.menu.models import Menu
from src.staff.models import UserModel

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE WORKORDER request
async def create_menu(menuItem: MenuSchema, db:Session, user: UserModel):

    #First receive and validate data
    new_menu = menuItem.model_dump()

    #Second, add data to databse by unpacking the data and using the database model as a blueprint
    db_new_menu = Menu(
            id = new_menu["id"],
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
    db.commit()
        
    #Improving endpoints for production:
    #This class is a performance format or practise to make the response more readable
    return db_new_menu

###########################################################################################
#Logic to carry out the GET REQUEST (based on the employeeID)
def get_menus(db: Session, user: UserModel, offset: int = 0, limit: int = 50):

    # 1. If the logged-in user is HR, return ALL menus from all employees
    # if user.role == "hr":
    #     return db.query(Menu).all()
        
    # 2. If the logged-in user is a worker, only return their own requests
    #First, query(SEARCH/LOOP) the database for all work orders and return ALL
    #db_all_workOrders = db.query(WorkOrder).all() #This is for all workorders including all IDs
    # db_all_menus = db.query(Menu).filter(Menu.staff_id == user.staff_id).all()

    # All use .all(). With 10,000+ staff/orders/menus, 
    # this loads everything into memory.
    # Add offset and limit query params to every list route:
    db_all_menus = db.query(Menu).offset(offset).limit(limit).all()

    return db_all_menus
    #return {"Request": db_all_requests}

###########################################################################################
#Logic to carry out the GET REQUEST BY ID request
def get_menu_by_id(db: Session, id: int):

    #First, query the database for the work order with the specified ID
    db_menu_by_id = db.query(Menu).filter(Menu.id == id).first()
    
    if db_menu_by_id is None:
        raise HTTPException(status_code=404, detail="Menu ID NOT FOUND", headers=None)
    
    return db_menu_by_id
    #return {"Work fetched": db_getworkOrder_by_id}

###########################################################################################
#Logic to carry out the EDIT/UPDATE REQUEST
async def edit_menu_by_id(menuItem: MenuSchema, db: Session, id: int, user: UserModel):
    db_edit_menu = db.query(Menu).filter(Menu.id == id).first()
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
    
    db.commit()
    return db_edit_menu


###########################################################################################
#Logic to carry out the DELETE WORKORDER request
def delete_menu_by_id(id: int, db: Session, user: UserModel):
    db_delete_menu_by_id = db.query(Menu).filter(Menu.id == id).first()

    # 1. Raise 404 if not found
    if db_delete_menu_by_id is None:
        raise HTTPException(status_code=404, detail="Menu ID NOT FOUND", headers=None)

    # 2. Check authorization
    # if db_delete_menu_by_id.staff_id != user.staff_id and user.role != "hr":
    #     raise HTTPException(status_code=403, detail="You are not authorized to delete this menu", headers=None)

    # 3. Delete from DB
    db.delete(db_delete_menu_by_id)
    db.commit()

    return {"Menu removed successfully"}
