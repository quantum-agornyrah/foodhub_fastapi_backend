from fastapi import APIRouter, Depends
from src.orders import controller
from src.orders.dtos import OrdersSchema, OrdersResponseSchema, OrdersUpdateSchema
from src.utils.db import get_db
from fastapi import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel

#Create a route instance with a prefix workorders in the links or domains
orders_router = APIRouter(prefix="/orders")

#Create a route to create a request
@orders_router.post("/create", response_model=OrdersResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_order(request: OrdersSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.create_order(request, db, user)

###########################################################################################

#Create a route to fetch all requests
@orders_router.get("/all", response_model=List[OrdersResponseSchema], status_code=status.HTTP_200_OK)
async def fetch_orders(db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_orders(db, user)

###########################################################################################

#Create a route to fetch a request by ID
@orders_router.get("/id/{id}", response_model=OrdersResponseSchema, status_code=status.HTTP_200_OK)
async def fetch_order_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_orders_by_id(db, id)

###########################################################################################

#Create a route to fetch a request by ID
@orders_router.get("/my/{id}", response_model=List[OrdersResponseSchema], status_code=status.HTTP_200_OK)
async def fetch_my_order_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_my_orders_by_id(db, id, user)

###########################################################################################

#Create a route to edit requests
@orders_router.put("/edit/{id}", response_model=OrdersResponseSchema, status_code=status.HTTP_200_OK)
async def edit_order_by_id(id: int, order: OrdersUpdateSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.edit_orders_by_id(order, db, id, user)

###########################################################################################

#Create a route to delete a request
@orders_router.delete("/delete/{id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.delete_orders_by_id(id, db, user)
