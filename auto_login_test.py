from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("IAESTE_EMAIL")
PASSWORD = os.getenv("IAESTE_PASSWORD")

URL = "https://iaeste.smartsimple.ie/iface/ex/ax_index.jsp?lang=1"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="iaeste_browser_profile",
        headless=True
    )

    page = browser.new_page()
    page.goto(URL)

    page.wait_for_timeout(3000)

    if page.locator("#user").is_visible():
        print("Login page detected. Logging in...")

        page.fill("#user", EMAIL)
        page.fill("#password", PASSWORD)
        page.wait_for_timeout(1000)
        page.press("#password", "Enter")

        page.wait_for_timeout(8000)
    else:
        print("Already logged in or login page not visible.")

    print("Current title:", page.title())
    print("Current URL:", page.url)

    input("Press ENTER to close browser...")
    browser.close()