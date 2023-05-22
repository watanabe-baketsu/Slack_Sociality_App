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
    prompt_system = "Please operate as a Japanese speech modification program. " \
                    "Determine whether the user's speech contains discriminatory content. " \
                    "If the speech contains discriminatory content, output '1' at the beginning, " \
                    "and if it does not contain discriminatory content, output '0'. If you output '1', " \
                    "please display the modified sentence in a polite form as '1: Modified sentence'. " \
                    "If you output '0', a modified sentence is not necessary." \
                    "Output the 'Modified sentence' part in Japanese."
    prompt_user = text
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
    )

    return response.choices[0].message.content.strip()


def kyotoben_transformer(text):
    prompt_user = f"以下の発言を皮肉っぽい、相手を煽るような京都弁に変換してください。" \
                  f"ただし、元の発言の反対の意味の形容を用いた皮肉を含めてください。煽りも忘れないでください。\n「{text}」"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
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
            text=f"<@{user_id}> さん、発言が不適切です。以下のように言い直してください。:\n```{polite_text}```",
            thread_ts=thread_ts
        )


@app.event("app_mention")
def handle_app_mention(body, say):
    print(body)
    channel_id = body['event']['channel']
    user_id = body['event']['user']
    text = body['event']['text']
    thread_ts = body['event']['ts']

    kyotoben_text = kyotoben_transformer(text)
    print(kyotoben_text)
    kyotoben_text = kyotoben_text.replace("<@U0559M7LES1> ", "")
    app.client.chat_postMessage(
        channel=channel_id,
        text=f"<@{user_id}> 京都弁transformerの結果です。:\n```{kyotoben_text}```",
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
