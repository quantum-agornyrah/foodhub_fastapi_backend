from fastapi import APIRouter, Depends
from src.staff import controller
from src.staff.dtos import UserSchema, LoginSchema, UserResponseSchema, UserUpdateSchema
from src.staff.models import UserModel
from src.utils.db import get_db
from fastapi import status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.limiter import limiter
from src.utils.helpers import is_authenticated

#Create a route instance with a prefix staff in the links or domains
staff_router = APIRouter(prefix="/staff")

#Create a route to create a user
@staff_router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def staff_register(user: UserSchema, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await controller.register(user, background_tasks, db)


###########################################################################################

#Create a route to get all users
@staff_router.get("/all", response_model=list[UserResponseSchema], status_code=status.HTTP_200_OK)
async def staff_get_all_users(db: AsyncSession = Depends(get_db)):
    return await controller.get_all_users(db)


###########################################################################################

#Create a route to login a user
@staff_router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")   # max 10 login attempts per minute per IP
async def staff_login(user: LoginSchema, request: Request, db: AsyncSession = Depends(get_db)):
    return await controller.login(user, request, db)


###########################################################################################

#Create a route to authenticate tokens
@staff_router.get("/auth", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def staff_authenticate(request: Request, db: AsyncSession = Depends(get_db)):
    return await controller.is_authenticated(request, db)


###########################################################################################

#Create a route to logout staff and blacklist tokens
@staff_router.post("/logout", status_code=status.HTTP_200_OK)
async def staff_logout(request: Request):
    return await controller.logout(request)


###########################################################################################

#Create a route to edit a user
@staff_router.put("/edit/{id}", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def staff_edit(id: int, user: UserUpdateSchema, user_logged: UserModel = Depends(is_authenticated), db: AsyncSession = Depends(get_db)):
    return await controller.edit_user_by_id(id, user, user_logged, db)


###########################################################################################

#Create a route to deactivate or activate a user
@staff_router.patch("/deactivate/{id}", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def staff_deactivate(id: int, background_tasks: BackgroundTasks, user_logged: UserModel = Depends(is_authenticated), db: AsyncSession = Depends(get_db)):
    return await controller.deactivate_user_by_id(id, user_logged, background_tasks, db)

@staff_router.patch("/activate/{id}", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def staff_activate(id: int, background_tasks: BackgroundTasks, user_logged: UserModel = Depends(is_authenticated), db: AsyncSession = Depends(get_db)):
    return await controller.activate_user_by_id(id, user_logged, background_tasks, db)

###########################################################################################

#Create a route to delete a user
@staff_router.delete("/delete/{id}", status_code=status.HTTP_200_OK)
async def staff_delete(id: int, user_logged: UserModel = Depends(is_authenticated), db: AsyncSession = Depends(get_db)):
    return await controller.delete_user_by_id(id, user_logged, db)
