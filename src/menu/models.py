from sqlalchemy import Column, Integer, String, Date
from src.utils.db import Base

class Menu(Base):
    __tablename__ = "menu_table"

    id = Column(Integer, primary_key=True, index=True)
    week_string = Column(Date)
    date = Column(Date)
    day = Column(String)
    title = Column(String)
    description = Column(String)
    image_url = Column(String)
    type = Column(String)
    status = Column(String)
    
