import os
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
import time # スリープ（待機）のためにtimeモジュールをインポート

# --- 設定項目 ---
scraping_target_url = "https://www.skysports.com/premier-league-table"
project_id = "predictionprediction"
# --- 設定項目ここまで ---

def main():
    print("Scraping process started...")
    
    try:
        # --- 【ここから修正】 ---
        # 1. ウェブサイトから順位表を取得 (リトライ機能付き)
        standings = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} of {max_retries} to fetch the webpage...")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                response = requests.get(scraping_target_url, headers=headers, timeout=15) # タイムアウトを15秒に設定
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                team_name_elements = soup.select('table.standing-table__table tbody tr a.standing-table__cell--name-link')

                if not team_name_elements:
                     raise ValueError("Could not find team names on the page. The website structure might have changed.")

                team_name_map = {
                    "Arsenal": "アーセナル", "Aston Villa": "アストン・ヴィラ", "Bournemouth": "ボーンマス",
                    "Brentford": "ブレントフォード", "Brighton": "ブライトン", "Chelsea": "チェルシー",
                    "Crystal Palace": "クリスタル・パレス", "Everton": "エヴァートン", "Fulham": "フラム",
                    "Ipswich": "イプスウィッチ・タウン", "Leicester": "レスター・シティ", "Liverpool": "リヴァプール",
                    "Man City": "マンチェスター・シティ", "Man Utd": "マンチェスター・ユナイテッド",
                    "Newcastle": "ニューカッスル・ユナイテッド", "Nott'm Forest": "ノッティンガム・フォレスト",
                    "Southampton": "サウサンプトン", "Tottenham": "トッテナム",
                    "West Ham": "ウェストハム", "Wolves": "ウルヴァーハンプトン",
                    "Burnley": "バーンリー", "Leeds United": "リーズ・ユナイテッド", "Sunderland": "サンダーランド"
                }

                scraped_standings = []
                for element in team_name_elements:
                    english_name = element.get_text(strip=True)
                    japanese_name = team_name_map.get(english_name)
                    if japanese_name:
                        scraped_standings.append(japanese_name)

                if len(scraped_standings) == 20:
                    standings = scraped_standings
                    print("Successfully scraped standings.")
                    break  # 成功したのでループを抜ける
                else:
                     raise ValueError(f"Expected 20 teams, but found {len(scraped_standings)}.")

            except requests.exceptions.RequestException as e:
                print(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 10 seconds...")
                    time.sleep(10) # 10秒待機
                else:
                    print("Max retries reached. Failing.")
                    raise
        
        if standings is None:
            raise ValueError("Failed to fetch standings after multiple retries.")
        # --- 【ここまで修正】 ---

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
        
        jst = timezone(timedelta(hours=9))
        
        data_to_save = {
            'standings': standings,
            'lastUpdated': datetime.now(jst)
        }
        doc_ref.set(data_to_save)
        
        print("Successfully updated Firestore document 'currentWeek'.")
        print("Scraping process finished.")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()