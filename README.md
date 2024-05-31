# notification_handler

Бот для уведомлений о новых заданиях в Репке.

Когда приходит запрос на в .env `MAIN_WEBHOOK_ADDRESS` с такими данными:
```json
{
    "id": 1,
    "url": "https://example.com",
    "text": "Появилось новое задание на проверку",
    "status": "free",
    "with_keyboard": false
}
```
где `status` - один из трех статусов (`free`, `occupied`, `done`).
