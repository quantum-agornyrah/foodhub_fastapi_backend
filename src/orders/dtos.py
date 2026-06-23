from typing import Optional
from pydantic import BaseModel
from datetime import date as dt_date, datetime

class OrdersSchema(BaseModel):
    id: int | None = None   # DB auto-generates
    date: dt_date
    day: str
    staff_name: str = ""
    week_string: dt_date
    menu_title: str
    status: str
    submitted_at: datetime | None = None
    rating: int = 0
    comment: str = ""
    menu_item_id: int | None = 0


class OrdersUpdateSchema(BaseModel):
    """Partial schema for updates — all fields optional"""
    id: int | None = None
    date: Optional[dt_date] = None
    day: str | None = None
    staff_name: str | None = None
    week_string: Optional[dt_date] = None
    menu_title: str | None = None
    status: str | None = None
    submitted_at: datetime | None = None
    rating: int | None = None
    comment: str | None = None
    menu_item_id: int | None = None


#Improving endpoints for production:
#This class is a performance format or practise to make the response more readable
#This schema shows that in the response body, the ID shouldnt show
class OrdersResponseSchema(BaseModel):
    id: int | None = None   # DB auto-generates
    date: dt_date
    day: str
    staff_name: str = ""
    week_string: dt_date
    menu_title: str
    status: str
    submitted_at: datetime | None = None
    rating: int = 0
    comment: str = ""

    #Display or show the id value of the user and menu item each order is assigned
    staff_id: int
    menu_item_id: int | None = 0
