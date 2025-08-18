import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import time

# --- 設定項目 ---
# Sky Sportsが内部的に使用しているデータAPIのURLに変更
api_url = "https://footballapi.skysports.com/api/v1/competitions/1/seasons/2024/tables"
project_id = "predictionprediction"
# --- 設定項目ここまで ---

def main():
    print("Process started to fetch data from API...")
    
    try:
        # 1. APIから順位表データを取得 (リトライ機能付き)
        standings = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} of {max_retries} to fetch API data...")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_for_status() # HTTPエラーがあればここで例外を発生させる
                
                # 取得したデータをJSON形式として解析
                data = response.json()
                
                # JSONデータの中から順位表のリストを取得
                table_rows = data.get('tables', [{}])[0].get('rows', [])

                if not table_rows:
                     raise ValueError("Could not find standings data in the API response.")

                team_name_map = {
                    "Arsenal": "アーセナル", "Aston Villa": "アストン・ヴィラ", "Bournemouth": "ボーンマス",
                    "Brentford": "ブレントフォード", "Brighton & Hove Albion": "ブライトン", # APIではフルネーム
                    "Chelsea": "チェルシー", "Crystal Palace": "クリスタル・パレス", "Everton": "エヴァートン", 
                    "Fulham": "フラム", "Ipswich Town": "イプスウィッチ・タウン", "Leicester City": "レスター・シティ", 
                    "Liverpool": "リヴァプール", "Manchester City": "マンチェスター・シティ", "Manchester United": "マンチェスター・ユナイテッド",
                    "Newcastle United": "ニューカッスル・ユナイテッド", "Nottingham Forest": "ノッティンガム・フォレスト",
                    "Southampton": "サウサンプトン", "Tottenham Hotspur": "トッテナム",
                    "West Ham United": "ウェストハム", "Wolverhampton Wanderers": "ウルヴァーハンプトン",
                    "Burnley": "バーンリー", "Leeds United": "リーズ・ユナイテッド", "Sunderland": "サンダーランド"
                }

                scraped_standings = []
                # position（順位）でソート
                sorted_rows = sorted(table_rows, key=lambda x: x.get('position', 99))

                for row in sorted_rows:
                    english_name = row.get('team', {}).get('name', '').strip()
                    japanese_name = team_name_map.get(english_name)
                    if japanese_name:
                        scraped_standings.append(japanese_name)

                if len(scraped_standings) == 20:
                    standings = scraped_standings
                    print("Successfully parsed standings from API.")
                    break
                else:
                     raise ValueError(f"Expected 20 teams, but parsed {len(scraped_standings)}.")

            except requests.exceptions.RequestException as e:
                print(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 15 seconds...")
                    time.sleep(15)
                else:
                    print("Max retries reached. Failing.")
                    raise
        
        if standings is None:
            raise ValueError("Failed to fetch standings after multiple retries.")

        for i, team in enumerate(standings):
            print(f"{i+1}: {team}")

        # 2. Firebaseに接続
        firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS')
        if not firebase_credentials_json:
            raise ValueError("FIREBASE_CREDENTIALS secret not found.")
        
        cred_dict = json.loads(firebase_credentials_json)
        cred = credentials.Certificate(cred_dict)
        
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()

        # 3. 取得した順位をFirestoreに保存
        doc_ref = db.collection('artifacts').document(project_id).collection('public').document('data').collection('actualStandings').document('currentWeek')
        
        jst = timezone(timezone(timedelta(hours=9))
        
        data_to_save = {
            'standings': standings,
            'lastUpdated': datetime.now(jst)
        }
        doc_ref.set(data_to_save)
        
        print("Successfully updated Firestore document 'currentWeek'.")
        print("Process finished.")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()