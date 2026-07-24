from fastapi import HTTPException
from src.orders.dtos import OrdersSchema, OrdersUpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from src.orders.models import Orders
from src.staff.models import UserModel
from datetime import date, datetime
from sqlalchemy.future import select

#NB: model_dump() converts a data from pydantic class to a dictionary

###########################################################################################
#Logic to carry out the CREATE ORDER orders
async def create_order(orderItem: OrdersSchema, db: AsyncSession, user: UserModel):

    #First receive and validate data
    new_order = orderItem.model_dump()

    #Check if status is submitted
    if new_order["status"].lower() == "submitted":
        new_order["submitted_at"] = datetime.now()

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
    await db.commit()
    await db.refresh(db_new_order)  # ✅ Add this
        
    #Improving endpoints for production:
    #This class is a performance format or practise to make the response more readable
    return db_new_order

###########################################################################################
#Logic to carry out the GET orders (based on the employeeID)
async def get_orders(db: AsyncSession, user: UserModel, offset: int = 0, limit: int = 100, week_string : date = None):

    # 1. If the logged-in user is HR, return ALL orderss from all employees
    if user.role == "hr":
        stmt = select(Orders)
        if week_string:
            stmt = stmt.where(Orders.week_string == week_string)
        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()
        
    # 2. If the logged-in user is a worker, only return their own orderss
    stmt = select(Orders).where(Orders.staff_id == user.staff_id)

    if week_string:
        stmt = stmt.where(Orders.week_string == week_string)

    result = await db.execute(stmt)
    db_all_orders = result.scalars().all()

    return db_all_orders

###########################################################################################
#Logic to carry out the GET orders BY ID orders
async def get_orders_by_id(db: AsyncSession, id: int):

    #First, query the database for the work order with the specified ID
    stmt = select(Orders).where(Orders.id == id)
    result = await db.execute(stmt)
    db_orders_by_id = result.scalar_one_or_none()
    
    if db_orders_by_id is None:
        raise HTTPException(status_code=404, detail="orders ID NOT FOUND", headers=None)
    
    return db_orders_by_id

###########################################################################################
#Logic to fetch an order based on staff_id
async def get_my_orders_by_id(db: AsyncSession, id: int, user: UserModel):
    if user.staff_id != id and user.role != "hr":
        raise HTTPException(status_code=403, detail="Not authorized to view these orders")

    stmt = select(Orders).where(Orders.staff_id == id)
    result = await db.execute(stmt)
    db_orders_by_id = result.scalars().all()

    return db_orders_by_id

###########################################################################################
#Logic to carry out the EDIT/UPDATE orders
async def edit_orders_by_id(ordersItem: OrdersUpdateSchema, db: AsyncSession, id: int, user: UserModel):

    stmt = select(Orders).where(Orders.id == id)
    result = await db.execute(stmt)
    db_edit_orders_by_id = result.scalar_one_or_none()
    
    # 1. Raise 404 if not found
    if db_edit_orders_by_id is None:
        raise HTTPException(status_code=404, detail="Orders ID NOT FOUND", headers=None)
    
    # 2. Check authorization
    if db_edit_orders_by_id.staff_id != user.staff_id and user.role != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to edit this order", headers=None)

    # 3. Apply updates
    update_data = ordersItem.model_dump(exclude_unset=True)

    # Automatically record submission timestamp if transitioning to submitted status
    if "status" in update_data and update_data["status"].lower() == "submitted":
        db_edit_orders_by_id.submitted_at = datetime.now()

    # This dynamically sets only the fields that were actually provided in the request.
    for key, value in update_data.items():
        setattr(db_edit_orders_by_id, key, value)
    
    await db.commit()
    await db.refresh(db_edit_orders_by_id)
    
    return db_edit_orders_by_id


###########################################################################################
#Logic to carry out the DELETE orders
async def delete_orders_by_id(id: int, db: AsyncSession, user: UserModel):
    stmt = select(Orders).where(Orders.id == id)
    result = await db.execute(stmt)
    db_delete_orders_by_id = result.scalar_one_or_none()

    # 1. Raise 404 if not found
    if db_delete_orders_by_id is None:
        raise HTTPException(status_code=404, detail="Orders ID NOT FOUND", headers=None)

    # 2. Check authorization
    if db_delete_orders_by_id.staff_id != user.staff_id and user.role != "hr":
        raise HTTPException(status_code=403, detail="You are not authorized to delete this order", headers=None)

    # 3. Delete from DB
    await db.delete(db_delete_orders_by_id)
    await db.commit()

    return None

###########################################################################################
# KEY PATTERNS TO REMEMBER:
# # Get one item
# stmt = select(Model).where(Model.id == id)
# result = await db.execute(stmt)
# item = result.scalar_one_or_none()  # Returns None if not found

# # Get all items
# stmt = select(Model).offset(offset).limit(limit)
# result = await db.execute(stmt)
# items = result.scalars().all()

# # Get all with filter
# stmt = select(Model).where(Model.status == "Active")
# result = await db.execute(stmt)
# items = result.scalars().all()

# Database Operations:
# # Create
# db.add(item)
# await db.commit()
# await db.refresh(item)

# # Update
# item.field = new_value
# await db.commit()
# await db.refresh(item)

# # Delete
# await db.delete(item)
# await db.commit()
