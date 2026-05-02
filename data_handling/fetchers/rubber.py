import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from data_handling.utils.format import format_price
from webdriver_manager.chrome import ChromeDriverManager


RUBBER_SOURCE = "https://rubberboard.gov.in/public?lang=E"


def fetch_rubber_price():
    driver = None
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")

        # Disable images (faster)
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        # Use webdriver_manager with Google Chrome
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(RUBBER_SOURCE)
        wait = WebDriverWait(driver, 20)
        rows = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//table//tr"))
        )

        rubber_row = None
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            cols_text = [c.text.strip() for c in cols]
            if len(cols_text) >= 3 and "RSS4" in cols_text[0]:
                rubber_row = cols_text
                break

        if not rubber_row:
            return _error("RSS4 not found")

        inr_100kg = float(rubber_row[1].replace(",", ""))
        usd_100kg = float(rubber_row[2].replace(",", ""))

        inr_per_kg = inr_100kg / 100
        usd_per_kg = usd_100kg / 100

        formatted_time = datetime.now().strftime("%Y-%m-%d")

        return {
            "commodity": "Natural Rubber (India - RSS4)",
            "price_usd": format_price(usd_per_kg),
            "price_inr": format_price(inr_per_kg),
            "unit": "per kg",
            "last_updated": formatted_time,
            "source": RUBBER_SOURCE
        }

    except TimeoutException:
        return _error("Site timeout")
    except Exception as e:
        return _error(str(e))
    finally:
        if driver:
            driver.quit()


def _error(msg):
    return {
        "commodity": "Natural Rubber (India - RSS4)",
        "price_usd": "N/A",
        "price_inr": "N/A",
        "unit": "",
        "last_updated": f"Failed: {msg}",
        "source": RUBBER_SOURCE
    }
