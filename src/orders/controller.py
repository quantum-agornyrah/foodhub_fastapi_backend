from fastapi import HTTPException
from src.orders.dtos import OrdersSchema, OrdersUpdateSchema
from sqlalchemy.orm import Session
from src.orders.models import Orders
from src.staff.models import UserModel
from datetime import datetime

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE ORDER orders
async def create_order(orderItem: OrdersSchema, db:Session, user: UserModel):

    #First receive and validate data
    new_order = orderItem.model_dump()

    #Check if status is submitted
    if new_order["status"].lower() == "submitted":
        new_order["submitted_at"] = datetime.now().isoformat()

    #Second, add data to databse by unpacking the data and using the database model as a blueprint
    db_new_order = Orders(
            date = new_order["date"],
            day = new_order["day"],
            staff_name = new_order["staff_name"],
            week_string = new_order["week_string"],
            menu_item_id = new_order["menu_item_id"],
            menu_title = new_order["menu_title"],
            status = new_order["status"],
            submitted_at = new_order["submitted_at"],
            rating = new_order["rating"],
            comment = new_order["comment"],

            #Adding the foreign key column to specify the order creator owner
            staff_id = user.staff_id,
            ) 

    #Third, add the unpacked data to the database and save changes(commit)
    db.add(db_new_order)
    db.commit()
        
    #Improving endpoints for production:
    #This class is a performance format or practise to make the response more readable
    return db_new_order

###########################################################################################
#Logic to carry out the GET orders (based on the employeeID)
def get_orders(db: Session, user: UserModel, offset: int = 0, limit: int = 50):

    # 1. If the logged-in user is HR, return ALL orderss from all employees
    if user.role == "hr":
        
        # All use .all(). With 10,000+ staff/orders/menus, 
        # this loads everything into memory.
        # Add offset and limit query params to every list route:
        return db.query(Orders).offset(offset).limit(limit).all()
        
    # 2. If the logged-in user is a worker, only return their own orderss
    #First, query(SEARCH/LOOP) the database for all work orders and return ALL
    #db_all_workOrders = db.query(WorkOrder).all() #This is for all workorders including all IDs
    db_all_orders = db.query(Orders).filter(Orders.staff_id == user.staff_id).all()

    return db_all_orders
    #return {"orders": db_all_orderss}

###########################################################################################
#Logic to carry out the GET orders BY ID orders
def get_orders_by_id(db: Session, id: int):

    #First, query the database for the work order with the specified ID
    db_orders_by_id = db.query(Orders).filter(Orders.id == id).first()
    
    if db_orders_by_id is None:
        raise HTTPException(status_code=404, detail="orders ID NOT FOUND", headers=None)
    
    return db_orders_by_id
    #return {"Work fetched": db_getworkOrder_by_id}

###########################################################################################
#Logic to fetch an order based on staff_id
def get_my_orders_by_id(db: Session, id: int, user: UserModel):
    if user.staff_id != id and user.role != "hr":
        raise HTTPException(status_code=403, detail="Not authorized to view these orders")

    db_orders_by_id = db.query(Orders).filter(Orders.staff_id == id).all()

    return db_orders_by_id

###########################################################################################
#Logic to carry out the EDIT/UPDATE orders
async def edit_orders_by_id(ordersItem: OrdersUpdateSchema, db: Session, id: int, user: UserModel):

    db_edit_orders_by_id: Orders = db.query(Orders).filter(Orders.id == id).first()
    
    # 1. Raise 404 if not found
    if db_edit_orders_by_id is None:
        raise HTTPException(status_code=404, detail="Orders ID NOT FOUND", headers=None)
    
    # 2. Check authorization
    if db_edit_orders_by_id.staff_id != user.staff_id and user.role != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to edit this order", headers=None)

    # 3. Apply updates
    update_data = ordersItem.model_dump(exclude_unset=True)

    # This dynamically sets only the fields that were actually provided in the request.
    for key, value in update_data.items():
        setattr(db_edit_orders_by_id, key, value)
    
    db.commit()
    
    return db_edit_orders_by_id


###########################################################################################
#Logic to carry out the DELETE WORKORDER orders
def delete_orders_by_id(id: int, db: Session, user: UserModel):
    db_delete_orders_by_id = db.query(Orders).filter(Orders.id == id).first()

    # 1. Raise 404 if not found
    if db_delete_orders_by_id is None:
        raise HTTPException(status_code=404, detail="Orders ID NOT FOUND", headers=None)

    # 2. Check authorization
    if db_delete_orders_by_id.staff_id != user.staff_id and user.role != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to delete this order", headers=None)

    # 3. Delete from DB
    db.delete(db_delete_orders_by_id)
    db.commit()

    return None
