import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth # stealthライブラリをインポート
import logging
import traceback
import time

# --- ログ設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 設定項目 ---
STANDINGS_URL = "https://www.premierleague.com/tables"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します（Selenium Stealth版）。")
    
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)

        # ▼▼▼ stealthを設定 ▼▼▼
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        # ▲▲▲ ここまで追加 ▲▲▲
        logging.info("ヘッドレスChromeブラウザをStealthモードで起動しました。")

        driver.get(STANDINGS_URL)
        logging.info(f"公式サイトにアクセスします: {STANDINGS_URL}")

        time.sleep(5) # ページが反応するまで少し待機

        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
            logging.info("Cookieの同意ボタンをクリックしました。")
        except:
            logging.info("Cookieの同意ボタンは見つかりませんでした。")

        time.sleep(5) # クリック後に描画が安定するまで待機

        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tableContainer")))
        logging.info("順位表の表示を確認しました。")

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        standings_table = soup.find('tbody')
        if not standings_table:
            raise ValueError("順位表のtbodyが見つかりませんでした。")

        rows = standings_table.find_all('tr')
        standings = []
        for row in rows:
            if row.has_attr('data-team-id'):
                team_name_span = row.find('span', class_='long')
                if team_name_span:
                    standings.append(team_name_span.text.strip())

        if not standings:
            raise ValueError("HTMLから順位リストを作成できませんでした。")
        logging.info(f"{len(standings)}チームの順位を解析しました。")
        
        # Firebase接続・書き込み (変更なし)
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        doc_ref = db.collection('artifacts/predictionprediction/public/data/actualStandings').document('currentWeek')
        doc_ref.set({'standings': standings, 'lastUpdated': firestore.SERVER_TIMESTAMP})
        logging.info("Firestoreへのデータ書き込みが正常に完了しました。")

    except Exception as e:
        logging.error("スクリプトの実行中にエラーが発生しました。")
        logging.error(traceback.format_exc())
        exit(1)
    
    finally:
        if driver:
            driver.quit()
        logging.info("自動順位更新スクリプトを終了します。")
        logging.info("====================\n")

if __name__ == "__main__":
    main()
