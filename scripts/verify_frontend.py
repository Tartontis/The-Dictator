from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Open the local HTML file
        cwd = os.getcwd()
        page.goto(f"file://{cwd}/frontend/index.html")

        # Wait for potential API calls to settle (config loading)
        page.wait_for_timeout(2000)

        # Take screenshot
        os.makedirs("/home/jules/verification", exist_ok=True)
        page.screenshot(path="/home/jules/verification/frontend_polish.png")

        browser.close()

if __name__ == "__main__":
    run()
