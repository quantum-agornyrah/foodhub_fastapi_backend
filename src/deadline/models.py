from sqlalchemy import Column, Integer, Date, DateTime
from src.utils.db import Base

class Deadline(Base):
    __tablename__ = "deadline_table"

    id = Column(Integer, primary_key=True, index=True)
    week_string = Column(Date, unique=True, index=True)
    deadline = Column(DateTime)
