from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, CheckConstraint
from src.utils.db import Base

class Orders(Base):
    __tablename__ = "orders_table"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    day = Column(String)
    staff_name = Column(String)
    week_string = Column(Date)
    menu_title = Column(String)
    status = Column(String)
    submitted_at = Column(DateTime)
    rating = Column(Integer)
    comment = Column(String)

    __table_args__ = (
        CheckConstraint('rating >= 0 AND rating <= 5', name='check_rating_range'),
    )

    #This is where you initialize linkage between some users & menu items and the orders assigned to them specifically
    staff_id = Column(Integer, ForeignKey("staff_table.staff_id", ondelete="CASCADE"))
    menu_item_id = Column(Integer, ForeignKey("menu_table.id", ondelete="CASCADE"))