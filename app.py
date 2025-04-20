# === backend/app.py ===

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from PIL import Image
from io import BytesIO

# Flaskアプリケーション
app = Flask(__name__)

# Gemini APIキーリスト
api_keys = [
    "AIzaSyAx3LfCJ7vOoZseBE5sLFScDk-f6rsrvfY",
    "AIzaSyCwgvF-p92UBBzkQpXNr1DLD0pUWTYrBko",
    "AIzaSyBfjo-pndIY29b2OVfoXvy6bmNCguyC9tQ"
]
current_api_key_index = 0

# 初期設定
genai.configure(api_key=api_keys[current_api_key_index])
text_model = genai.GenerativeModel("models/gemini-2.0-pro-exp-02-05")
vision_model = genai.GenerativeModel("models/gemini-2.0-pro-exp-02-05")

# APIキー切り替え
def switch_api_key():
    global current_api_key_index
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    genai.configure(api_key=api_keys[current_api_key_index])

# 会話履歴を保存
conversation_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")
    uploaded_file = request.files.get("file")

    if not user_message and not uploaded_file:
        return jsonify({"reply": "⚠ メッセージまたは画像を送ってください"})

    if uploaded_file:
        # 画像処理
        try:
            image_data = uploaded_file.read()

            response = vision_model.generate_content([
                { "mime_type": uploaded_file.mimetype, "data": image_data },
                { "text": "この画像について日本語で説明してください。" }
            ])
            reply = response.text if response.text else "⚠ 応答がありませんでした（画像）"
        except Exception as e:
            reply = f"⚠ 画像処理エラー: {str(e)}"

    elif user_message.startswith("!image "):
        # 画像生成
        try:
            prompt = user_message[len("!image "):]
            response = vision_model.generate_content(
                prompt,
                generation_config={"response_mime_type": "image/png"}
            )
            image_data = response._result.candidates[0].content.parts[0].inline_data.data
            # 画像をbase64エンコードして返す（ブラウザで表示できるように）
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            reply = f"data:image/png;base64,{base64_image}"
        except Exception as e:
            reply = f"⚠ 画像生成エラー: {str(e)}"

    else:
        # テキスト処理
        conversation_history.append(f"ユーザー: {user_message}")
        if len(conversation_history) > 5:
            conversation_history.pop(0)

        history_text = "\n".join(conversation_history)
        history_text = "日本語で答えてください: " + history_text

        try:
            response = text_model.generate_content(history_text)
            reply = response.text if response.text else "⚠ 応答がありませんでした（テキスト）"
        except Exception as e:
            reply = f"⚠ エラー: {str(e)}"

        conversation_history.append(f"AI: {reply}")

    switch_api_key()
    return jsonify({"reply": reply[:4000]})


if __name__ == "__main__":
    app.run(debug=True)
