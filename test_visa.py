from playwright.sync_api import sync_playwright, Page
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")

def go_to_calendar(page: Page):
    """Fill form and navigate to calendar page"""
    page.goto("https://pieraksts.mfa.gov.lv/ru/uzbekistan/index", timeout=20000)

    page.get_by_label("Имя").fill("Jasur")
    page.get_by_label("Фамилия").fill("Juraev")
    page.get_by_label("Э-почта").fill("jasurjuraev.lv@gmail.com")
    page.get_by_label("E-pasts atkārtoti").fill("jasurjuraev.lv@gmail.com")
    page.get_by_label("Номер телефона (с кодом страны, например +371...)").fill("+37123456789")
    page.get_by_role("button", name="Следующий шаг").click()

    page.get_by_text("Выбрать услугу").click()
    option = page.locator("label[for='Persons-0-227']")
    option.wait_for(state="visible", timeout=5000)
    option.click()
    page.locator("label[for='active-confirmation']").click()
    page.get_by_role("button", name="Добавить").click()
    page.get_by_role("button", name="Следующий шаг").click()

    page.locator("#calendar-daygrid").wait_for(state="visible", timeout=10000)
    print("✅ Reached calendar page")

def check_calendar(page: Page):
    page.reload()
    time.sleep(2)

    if "/step3" not in page.url:
        raise Exception("Session expired → redirected back to index page")

    if "Šobrīd visi pieejamie laiki ir aizņemti" in page.content():
        print("❌ No slots available")
    else:
        print("✅ Slots available!")
        send_telegram_message("✅ Slots available for appointment!")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        page = browser.new_page()

        while True:
            try:
                if "/step3" not in page.url:
                    go_to_calendar(page)

                check_calendar(page)

            except Exception as e:
                print(f"⚠️ {e}")
                print("🔄 Restarting flow...")

                try:
                    go_to_calendar(page)
                except Exception as e2:
                    print(f"❌ Failed to reload form: {e2}")
                    time.sleep(5)
