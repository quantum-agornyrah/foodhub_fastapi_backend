from fastapi import APIRouter, Depends
from src.orders import controller
from src.orders.dtos import OrdersSchema, OrdersResponseSchema, OrdersUpdateSchema
from src.utils.db import get_db
from fastapi import status
from typing import List
from sqlalchemy.orm import Session
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel
# import logging

# logger = logging.getLogger("foodhub")
#Create a route instance with a prefix workorders in the links or domains
orders_router = APIRouter(prefix="/orders")

#Create a route to create a request
@orders_router.post("/create",response_model=OrdersResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_order(request: OrdersSchema, db: Session = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    
    #This is used to produce the id of the user who created the particular workOrder
    # print(user.staff_id) 
    # logger.debug("User ID: %s", user.staff_id)

    return await controller.create_order(request, db, user)

#NB:
#The response_model parameter is used to define the structure of the response data.
#And it only gives me the fields in the response i want to see / display

#NB:
#user:UserModel = Depends(is_authenticated) is for dependency injection 
#such that only authorized users can access apis

###########################################################################################

#Create a route to fetch all requests
@orders_router.get("/all",response_model=List[OrdersResponseSchema], status_code=status.HTTP_200_OK)
def fetch_orders(db: Session = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return controller.get_orders(db, user) #Return a order based on a logged in user

#We use LIST here becaue there would be alot of objects in the response body

###########################################################################################

#Create a route to fetch a request by ID
@orders_router.get("/id/{id}",response_model=OrdersResponseSchema, status_code=status.HTTP_200_OK)
def fetch_order_by_id(id: int, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    return controller.get_orders_by_id(db, id)

###########################################################################################

#Create a route to fetch a request by ID
@orders_router.get("/my/{id}",response_model=List[OrdersResponseSchema], status_code=status.HTTP_200_OK)
def fetch_my_order_by_id(id: int, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    return controller.get_my_orders_by_id(db, id, user)

###########################################################################################

#Create a route to edit requests
@orders_router.put("/edit/{id}",response_model=OrdersResponseSchema, status_code=status.HTTP_200_OK)
async def edit_order_by_id(id: int, order: OrdersUpdateSchema, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    return await controller.edit_orders_by_id(order, db, id, user)

###########################################################################################

#Create a route to delete a request
@orders_router.delete("/delete/{id}",response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_order_by_id(id: int, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    return controller.delete_orders_by_id(id, db, user)

###########################################################################################
