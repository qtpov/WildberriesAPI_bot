from app.core.configurate import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey,DateTime
from datetime import datetime
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    artikul = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    rating = Column(Float)
    stock_quantity = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Время последнего обновления
    # Обратная связь с подписками
    subscriptions = relationship("Subscription", back_populates="product")

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    artikul = Column(Integer, ForeignKey("products.artikul"), nullable=False)

    # Связь с продуктом
    product = relationship("Product", back_populates="subscriptions")