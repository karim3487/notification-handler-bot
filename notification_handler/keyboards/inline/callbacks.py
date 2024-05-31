from aiogram.filters.callback_data import CallbackData


class Action(CallbackData, prefix="act"):
    action: str


class SendToWebhook(CallbackData, prefix="wh", sep="$"):
    url: str
