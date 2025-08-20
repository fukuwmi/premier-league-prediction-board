import os
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import traceback

# --- ログ設定 ---
logging.basicConfig(
    filename='premier_league_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# --- 設定項目 ---
# API-Footballから取得したリーグIDとシーズン
LEAGUE_ID = "39"  # プレミアリーグ
SEASON = "2025"   # 2025-2026シーズン
API_URL = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"

# Firebaseの秘密鍵ファイル名（変更不要）
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"
# --- 設定項目ここまで ---

def main():
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します。")

    try:
        # 1. GitHubのシークレットからAPIキーを取得
        api_key = os.environ.get('API_FOOTBALL_KEY')
        if not api_key:
            raise ValueError("APIキーが設定されていません。GitHubのシークレットを確認してください。")
        logging.info("APIキーを正常に読み込みました。")

        headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': api_key
        }

        # 2. APIから順位表データを取得
        logging.info(f"APIエンドポイントにリクエストを送信します: {API_URL}")
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info("APIからデータを正常に取得しました。")

        # 3. 取得したデータから順位リストを作成
        standings_data = data['response'][0]['league']['standings'][0]
        standings = [team['team']['name'] for team in standings_data]
        if not standings:
            raise ValueError("APIレスポンスから順位リストを作成できませんでした。")
        logging.info(f"{len(standings)}チームの順位を解析しました。")
        
        # 4. Firebaseに接続
        logging.info("Firebaseアプリの初期化を確認します。")
        if not firebase_admin._apps:
            # GitHub Actionsの実行環境では、ファイルから直接読み込む
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
            logging.info("Firebaseアプリを初期化しました。")
        
        db = firestore.client()

        # 5. 取得した順位をFirestoreに保存
        doc_ref = db.collection('artifacts/predictionprediction/public/data/actualStandings').document('currentWeek')
        logging.info(f"Firestoreのドキュメント '{doc_ref.path}' を更新します。")
        doc_ref.set({
            'standings': standings,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        })
        logging.info("Firestoreへのデータ書き込みが正常に完了しました。")

    except Exception as e:
        # ★★★この部分がエラー詳細を出力します★★★
        logging.error("スクリプトの実行中にエラーが発生しました。")
        logging.error(traceback.format_exc())
        exit(1)
    
    finally:
        logging.info("自動順位更新スクリプトを終了します。")
        logging.info("====================\n")

if __name__ == "__main__":
    main()
