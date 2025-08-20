import os
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import traceback

# --- 設定項目（変更なし） ---
LEAGUE_ID = "39"
SEASON = "2025"
API_URL = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

def main():
    print("--- スクリプト実行開始 ---")

    try:
        # 1. APIキーの読み込み
        api_key = os.environ.get('API_FOOTBALL_KEY')
        if not api_key:
            raise ValueError("APIキーが設定されていません。")
        print("1. APIキー読み込み成功")

        # 2. APIリクエスト
        headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': api_key
        }
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        print("2. APIからのデータ取得成功")

        # 3. データ解析
        if not data.get('response') or not data['response']:
             raise ValueError("APIレスポンスに 'response' が含まれていません。")
        league_data = data['response'][0].get('league')
        if not league_data or not league_data.get('standings') or not league_data['standings']:
            raise ValueError("APIレスポンスに順位表データが含まれていません。")
        standings_data = league_data['standings'][0]
        standings = [team['team']['name'] for team in standings_data]
        if not standings:
            raise ValueError("順位リストの作成に失敗。")
        print("3. データ解析成功")

        # 4. Firebase初期化
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file_name)
            firebase_admin.initialize_app(cred)
        print("4. Firebase初期化成功")

        # 5. Firestoreへの書き込み
        db = firestore.client()
        doc_ref = db.collection('artifacts/predictionprediction/public/data/actualStandings').document('currentWeek')
        doc_ref.set({
            'standings': standings,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        })
        print("5. Firestoreへの書き込み成功")

    except Exception as e:
        # ▼▼▼ エラー出力方法を変更 ▼▼▼
        print("--- エラー発生！詳細を標準エラー出力に書き出します ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        exit(1)
    
    print("--- スクリプト正常終了 ---")

if __name__ == "__main__":
    main()
