from sqlalchemy import Column, Integer, String, ARRAY, Float
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base


# SQLAlchemy models: Define how data is stored in the database


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    item_data = Column(JSONB)
    embedding = Column(ARRAY(Float(precision=6)))  # Array of floats
