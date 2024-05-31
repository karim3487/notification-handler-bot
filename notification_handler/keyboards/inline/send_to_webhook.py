from aiogram.types import InlineKeyboardMarkup

from notification_handler.keyboards.inline.callbacks import SendToWebhook
from notification_handler.keyboards.inline.consts import InlineConstructor


class YesOrNoKb(InlineConstructor):
    @staticmethod
    def yes_or_no() -> InlineKeyboardMarkup:
        schema = [2]
        actions = [
            {"text": "Yes", "callback_data": SendToWebhook(url="https://9f4e-188-243-133-18.ngrok-free.app/yes")},
            {"text": "No", "callback_data": SendToWebhook(url="https://9f4e-188-243-133-18.ngrok-free.app/no")},
        ]

        return YesOrNoKb._create_kb(actions, schema)
