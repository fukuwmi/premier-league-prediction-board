import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import traceback

# --- ログ設定 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 設定項目 ---
STANDINGS_URL = "https://www.premierleague.com/tables"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します（スクレイピング版）。")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logging.info(f"公式サイトにリクエストを送信します: {STANDINGS_URL}")
        response = requests.get(STANDINGS_URL, headers=headers)
        response.raise_for_status()
        logging.info("HTMLを正常に取得しました。")

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ▼▼▼ スクリーンショットを元に、この部分を正しい検索方法に修正しました ▼▼▼
        # data-widget="standings-table" という目印を持つdiv要素を探す
        standings_widget = soup.find('div', {'data-widget': 'standings-table'})
        if not standings_widget:
            raise ValueError("順位表のウィジェット(data-widget='standings-table')が見つかりませんでした。")

        # そのウィジェットの中にあるtbody（表の本体）を探す
        standings_table = standings_widget.find('tbody')
        # ▲▲▲ ここまで修正 ▲▲▲

        if not standings_table:
            raise ValueError("順位表のtbodyが見つかりませんでした。")

        rows = standings_table.find_all('tr')
        standings = []
        for row in rows:
            # tr要素にdata-team-id属性があるものだけを対象とする
            if row.has_attr('data-team-id'):
                team_name_span = row.find('span', class_='long')
                if team_name_span:
                    standings.append(team_name_span.text.strip())

        if not standings:
            raise ValueError("HTMLから順位リストを作成できませんでした。")
        logging.info(f"{len(standings)}チームの順位を解析しました。")
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()

        doc_ref = db.collection('artifacts/predictionprediction/public/data/actualStandings').document('currentWeek')
        logging.info(f"Firestoreのドキュメント '{doc_ref.path}' を更新します。")
        doc_ref.set({
            'standings': standings,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        })
        logging.info("Firestoreへのデータ書き込みが正常に完了しました。")

    except Exception as e:
        logging.error("スクリプトの実行中にエラーが発生しました。")
        logging.error(traceback.format_exc())
        exit(1)
    
    finally:
        logging.info("自動順位更新スクリプトを終了します。")
        logging.info("====================\n")

if __name__ == "__main__":
    main()
