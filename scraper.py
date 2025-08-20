import firebase_admin
from firebase_admin import credentials, firestore
import traceback

# Firebaseの秘密鍵ファイル名
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

print("--- テストスクリプト開始 ---")

try:
    print("1. 秘密鍵ファイルを読み込みます。")
    cred = credentials.Certificate(credentials_file_name)
    print("2. 秘密鍵の読み込み成功。")

    print("3. Firebaseアプリを初期化します。")
    firebase_admin.initialize_app(cred)
    print("4. Firebaseアプリの初期化成功。")

    db = firestore.client()
    print("5. Firestoreクライアントの取得成功。")

    test_doc_ref = db.collection('test_collection').document('test_doc')
    print(f"6. テスト書き込み先: {test_doc_ref.path}")

    test_doc_ref.set({'status': 'ok', 'timestamp': firestore.SERVER_TIMESTAMP})
    print("7. テストデータの書き込み成功！")

except Exception as e:
    print("--- エラー発生 ---")
    # traceback.format_exc() でエラーの詳細を出力
    print(traceback.format_exc())
    exit(1)

print("--- テストスクリプト正常終了 ---")
