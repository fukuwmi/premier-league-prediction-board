import os
import requests
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
LEAGUE_ID = "39"
SEASON = "2025"
API_URL = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します。")

    try:
        api_key = os.environ.get('API_FOOTBALL_KEY')
        if not api_key:
            raise ValueError("APIキーが設定されていません。")
        logging.info("APIキーを正常に読み込みました。")

        headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': api_key
        }

        logging.info(f"APIエンドポイントにリクエストを送信します: {API_URL}")
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info("APIからデータを正常に取得しました。")

        # ▼▼▼ データ構造のチェックを強化 ▼▼▼
        if not data.get('response') or not data['response']:
             raise ValueError("APIレスポンスに 'response' が含まれていないか、空です。")
        
        league_data = data['response'][0].get('league')
        if not league_data or not league_data.get('standings') or not league_data['standings']:
            raise ValueError("APIレスポンスに順位表データが含まれていません。")

        standings_data = league_data['standings'][0]
        standings = [team['team']['name'] for team in standings_data]
        # ▲▲▲ ここまで修正 ▲▲▲

        if not standings:
            raise ValueError("APIレスポンスから順位リストを作成できませんでした。")
        logging.info(f"{len(standings)}チームの順位を解析しました。")
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
            logging.info("Firebaseアプリを初期化しました。")
        
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
