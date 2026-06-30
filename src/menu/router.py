from fastapi import APIRouter, Depends, HTTPException, Request
from src.menu import controller
from src.menu.dtos import MenuSchema, MenuResponseSchema
from src.utils.db import get_db
from fastapi import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel
import aiofiles
import os
import uuid
from fastapi import UploadFile, File
from src.utils.storage import upload_to_s3

UPLOAD_DIR = "uploads"

#Create a route instance with a prefix menu in the links or domains
menu_router = APIRouter(prefix="/menu")

#Create a route to create a menu
@menu_router.post("/create", response_model=MenuResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_menu(menu: MenuSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):

    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can create menu items.")

    return await controller.create_menu(menu, db, user)

###########################################################################################

#Create a route to fetch all menus
@menu_router.get("/all", response_model=List[MenuResponseSchema], status_code=status.HTTP_200_OK)
async def fetch_menus(db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_menus(db, user)

###########################################################################################

#Create a route to fetch a menu by ID
@menu_router.get("/id/{id}", response_model=MenuResponseSchema, status_code=status.HTTP_200_OK)
async def fetch_menu_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    return await controller.get_menu_by_id(db, id)

###########################################################################################

#Create a route to edit menus
@menu_router.put("/edit/{id}", response_model=MenuResponseSchema, status_code=status.HTTP_200_OK)
async def edit_menu_by_id(id: int, menu: MenuSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can edit menu items.")
    
    return await controller.edit_menu_by_id(menu, db, id, user)

###########################################################################################

#Create a route to delete a menu
@menu_router.delete("/delete/{id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_by_id(id: int, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):
    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can delete menu items.")
    
    return await controller.delete_menu_by_id(id, db, user)

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