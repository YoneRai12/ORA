# ORA Ecosystem (ORALLM Pro) | ⚡ Universal AI Interface

![ORA Banner](https://img.shields.io/badge/ORA-Universal_AI-7d5bf6?style=for-the-badge&logo=openai)
![Status](https://img.shields.io/badge/Status-Operational-brightgreen?style=for-the-badge&logo=discord)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**ORA** は、単なるDiscord Botではありません。
あなたのPC上で動作し、**視覚（Vision）**、**聴覚（Voice）**、そして **システム制御（Control）** を兼ね備えた、次世代のパーソナルAIアシスタント（Universal Interface）です。
ローカルLLM (LM Studio) と連携し、プライバシーを守りながら「あなただけの最強の秘書」として機能します。

---

## 🌌 Core Architecture (アーキテクチャ)

ORAは3つの要素で構成される「エコシステム」です。

### 1. 🧠 The BRAIN (思考中枢)
*   **Local LLM Integration**: LM Studio (Mistral, LLaMA 3, Qwen) を脳として使用。API代を気にせず無限に思考できます。
*   **Universal Memory (SQLite)**: 会話内容、生成した画像、エラーログを記憶し、継続的な学習を行います。
*   **True Vision**: 画像を直接「見る」能力を持ち、グラフの解析やゲーム画面のアドバイスが可能です。

### 2. 🗣️ The BODY (身体・インターフェース)
*   **Neural Voice**: VoiceVoxエンジンを使用し、遅延を感じさせない自然な日本語で対話します。
*   **Automatic Deafening**: 接続安定化のため、Discord Gatewayに対し適切なステータス管理を行います。
*   **Ear (Whisper)**: あなたの話す言葉をリアルタイムでテキスト化し、聞き取ります。

### 3. 🛡️ The GUARDIAN (システム制御)
*   **Admin Sandbox**: PCの操作権限を持ちながらも、安全なサンドボックス内で動作。
*   **Self-Healing**: 自身のコードにエラーが発生した場合、自律的に修復を試みる「自己修復機能 (Opus Check等)」を搭載。

---

## 🚀 Setup Guide (導入手順)

### 1. 必須要件 (Prerequisites)
*   **OS**: Windows 10 / 11 (推奨)
*   **Python**: 3.11 以上
*   **VoiceVox**: 音声合成に必須。起動してバックグラウンドで動かしておく必要があります。 [ダウンロード](https://voicevox.hiroshiba.jp/)
*   **LM Studio**: AIの脳として必須。 [ダウンロード](https://lmstudio.ai/)
    *   **Server Mode**: Local Serverを開始してください。
    *   推奨モデル: `LLaVA` (Vision対応) または `Mistral-Nemo`

### 2. ⚠️ Critical Dependencies (重要: 手動導入ファイル)

Botが「声」を出すために、以下のファイルが**絶対に必要**です。
（ライセンスの都合上、同梱できないため、必ず手動で入れてください）

1.  **`libopus-0.x64.dll`** をWebからダウンロード。
    *   Google検索: `libopus-0.x64.dll download` (GitHubの `discord-opus` など)
2.  このファイルを、プロジェクトの**ルートフォルダ**（`start_all.bat` がある場所）に配置。

> **Warning**: これがない場合、VC接続時に `Timed out connecting to voice` エラーで切断されます。

### 3. インストール & 起動
Powershell または CMD で以下を実行：

```bash
# 1. ライブラリのインストール
pip install -r requirements.txt

# 2. 起動 (Bot + Web API)
start_all.bat
```

### 4. 環境設定 (.env Configuration)
`.env.example` をコピーして `.env` を作成し、以下を設定してください。

| 変数名 | 説明 | サンプル値 | 必須 |
| :--- | :--- | :--- | :--- |
| `DISCORD_BOT_TOKEN` | Discord Developer Portalで取得したToken | `MTE...` | ✅ |
| `DISCORD_APP_ID` | Application ID | `123456789...` | ✅ |
| `ORA_DEV_GUILD_ID` | スラッシュコマンドを即時反映するサーバーID | `987654321...` | ✅ |
| `LLM_BASE_URL` | LM StudioのURL | `http://127.0.0.1:1234/v1` | ✅ |
| `LLM_MODEL` | 使用するモデル名 (LM Studio上のID) | `mistralai/ministral-3...` |  |
| `VOICEVOX_API_URL` | VoiceVoxのURL | `http://127.0.0.1:50021` | ✅ |
| `VOICEVOX_SPEAKER_ID` | デフォルトの話者ID | `1` (ずんだもん), `2` (メタン) |  |

---

## 🎮 Command Reference (コマンド一覧)

Botは「自然言語」と「スラッシュコマンド」の両方で操作できます。

### 🗣️ Voice & Chat (基本操作)
| コマンド/発言 | 動作 | 詳細 |
| :--- | :--- | :--- |
| `join_voice_channel` / `@ORA 来て` | VCに参加 | 自動的に読み上げを開始します。 |
| `leave_voice_channel` / `@ORA ばいばい` | VCから切断 | 読み上げを終了して退出します。 |
| `speak` (Slash) | 強制発話 | 指定したテキストをBotに喋らせます。 |
| `change_voice` | 声の変更 | 「ずんだもん」「四国めたん」などへ切り替え可能。 |
| `music_play` | 音楽再生 | YouTubeのURLやキーワードで検索して再生します。 |

### 👁️ Vision & Analysis (視覚機能)
| 操作 | 動作 | 詳細 |
| :--- | :--- | :--- |
| **画像を添付**して `これ解いて` | 画像解析 | 数式、グラフ、ゲーム画面、エラーログなどを解析します。 |
| **画像の付いたメッセージに返信** | 過去参照 | 過去の画像メッセージに対して同様に解析を行えます。 |
| `desktop_watch` (Slash) | 画面共有 | (Pro機能) 自分のPC画面をBotに見せ続けます。 |

### 🛠️ System & Admin (管理者機能)
| ツール名 | 動作 | 詳細 |
| :--- | :--- | :--- |
| `get_system_stats` | リソース監視 | CPU, メモリ, **GPU (VRAM)** の使用状況を表示。 |
| `create_channel` | チャンネル作成 | 指定した名前・カテゴリで新しいチャンネルを作成。 |
| `create_file` | ファイル作成 | PC上にテキストファイルを作成 (Sandbox内)。 |
| `google_search` | Google検索 | SerpApiを使用してWeb上の最新情報を取得。 |
| `ping` | 応答速度 | BotのWebSocketレイテンシを確認。 |

---

## ⚠️ Troubleshooting (FAQ)

### Q. VCに入ってこない / 切断される
*   **A.** `libopus-0.x64.dll` がフォルダに入っていますか？一番多い原因です。
*   **A.** VoiceVoxは起動していますか？
*   **A.** Botに「管理者権限」や「接続権限」が付与されていますか？

### Q. 「これ解いて」と言っても変な検索をする / 音楽が流れる
*   **A.** LM Studioでロードしているモデルが「Vision非対応 (Text-only)」の場合、BotはOCRテキストを誤読して検索しようとすることがあります。
    *   **解決策**: `LLaVA` や `Qwen-VL` などのVision対応モデルを使用してください。
    *   **解決策**: プロンプトで「画像が見えない場合は教えて」と指示済みですが、モデルの性能によります。

### Q. 起動時に `ModuleNotFoundError` が出る
*   **A.** `pip install -r requirements.txt` を忘れていませんか？
*   **A.** 仮想環境 (`.venv`) が有効になっていますか？ `start_all.bat` を使えば自動で有効になります。

---

## 📜 Credits & Technology

*   **Language**: Python 3.11, TypeScript (Next.js)
*   **Discord Lib**: `discord.py` (2.3+)
*   **Voice Engine**: [VoiceVox](https://voicevox.hiroshiba.jp/) (Zundamon, Metan, etc.)
*   **Brain**: [LM Studio](https://lmstudio.ai/) (Local LLM Inference)
*   **Search**: Google Custom Search API / SerpApi
*   **Vision**: Google Cloud Vision API (Fallback) / OpenAI Vision Format

---
*Created by YoneRai12 | Powered by ORA Architecture*
