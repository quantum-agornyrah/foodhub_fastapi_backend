from fastapi import APIRouter, Depends, HTTPException, Request
from src.menu import controller
from src.menu.dtos import MenuSchema, MenuResponseSchema
from src.utils.db import get_db
from fastapi import status
from typing import List
from sqlalchemy.orm import Session
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel
# import logging
import aiofiles
import os
import uuid
from fastapi import UploadFile, File
from src.utils.storage import upload_to_s3

UPLOAD_DIR = "uploads"
# logger = logging.getLogger("foodhub")
#Create a route instance with a prefix menu in the links or domains
menu_router = APIRouter(prefix="/menu")

#Create a route to create a menu
@menu_router.post("/create",response_model=MenuResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_menu(menu: MenuSchema, db: Session = Depends(get_db), user: UserModel = Depends(is_authenticated)):

    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can create menu items.")
    
    #This is used to produce the id of the user who created the particular workOrder
    # print(user.staff_id) 
    # logger.debug("User ID: %s", user.staff_id)

    return await controller.create_menu(menu, db, user)

#NB:
#The response_model parameter is used to define the structure of the response data.
#And it only gives me the fields in the response i want to see / display

#NB:
#user:UserModel = Depends(is_authenticated) is for dependency injection 
#such that only authorized users can access apis

###########################################################################################

#Create a route to fetch all menus
@menu_router.get("/all",response_model=List[MenuResponseSchema], status_code=status.HTTP_200_OK)
def fetch_menus(db: Session = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return controller.get_menus(db, user) #Return a menu based on a logged in user

#We use LIST here becaue there would be alot of objects in the response body

###########################################################################################

#Create a route to fetch a menu by ID
@menu_router.get("/id/{id}",response_model=MenuResponseSchema, status_code=status.HTTP_200_OK)
def fetch_menu_by_id(id: int, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    return controller.get_menu_by_id(db, id)

###########################################################################################

#Create a route to edit menus
@menu_router.put("/edit/{id}",response_model=MenuResponseSchema, status_code=status.HTTP_200_OK)
async def edit_menu_by_id(id: int, menu: MenuSchema, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can edit menu items.")
    
    return await controller.edit_menu_by_id(menu, db, id, user)

###########################################################################################

#Create a route to delete a menu
@menu_router.delete("/delete/{id}",response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_by_id(id: int, db: Session = Depends(get_db), user:UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can delete menu items.")
    
    return controller.delete_menu_by_id(id, db, user)

###########################################################################################

#Create an upload router for local storage
@menu_router.post("/upload-image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    image_url = f"{str(request.base_url)}uploads/{filename}"
    return {"image_url": image_url}

#Create an upload router for minio storage
# @menu_router.post("/upload-image")
# async def upload_image(file: UploadFile = File(...)):
#     import uuid
#     ext = file.filename.split(".")[-1]
#     filename = f"menu/{uuid.uuid4()}.{ext}"
#     content = await file.read()
#     image_url = await upload_to_s3(content, filename, file.content_type or "image/jpeg")
#     return {"image_url": image_url}