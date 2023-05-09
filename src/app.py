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
    prompt_system = "あなたはとても優秀なassistantです。"
    prompt_user = f"以下の発言が、差別的な内容を含む発言であるかどうか判定してください。" \
                  f"差別的な内容を含む発言である場合は「1」を、差別的な内容を含まない発言の場合は「0」を先頭に出力してください。" \
                  f"「1」を出力する場合のみ、丁寧な形に修正後の文章を、「1:修正後の文章」の形で修正後の文章を表示してください。" \
                  f"「0」を出力する場合は修正後の文章は必要ありません。:\n\n「{text}」\n"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
    )

    return response.choices[0].message.content.strip()


@app.event("message")
def handle_message(body, say):
    print(body)
    channel_id = body['event']['channel']
    if 'subtype' not in body['event']:
        user_id = body['event']['user']
        text = body['event']['text']
        thread_ts = body['event']['ts']
    elif body['event']['subtype'] == 'message_changed':
        user_id = body['event']['message']['user']
        text = body['event']['message']['text']
        thread_ts = body['event']['message']['ts']
    else:
        return

    polite_text = polite_japanese(text)
    print(polite_text)
    if "1:" in polite_text:
        polite_text = polite_text.replace("1:", "")
        polite_text = polite_text.replace("<@U0559M7LES1> ", "")

        app.client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}> よ、発言が過激だ。このように言い直すのだ。:\n```{polite_text}```",
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
