# OpenAI Usage & Policy (ORA System)

## 1. 共有無料枠 (Daily Free Allowance)
OpenAI と共有されるトラフィックを毎日無料でご利用いただけます。

### 🚀 High Intel Lane (100万トークン/日)
以下のモデルは、全体で 1 日あたり最大 **100 万トークン** まで無料です。
- `gpt-5.1`
- `gpt-5.1-codex`
- `gpt-5`
- `gpt-5-codex`
- `gpt-5-chat-latest`
- `gpt-4.1`
- `gpt-4o`
- `o1`
- `o3`

### ⚡ Stable/Mini Lane (1000万トークン/日)
以下のモデルは、全体で 1 日あたり最大 **1000 万トークン** まで無料です。
- `gpt-5.1-codex-mini`
- `gpt-5-mini`
- `gpt-5-nano`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `gpt-4o-mini`
- `o1-mini`
- `o3-mini`
- `o4-mini`
- `codex-mini-latest`

## 2. 制限事項 (Critical Constraints)
- **温度 (Temperature) の禁止**: 
  `gpt-5` シリーズ、`o1`、`o3` などの推論/次世代モデルに対して **`temperature` パラメータを送信してはいけません**。送信すると API エラーが発生します。
- **超過料金**: 
  上記の制限を超える使用量、および他のモデル（Legacy等）の使用については、標準料金が請求されます。

## 3. API 設定
- 本システムは `OPENAI_API_KEY` を優先的に使用します。
- ローカルモデルが動作していない場合、または特定のキーワードを検知した場合、自動的に上記のクラウドモデルへルーティングされます。
