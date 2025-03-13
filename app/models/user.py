from dataclasses import dataclass
from datetime import date
from typing import Optional
from app.models.base_model import BaseModel


@dataclass
class User(BaseModel):
    """
    User model representing an insurance customer
    """
    nickname: str
    full_name: str
    cell_phone: str
    car_type: str
    license_plate: str
    due_month: Optional[date] = None
    notice: Optional[date] = None
    due_day: Optional[date] = None
    made_on: Optional[date] = None
    amount: int = 0
    installments: int = 0
    policy_number: str = ""
    id: Optional[int] = None