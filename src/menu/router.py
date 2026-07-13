from fastapi import APIRouter, Depends, HTTPException, Request
from src.menu import controller
from src.menu.dtos import MenuSchema, MenuResponseSchema, BulkMenuCreateSchema
from src.utils.db import get_db
from fastapi import status
from datetime import date
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.helpers import is_authenticated
from src.staff.models import UserModel

from fastapi import WebSocket, WebSocketDisconnect, Query
from src.utils.db import LocalSession
from src.utils.helpers import get_user_from_token
from src.utils.ws_manager import ws_manager

import aiofiles
import os
import uuid
from fastapi import UploadFile, File
from src.utils.storage import upload_to_s3

from PIL import Image
import io

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

#Create a route to create a bulk menu
@menu_router.post("/bulk-create", response_model=List[MenuResponseSchema], status_code=status.HTTP_201_CREATED)
async def bulk_create_menu(menu: BulkMenuCreateSchema, db: AsyncSession = Depends(get_db), user: UserModel = Depends(is_authenticated)):

    # Guard check
    if user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="Only HR can create menu items.")

    return await controller.bulk_create_menu(menu, db, user)

###########################################################################################

#Create a route to fetch all menus
@menu_router.get("/all", response_model=List[MenuResponseSchema], status_code=status.HTTP_200_OK)
async def fetch_menus(
    offset: int = 0, 
    limit: int = 100,
    week_string: Optional[date] = None, 
    db: AsyncSession = Depends(get_db), 
    user: UserModel = Depends(is_authenticated)
):
    return await controller.get_menus(db, user, offset=offset, limit=limit, week_string=week_string)

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
    
    # Read raw content
    content = await file.read()
    
    # Default outputs
    filename = f"{uuid.uuid4()}.webp"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Open with Pillow (a python library for compressing images)
        img = Image.open(io.BytesIO(content))
        
        # Enforce max dimension of 800px (keeps aspect ratio)
        max_size = 800
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size))
        
        # Save as WebP with 80% quality compression
        img.save(filepath, format="WEBP", quality=80)

    except Exception as e:
        # Fallback to saving original file if file is not an image or processing fails
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
            
    image_url = f"{str(request.base_url)}uploads/{filename}"
    return {"image_url": image_url}

###########################################################################################
#Create a route to start a websocket connection
@menu_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Authenticate immediately using a temporary database session context
    async with LocalSession() as db:
        user = await get_user_from_token(token, db)
        
    if not user:
        await websocket.close(code=4003)  # Forbidden
        return
    staff_id = user.staff_id
    await ws_manager.connect(staff_id, websocket)
    try:
        while True:
            # Block to keep connection open and listen for disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(staff_id, websocket)