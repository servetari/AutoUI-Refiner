from playwright.sync_api import sync_playwright
import time

def take_screenshot(url="http://localhost:5173", output_path="screenshot.png"):
    """
    Connects to the given URL using Playwright and takes a screenshot.
    """
    print(f"[*] Connecting to: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            page.goto(url, wait_until="networkidle")
            time.sleep(2)
            page.screenshot(path=output_path, full_page=True)
            print(f"[+] Screenshot successfully saved: {output_path}")
            return True
        except Exception as e:
            print(f"[-] Error occurred (Connection failed): {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    take_screenshot()
