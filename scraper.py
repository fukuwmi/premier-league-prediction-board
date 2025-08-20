import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import traceback

# --- ログ設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 設定項目 ---
STANDINGS_URL = "https://www.premierleague.com/tables"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します（Selenium版）。")
    
    driver = None
    try:
        # 1. Seleniumでブラウザを起動
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        logging.info("ヘッドレスChromeブラウザを起動しました。")

        # 2. ページにアクセスし、テーブルが表示されるまで待機
        driver.get(STANDINGS_URL)
        logging.info(f"公式サイトにアクセスします: {STANDINGS_URL}")

        # cookieの同意ボタンが表示されたらクリックする処理
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
            logging.info("Cookieの同意ボタンをクリックしました。")
        except:
            logging.info("Cookieの同意ボタンは見つかりませんでした。")

        # 順位表の本体(tbody)が表示されるまで最大20秒待機
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widget='standings-table'] tbody")))
        logging.info("順位表の表示を確認しました。")

        # 3. ページのHTMLを取得して解析
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
        
        # 4. Firebaseに接続・書き込み
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()

        doc_ref = db.collection('artifacts/predictionprediction/public/data/actualStandings').document('currentWeek')
        logging.info(f"Firestoreのドキュメント '{doc_ref.path}' を更新します。")
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
