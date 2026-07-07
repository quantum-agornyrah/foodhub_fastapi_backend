from pydantic import BaseModel
from datetime import date

#Schema maintained for edits or updates
class MenuSchema(BaseModel):
    id: int | None = None
    week_string: date
    date: date
    day: str
    title: str
    description: str
    image_url: str
    type: str
    status: str | None = None

#Schema for bulk operations
class MenuCreateSchema(BaseModel):
    week_string: date
    date: date
    day: str
    title: str
    description: str = ""
    image_url: str = ""
    type: str
    status: str | None = None

class BulkMenuCreateSchema(BaseModel):
    items: list[MenuCreateSchema]

#Improving endpoints for production:
#This class is a performance format or practise to make the response more readable
#This schema shows that in the response body, the ID shouldnt show
class MenuResponseSchema(BaseModel):
    id: int
    week_string: date
    date: date
    day: str
    title: str
    description: str
    image_url: str
    type: str
    status: str | None = None
