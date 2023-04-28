# Slack_Sociality_App
Slackのカスタムアプリケーションとして動作する社会性育成プログラム。
@メンションをつけてアプリケーションに対して発言した内容を丁寧な日本語にしてスレッドに返信する。

## 技術スタック
AWS SAM + Python + OpenAI API

## デプロイ構成
API Gateway + Lambda + Secrets Manager

## Build & Deploy
```bash
sam build
sam deploy --guided --capabilities CAPABILITY_NAMED_IAM
```

## Secrets Manager
```json
{
  'slack-app-token': 'xoxb-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx',
  'slack-bot-token': 'xoxb-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx',
  'slack-signing-secret': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  'openai-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
}
```