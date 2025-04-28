from dataclasses import dataclass
from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class OpenStates(StatesGroup):
    waiting_account_currency = State()
    waiting_account_amount = State()
    waiting_deposit_account = State()
    waiting_deposit_product = State()
    waiting_deposit_amount = State()
    waiting_deposit_period = State()
    waiting_deposit_auto_prolong = State()

class Action(str, Enum):
    open_menu = "open_menu"
    close_menu = "close_menu"
    info_menu = "info_menu"

    deposits = "deposits"
    credits = "credits"
    accounts = "accounts"
    products = "products"

    open_account = "open_account"
    open_deposit = "open_deposit"
    open_credit = "open_credit"

    close_account = "close_account"
    close_deposit = "close_deposit"
    close_credit = "close_credit"

    close_current_account = "close_current_account"

    prev_item = "prev_item"
    next_item = "next_item"


class DefaultActions(CallbackData, prefix="def"):
    action: Action
    cache: Optional[str] = None

@dataclass
class Account:
    id: str
    account_number: str
    amount: float
    available_amount: float
    start_date: str
    end_date: Optional[str]
    status: str
    currency_number: int

@dataclass
class DepositProduct:
    product_id: str
    name: str
    min_amount: float
    max_amount: float
    rate: float
    min_period: int
    max_period: int
    currency_number: int

@dataclass
class Deposit:
    id: str
    number: str
    amount: float
    start_date: str
    end_date: Optional[str]
    planned_end_date: str
    name: str
    product_id: str
    rate: float
    period: int
    auto_prolongation: bool
    status: str
    currency_number: int