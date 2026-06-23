from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    staff_id: int
    name: str
    email: EmailStr
    role: str
    department: str
    status: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str



#Improving endpoints for production:
#This class is a pperformance format or practise to make the response more readable
#This schema shows that in the response body, the ID shouldnt show
class UserResponseSchema(BaseModel):
    staff_id: int
    name: str
    email: str
    role: str
    department: str
    status: str

#use UserUpdateSchema for PUT /employee/edit/{id}
class UserUpdateSchema(BaseModel):
    staff_id: int
    name: str
    email: str
    role: str
    department: str
    status: str
