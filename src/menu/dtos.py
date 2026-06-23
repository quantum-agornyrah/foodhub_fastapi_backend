from pydantic import BaseModel
from datetime import date

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
