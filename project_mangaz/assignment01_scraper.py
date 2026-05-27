"""
manga_scraper.py
────────────────
從 mangaz.com 自動爬取漫畫頁面並儲存為圖片。

使用方式：
    python manga_scraper.py
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ══════════════════════════════════════════════════════════════
# 設定區（可依需求修改）
# ══════════════════════════════════════════════════════════════

TARGET_URL  = "https://www.mangaz.com/book/detail/157901"
FOLDER_NAME = "漫畫存放處"
WAIT_SECS   = 2    # 翻頁後等待秒數
TIMEOUT     = 10   # WebDriverWait 逾時秒數


# ══════════════════════════════════════════════════════════════
# 函式定義
# ══════════════════════════════════════════════════════════════

def create_folder(folder_name: str) -> None:
    """建立儲存資料夾，已存在則略過。"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"【系統提示】已成功建立新資料夾：{folder_name}")
    else:
        print(f"【系統提示】資料夾 {folder_name} 已存在，圖片將直接存入。")


def build_driver() -> webdriver.Chrome:
    """建立並回傳已設定反偵測的 Chrome WebDriver。"""
    options = Options()

    # 反偵測設定
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/121.0.0.0 Safari/537.36'
    )
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--incognito')
    options.add_argument('--start-maximized')

    driver = webdriver.Chrome(options=options)

    # 進一步隱藏 navigator.webdriver
    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
    )
    return driver


def open_viewer(driver: webdriver.Chrome, url: str) -> None:
    """
    開啟目標頁面，點擊「開始閱讀」按鈕，
    並切換到新開啟的漫畫閱讀視窗。
    """
    driver.get(url)
    print(f"Page Title: {driver.title}")

    # 點擊「開始閱讀」按鈕
    button = driver.find_element(By.CSS_SELECTOR, 'button.open-viewer.book-begin.ga')
    button.click()

    # 切換到最新開啟的視窗
    all_windows = driver.window_handles
    driver.switch_to.window(all_windows[-1])

    # 點擊「すぐに読む」（立即閱讀）連結
    read_now = driver.find_element(By.PARTIAL_LINK_TEXT, 'すぐに読む')
    read_now.click()


def scrape_all_pages(
    driver: webdriver.Chrome,
    folder_name: str,
    timeout: int = TIMEOUT,
    wait_secs: int = WAIT_SECS,
) -> int:
    """
    循環截取每頁可見圖片，直到找不到下一頁按鈕為止。

    Returns:
        total_image_count (int): 共儲存的圖片總數
    """
    wait          = WebDriverWait(driver, timeout)
    total_count   = 0

    while True:

        # ── A：擷取當前頁面可見圖片 ──────────────────────────
        image_elements = driver.find_elements(
            By.CSS_SELECTOR, 'div.page_image img.image'
        )

        for img in image_elements:
            if img.is_displayed():
                file_path = os.path.join(folder_name, f"manga_page_{total_count}.png")
                img.screenshot(file_path)
                print(f"成功擷取並儲存：{file_path}")
                total_count += 1

        # ── B：嘗試點擊下一頁 ────────────────────────────────
        try:
            next_page = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.flip.flip-left'))
            )
            next_page.click()
            print("已點擊下一頁，等待畫面載入...")
            time.sleep(wait_secs)

        except TimeoutException:
            print("【系統提示】找不到下一頁按鈕，已達最後一頁，結束爬取。")
            break

    return total_count


# ══════════════════════════════════════════════════════════════
# 主程式
# ══════════════════════════════════════════════════════════════

def main() -> None:
    create_folder(FOLDER_NAME)

    driver = build_driver()
    try:
        open_viewer(driver, TARGET_URL)
        total = scrape_all_pages(driver, FOLDER_NAME)
        print(f"\n【完成】共儲存 {total} 張圖片至「{FOLDER_NAME}」資料夾。")
    finally:
        driver.quit()
        print("【系統提示】瀏覽器已關閉。")


if __name__ == "__main__":
    main()
