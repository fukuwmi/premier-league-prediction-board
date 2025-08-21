import firebase_admin
from firebase_admin import credentials, firestore
import sys
import traceback

# Firebaseの秘密鍵ファイル名
credentials_file_name = "predictionprediction-firebase-adminsdk-fbsvc-e801e9cb8b.json"

print("--- Firebase接続テストを開始します ---")

try:
    print("1. 秘密鍵ファイルを読み込みます。")
    cred = credentials.Certificate(credentials_file_name)
    print("2. 秘密鍵の読み込みに成功しました。")

    print("3. Firebaseアプリを初期化します。")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    print("4. Firebaseアプリの初期化に成功しました。")

    db = firestore.client()
    print("5. Firestoreクライアントの取得に成功しました。")

    test_doc_ref = db.collection('test_collection').document('test_doc')
    print(f"6. テストデータを書き込みます: {test_doc_ref.path}")

    test_doc_ref.set({'status': 'ok', 'timestamp': firestore.SERVER_TIMESTAMP})
    print("7. テストデータの書き込みに成功しました！")

except Exception as e:
    print("--- エラーが発生しました ---", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    exit(1)

print("--- Firebase接続テストは正常に完了しました ---")
