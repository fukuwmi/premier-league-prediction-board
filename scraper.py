import os
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 設定項目 ---
API_URL = "https://api.football-data.org/v4/competitions/PL/standings"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します（Football-Data.org版）。")

    try:
        api_key = os.environ.get('FOOTBALL_DATA_API_KEY')
        if not api_key:
            raise ValueError("APIキーが設定されていません。")
        
        headers = {'X-Auth-Token': api_key}

        logging.info(f"APIエンドポイントにリクエストを送信します: {API_URL}")
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info("APIからデータを正常に取得しました。")

        if not data.get('standings') or not data['standings'][0].get('table'):
            raise ValueError("APIレスポンスから順位表が見つかりません。")

        standings_data = data['standings'][0]['table']
        standings = [row['team']['name'] for row in standings_data]

        if not standings:
            raise ValueError("順位リストの作成に失敗。")
        logging.info(f"{len(standings)}チームの順位を解析しました。")
        
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
        logging.info("自動順位更新スクリプトを終了します。")
        logging.info("====================\n")

if __name__ == "__main__":
    main()
