from sqlalchemy import Column, Integer, String
from src.utils.db import Base

class UserModel(Base):
    __tablename__ = "staff_table"

    staff_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    department = Column(String)
    status = Column(String)
    hash_password = Column(String)
