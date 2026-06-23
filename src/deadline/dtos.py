from pydantic import BaseModel
from datetime import date, datetime

class DeadlineSchema(BaseModel):
    week_string: date
    deadline: datetime

#Improving endpoints for production:
#This class is a performance format or practise to make the response more readable
#This schema shows that in the response body, the ID shouldnt show
class DeadlineResponseSchema(BaseModel):
    week_string: date
    deadline: datetime
