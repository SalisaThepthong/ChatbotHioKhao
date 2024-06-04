from datetime import datetime, time
import requests
import schedule
import time

LINE_ACCESS_TOKEN = "ptzc8iKTFPXD7U7DabfPyjFHK3C1BLJbCCBgsVo6MDZgTcZHhHD5ql5826l/IogX6H/y1h4W2c2XYDnI+x/3iokie0qxIAFqpqoXAW8KvYSVwuQcjdxOgg3pqR08gK28pXdtmDjV9ZU4fnN0/3YY9wdB04t89/1O/w1cDnyilFU="
LINE_API_URL = "https://api.line.me/v2/bot/message/broadcast"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + LINE_ACCESS_TOKEN,
}

payload = {
    "messages": [
        {
            "type": "text",
            "text": "กินไรยางงงลองเรียกใช้งาน หิว ดูสิ!!"
        }
    ]
}

def send_message():
    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    print("Message sent. Response Status Code:", response.status_code)

def schedule_messages():
    schedule.every().day.at("08:00").do(send_message)
    schedule.every().day.at("12:00").do(send_message)
    #schedule.every().day.at("15:00").do(send_message)
    schedule.every().day.at("18:00").do(send_message)

# Schedule messages
schedule_messages()

# Infinite loop to run the scheduler
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping the scheduler.")
