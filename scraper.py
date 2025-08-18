import os
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta

# --- 設定項目 ---
scraping_target_url = "https://www.bbc.com/sport/football/premier-league/table"
project_id = "predictionprediction"
# --- 設定項目ここまで ---

def main():
    print("Scraping process started...")
    
    try:
        # 1. ウェブサイトから順位表を取得
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(scraping_target_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 【ここから修正】 ---
        # BBC Sportの新しいHTML構造に対応したCSSセレクタに変更
        # チーム名が含まれるspan要素をより確実に捉える
        team_name_elements = soup.select('table[class*="Table"] tbody tr td:nth-of-type(3) span[title]')
        # --- 【ここまで修正】 ---

        if not team_name_elements:
             raise ValueError("Could not find team names on the page. The website structure might have changed.")

        team_name_map = {
            "Arsenal": "アーセナル", "Aston Villa": "アストン・ヴィラ", "Bournemouth": "ボーンマス",
            "Brentford": "ブレントフォード", "Brighton and Hove Albion": "ブライトン", "Chelsea": "チェルシー",
            "Crystal Palace": "クリスタル・パレス", "Everton": "エヴァートン", "Fulham": "フラム",
            "Ipswich Town": "イプスウィッチ・タウン", "Leicester City": "レスター・シティ", "Liverpool": "リヴァプール",
            "Manchester City": "マンチェスター・シティ", "Manchester United": "マンチェスター・ユナイテッド",
            "Newcastle United": "ニューカッスル・ユナイテッド", "Nottingham Forest": "ノッティンガム・フォレスト",
            "Southampton": "サウサンプトン", "Tottenham Hotspur": "トッテナム",
            "West Ham United": "ウェストハム", "Wolverhampton Wanderers": "ウルヴァーハンプトン",
            "Burnley": "バーンリー", "Leeds United": "リーズ・ユナイテッド", "Sunderland": "サンダーランド"
        }

        standings = []
        for element in team_name_elements:
            # title属性からチーム名を取得するように変更
            english_name = element.get('title', '').strip()
            japanese_name = team_name_map.get(english_name)
            if japanese_name:
                standings.append(japanese_name)

        if len(standings) != 20:
            raise ValueError(f"Expected 20 teams, but found {len(standings)}. Data might be incomplete.")

        print("Successfully scraped standings:")
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