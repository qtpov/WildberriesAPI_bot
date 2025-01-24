from app.core.configurate import Base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, nullable=True)  # Рейтинг может быть необязательным
    stock_quantity = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def __repr__(self):
        return f"<Product(artikul={self.artikul}, name={self.name}, price={self.price}, stock_quantity={self.stock_quantity})>"

