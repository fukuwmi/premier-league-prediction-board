import os
import requests
import traceback

print("--- API接続テストを開始します ---")

try:
    # ステップ1：APIキーが読み込めているか確認
    api_key = os.environ.get('API_FOOTBALL_KEY')
    if not api_key:
        print("エラー: APIキーが読み込めませんでした。")
        exit(1)
    
    # キーの一部だけを表示して、正しく読み込めているか確認
    print(f"APIキーを読み込みました (先頭4文字: {api_key[:4]}...)" )

    # ステップ2：APIにリクエストを送信
    LEAGUE_ID = "39"  # プレミアリーグ
    SEASON = "2025"   # 2025-2026シーズン
    API_URL = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"
    
    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': api_key
    }

    print(f"ヘッダー情報を設定し、{API_URL} にリクエストを送信します。")
    response = requests.get(API_URL, headers=headers)
    
    # ステップ3：APIからの応答を確認
    print(f"APIからの応答ステータスコード: {response.status_code}")
    # 応答のテキスト内容をすべて表示
    print("--- APIからの応答内容 ---")
    print(response.text)
    print("--------------------------")

    # もし応答がエラーなら、ここでスクリプトを止める
    response.raise_for_status()

    print("APIテストは正常に完了しました。")

except Exception as e:
    print("--- テスト中にエラーが発生しました ---")
    print(traceback.format_exc())
    exit(1)
