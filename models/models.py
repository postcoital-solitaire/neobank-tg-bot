import typing
from datetime import datetime
from enum import Enum
from typing import List, Optional

from aiogram.filters.callback_data import CallbackData

import content
from orm.base_model import BaseModel, AbstractModel

class Action(str, Enum):
    verificate = "verificate"
    cancel = "cancel"
    edit = "edit"
    stop = "stop"
    edit_numbers = "edit_numbers"
    edit_birthdate = "edit_birthdate"

    add_card = "add_card"
    del_card = "del_card"
    add_ind_card = "add_ind_card"
    verificate_card_ind = "verificate_card_ind"
    info_card = "info_card"
    back_to_profile = "back_to_profile"
    my_cards = "my_cards"
    join_group = "join_group"
    notifications = "notifications"


class DefaultActions(CallbackData, prefix="def"):
    action: Action
    cache: Optional[str]


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



