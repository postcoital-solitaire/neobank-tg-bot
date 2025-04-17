from datetime import datetime
from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData

from orm.base_model import BaseModel


class Action(str, Enum):
    checktoken = "checktoken"

    deposits = "deposits"
    credits = "credits"
    accounts = "accounts"
    products = "products"

class DefaultActions(CallbackData, prefix="def"):
    action: Action
    cache: Optional[str] = None


class Manager(BaseModel):
    TABLE_NAME = 'managers'

    individual_id: int
    telegram_id: Optional[int]
    is_active: Optional[bool]
    username: Optional[str]

    join_time: datetime

#----------------------------

class Worker(BaseModel):
    TABLE_NAME = 'workers'

    individual_id: int
    telegram_id: Optional[int]
    owner_id: Optional[int]
    is_active: Optional[bool]
    username: Optional[str]

    join_time: datetime

class Individual(BaseModel):
    TABLE_NAME = 'individuals'

    name: str
    surname: str
    last_name: Optional[str]
    phone_number: Optional[str]
    fullname: Optional[str]
    birthdate: Optional[str]
    series: Optional[str]
    number: Optional[str]

    docx_first_page: Optional[str]
    docx_second_page: Optional[str]

class Card(BaseModel):
    TABLE_NAME = 'cards'

    worker_id: int
    is_valid: bool

    individual_id: int
    card_status: int
    age_range: int

    card_number: Optional[int]
    cvv: Optional[int]
    activation_date: Optional[str]

    add_time: datetime



