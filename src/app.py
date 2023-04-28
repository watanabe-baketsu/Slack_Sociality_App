import json
from http import HTTPStatus

import boto3
import openai
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler


def get_secret():
    secret_name = "social-skill-develop"
    region_name = "ap-northeast-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response['SecretString']
    except Exception as e:
        raise e


secrets = json.loads(get_secret())
openai.api_key = secrets['openai-api-key']

# Slack App設定
SLACK_APP_TOKEN = secrets['slack-app-token']
SLACK_BOT_TOKEN = secrets['slack-bot-token']
SLACK_SIGNING_SECRET = secrets['slack-signing-secret']

app = App(
    token=SLACK_BOT_TOKEN,
    process_before_response=True,
    signing_secret=SLACK_SIGNING_SECRET,
)


def polite_japanese(text):
    prompt = f"以下の文章を丁寧な言い方に変えてください。出力は修正後の文章のみにしてください。" \
             f":\n\n{text}\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()


@app.event("app_mention")
def handle_message(body, say):
    user_id = body['event']['user']
    text = body['event']['text']
    thread_ts = body['event']['ts']
    channel_id = body['event']['channel']

    polite_text = polite_japanese(text)
    polite_text = polite_text.replace("<@U0559M7LES1> ", "")

    app.client.chat_postMessage(
        channel=channel_id,
        text=f"<@{user_id}> さんの発言に社会性を付与しますと以下のようになります。:\n```{polite_text}```",
        thread_ts=thread_ts
    )


def handler(event, context):
    # リクエストヘッダを確認し、リトライリクエストの場合はLambda関数を終了
    headers = event.get("headers", {})
    if "X-Slack-Retry-Num" in headers:
        return {
            "statusCode": HTTPStatus.OK,
            "body": "Retry request ignored"
        }
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
