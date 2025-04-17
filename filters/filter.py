from typing import Union, Dict, Any

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message

import config as c


#from main import dm


class TypicalFilter(BaseFilter):
    def __init__(self, for_replace: Union[str, list]):
        if isinstance(for_replace, str):
            self.for_replace = [for_replace.lower()]
        else:
            self.for_replace = [s.lower() for s in for_replace]

    async def __call__(self, message: Message) -> bool:
        message_text = str(message.text).strip().lower()
        return message_text in self.for_replace

class GetTagsFilter(BaseFilter):
    #for_replace: Union[str, list]
    def __init__(self, for_replace):
         self.for_replace: Union[str, list] = for_replace

    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:

        if message.caption is not None:
            tags = message.caption.lower()
            if any(ext in tags for ext in self.for_replace):
                for replacment_text in self.for_replace:
                    tags = tags.replace(replacment_text, "")
                if len(tags.split(" ")) > 0:
                    return {"tags": tags.split(" ")}
                return False
            return False

        if message.text is not None:
            tags = message.text.lower()
            if any(ext in tags for ext in self.for_replace):
                for replacment_text in self.for_replace:
                    tags = tags.replace(replacment_text, "")
                if len(tags.split(" ")) > 0:
                    return {"tags": tags.split(" ")}
                return False
            return False

class IsTextFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text or False

# class IsBeInDataBaseFilter(BaseFilter):
#     async def __call__(self, message: Message) -> bool:
#         user = Worker(user_id=message.from_user.id)
#         return not await dm.execute_query(user.get_one)
#         pass

# class IsWorker(BaseFilter):
#     def __init__(self, state_required):
#         self.state_required: Union[bool] = state_required
#
#     async def __call__(self, message: Message) -> bool:
#         user = Worker(telegram_id=message.from_user.id)
#         return await dm.execute_query(user.get_one) == self.state_required
#         pass
#
# class WithFullIndividual(BaseFilter):
#     def __init__(self, state_required):
#         self.state_required: Union[bool] = state_required
#
#     async def __call__(self, message: Message) -> bool:
#         user = Worker(telegram_id=message.from_user.id)
#
#         if await dm.execute_query(user.get_one):
#             if user.individual_id is not None:
#                 individual = Individual(id=user.individual_id)
#                 await dm.execute_query(individual.get_one)
#
#                 a = individual.docx_first_page is not None
#                 b = individual.docx_second_page is not None
#
#                 return (((user.individual_id is not None) and a and b)
#                         == self.state_required)
#         return False == self.state_required
#         pass

class WithPhoto(BaseFilter):
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        return message.photo is not None and message.photo[-1].file_id is not None

class IsAdminOrCreator(BaseFilter):
    async def __call__(self, message: Message, bot: Bot) -> bool:
        #or member_status.status in ("creator", "administrator") or message.chat.type == "private"
        #member_status = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return message.from_user.id in c.ADMINS 


