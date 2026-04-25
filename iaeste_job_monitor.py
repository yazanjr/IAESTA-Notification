from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()

EMAIL = os.getenv("IAESTE_EMAIL")
PASSWORD = os.getenv("IAESTE_PASSWORD")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://iaeste.smartsimple.ie/iface/ex/ax_index.jsp?lang=1"
SEEN_FILE = "seen_jobs.json"


def load_seen_jobs():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    return set()


def save_seen_jobs(jobs):
    with open(SEEN_FILE, "w", encoding="utf-8") as file:
        json.dump(list(jobs), file, indent=2)


def extract_jobs(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    jobs = []

    for i, line in enumerate(lines):
        if "-2026-" in line:
            jobs.append({
                "code": line,
                "company": lines[i + 1] if i + 1 < len(lines) else "Unknown",
                "country": lines[i + 2] if i + 2 < len(lines) else "Unknown"
            })

    return jobs


def find_internship_frame(page):
    for attempt in range(10):
        print(f"Looking for internship frame... attempt {attempt + 1}")
        page.wait_for_timeout(3000)

        for frame in page.frames:
            if "ax_content.jsp?linkid=2972" in frame.url:
                print("Internship frame found.")
                return frame

    print("Internship frame not found.")
    print("Available frames:")
    for frame in page.frames:
        print(frame.url)

    return None
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="iaeste_browser_profile",
        headless=True
    )

    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(3000)

    if page.locator("#user").is_visible():
        print("Logging in...")
        page.fill("#user", EMAIL)
        page.fill("#password", PASSWORD)
        page.click('input[type="submit"][value="Login"]')
        page.wait_for_timeout(8000)
    else:
        print("Already logged in.")

    internship_frame = find_internship_frame(page)

    if internship_frame is None:
        browser.close()
        exit()

    seen_jobs = load_seen_jobs()
    current_jobs = set()
    new_jobs = []

    page_number = 1

    while True:
        print(f"Reading page {page_number}...")

        page.wait_for_timeout(2000)

        text = internship_frame.locator("body").inner_text()
        jobs_on_page = extract_jobs(text)

        for job in jobs_on_page:
            code = job["code"]
            current_jobs.add(code)

            if code not in seen_jobs:
                new_jobs.append(job)

        next_button = internship_frame.locator("text=Next").last

        if not next_button.is_visible():
            break

        if next_button.is_disabled():
            break

        button_classes = next_button.get_attribute("class") or ""

        if "disabled" in button_classes.lower():
            break

        next_button.click()
        page_number += 1
        page.wait_for_timeout(3000)

    if new_jobs:
        print("\nNEW INTERNSHIPS FOUND:\n")

        for job in new_jobs:
            message = f"🚀 New IAESTE Internship!\n\n{job['code']}\n{job['company']}\n{job['country']}"
            print(message)
            send_telegram(message)
    else:
        print("\nNo new internships.")

    seen_jobs.update(current_jobs)
    save_seen_jobs(seen_jobs)

    browser.close()