import os
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import traceback

# --- ロガー設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 設定項目 ---
API_URL = "https://api.football-data.org/v4/competitions/PL/standings"
FIRESTORE_COLLECTION_PATH = 'artifacts/predictionprediction/public/data/actualStandings'
FIRESTORE_DOCUMENT_ID = 'currentWeek'


def initialize_firebase():
    """Firebase Admin SDKを初期化します。"""
    if firebase_admin._apps:
        return

    # ユーザーが設定した 'FIREBASE_CREDENTIALS' という名前のSecretを環境変数経由で読み込む
    firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    
    if not firebase_creds_json:
        raise ValueError("Firebaseの認証情報が環境変数 'FIREBASE_CREDENTIALS' に設定されていません。")
        
    logging.info("環境変数からFirebase認証情報を読み込みます。")
    creds_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(creds_dict)
    firebase_admin.initialize_app(cred)
    logging.info("Firebaseアプリの初期化が完了しました。")


def fetch_standings_from_api() -> list:
    """Football-Data.org APIから順位表データを取得します。"""
    # ユーザーが設定した 'FOOTBALL_DATA_API_KEY' という名前のSecretを環境変数経由で読み込む
    api_key = os.environ.get('FOOTBALL_DATA_API_KEY')
    if not api_key:
        raise ValueError("APIキーが環境変数 'FOOTBALL_DATA_API_KEY' に設定されていません。")
    
    headers = {'X-Auth-Token': api_key}
    logging.info(f"APIエンドポイントにリクエストを送信します: {API_URL}")
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    logging.info("APIからデータを正常に取得しました。")

    try:
        standings_data = data['standings'][0]['table']
        standings = [row['team']['name'] for row in standings_data]
    except (KeyError, IndexError) as e:
        raise ValueError(f"APIレスポンスの解析に失敗しました。予期せぬ形式の可能性があります。 Error: {e}")

    if not standings:
        raise ValueError("順位リストの作成に失敗しました。")
    
    logging.info(f"{len(standings)}チームの順位を解析しました。")
    return standings


def update_standings_in_firestore(standings: list):
    """取得した順位表をFirestoreに書き込みます。"""
    db = firestore.client()
    doc_ref = db.collection(FIRESTORE_COLLECTION_PATH).document(FIRESTORE_DOCUMENT_ID)
    update_data = {'standings': standings, 'lastUpdated': firestore.SERVER_TIMESTAMP}
    doc_ref.set(update_data)
    logging.info(f"Firestoreへのデータ書き込みが正常に完了しました。")


def main():
    """メインの処理を実行します。"""
    logging.info("====================")
    logging.info("自動順位更新スクリプトを開始します。")

    try:
        initialize_firebase()
        standings_list = fetch_standings_from_api()
        update_standings_in_firestore(standings_list)
    except Exception:
        logging.error("スクリプトの実行中に致命的なエラーが発生しました。")
        logging.error(traceback.format_exc())
        exit(1)
    
    finally:
        logging.info("自動順位更新スクリプトを終了します。")
        logging.info("====================\n")


if __name__ == "__main__":
    main()
