from playwright.sync_api import sync_playwright

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 800},
    "mobile": {"width": 390, "height": 844},
}


def capture_page(url, screenshots):
    """
    Takes one screenshot per requested viewport and collects browser-side errors.

    screenshots: dict mapping a viewport name from VIEWPORTS to an output path,
                 e.g. {"desktop": "iter/desktop.png", "mobile": "iter/mobile.png"}

    Returns (success, console_errors) where console_errors is a deduplicated
    list of console errors, uncaught page errors, and failed network requests.
    """
    console_errors = []
    print(f"[*] Connecting to: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for name, output_path in screenshots.items():
                page = browser.new_page(viewport=VIEWPORTS[name])
                page.on(
                    "console",
                    lambda msg: console_errors.append(f"[console] {msg.text}")
                    if msg.type == "error"
                    else None,
                )
                page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))
                page.on(
                    "requestfailed",
                    lambda req: console_errors.append(
                        f"[requestfailed] {req.url} ({req.failure})"
                    ),
                )
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                page.screenshot(path=output_path, full_page=True)
                page.close()
                print(f"[+] Screenshot saved ({name}): {output_path}")
            return True, list(dict.fromkeys(console_errors))
        except Exception as e:
            print(f"[-] Error occurred (Connection failed): {e}")
            return False, list(dict.fromkeys(console_errors))
        finally:
            browser.close()


if __name__ == "__main__":
    capture_page(
        "http://127.0.0.1:5173",
        {"desktop": "screenshot_desktop.png", "mobile": "screenshot_mobile.png"},
    )
