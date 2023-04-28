import os
import openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


# OpenAI API設定
openai.api_key = os.environ["OPENAI_API_KEY"]

# Slack App設定
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

app = App(token=SLACK_BOT_TOKEN)


def polite_japanese(text):
    prompt = f"あなたはとても優秀なassistantです。" \
             f"以下のテキストを丁寧で人を傷つけない言い方に変えてください。" \
             f":\n\n{text}\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
    )
    return response.choices[0].text


@app.event("app_mention")
def handle_message(body, say):
    user_id = body['event']['user']
    text = body['event']['text']
    thread_ts = body['event']['ts']
    channel_id = body['event']['channel']

    # GPT-4による変換
    polite_text = polite_japanese(text)

    # 変換後のテキストをスレッドに投稿
    app.client.chat_postMessage(
        channel=channel_id,
        text=f"<@{user_id}> さんの発言に社会性を付与しますと以下のようになります。:\n```{polite_text}```",
        thread_ts=thread_ts
    )

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
