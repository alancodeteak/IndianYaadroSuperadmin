from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db_session
from app.repositories.order_repository import OrderRepository


def get_order_repository(db: Session = Depends(get_db_session)) -> OrderRepository:
    return OrderRepository(db=db)

