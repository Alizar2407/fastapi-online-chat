import requests

from celery import Celery
from celery_app.config import celery_app_settings


TELEGRAM_BOT_TOKEN = celery_app_settings.TELEGRAM_BOT_TOKEN

celery_app = Celery(
    "tasks",
    broker=celery_app_settings.CELERY_BROKER_URL,
    backend=celery_app_settings.CELERY_BROKER_URL,
)


@celery_app.task
def send_telegram_notification(telegram_id: str, sender_name: str, message_text: str):

    get_updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.post(get_updates_url).json()

    if not response["ok"]:
        return

    for update in response["result"]:

        if telegram_id.endswith(update["message"]["chat"]["username"]):

            chat_id = update["message"]["chat"]["id"]

            data = {
                "chat_id": chat_id,
                "text": f"Пользователь {sender_name} отправил вам сообщение:\n{message_text}",
            }

            send_message_url = (
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            )

            try:
                response = requests.post(send_message_url, data=data)
                response.raise_for_status()
                print(f"Notification sent to Telegram user {telegram_id}")

            except requests.exceptions.RequestException as e:
                print(f"Failed to send Telegram notification: {e}")

            break
