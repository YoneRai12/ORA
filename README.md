# ORA Ecosystem (ORALLM Pro) | ⚡ Universal AI Interface

![ORA Banner](https://img.shields.io/badge/ORA-Universal_AI-7d5bf6?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Operational-brightgreen?style=for-the-badge&logo=discord)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)

**ORA** は、単なるDiscord Botではありません。
あなたのPC上で動作し、**視覚（Vision）**、**聴覚（Voice）**、そして **システム制御（Control）** を兼ね備えた、次世代のパーソナルAIアシスタント（Universal Interface）です。

ローカルLLM (LM Studio) と連携し、プライバシーを守りながら「あなただけの最強の秘書」として機能します。

---

## 🌌 Core Architecture (アーキテクチャ)

ORAは3つの要素で構成される「エコシステム」です。

### 1. 🧠 The BRAIN (思考中枢)
*   **Local LLM Integration**: LM Studio (Mistral, LLaMA 3, Qwen) を脳として使用。
*   **Universal Memory**: 会話内容、生成した画像、エラーログを記憶し、継続的な学習を行います。
*   **True Vision**: 画像を直接「見る」能力を持ち、グラフの解析やゲーム画面のアドバイスが可能です。

### 2. 🗣️ The BODY (身体・インターフェース)
*   **Neural Voice**: VoiceVoxエンジンを使用し、遅延を感じさせない自然な日本語で対話します。
*   **Automatic Deafening**: 接続安定化のため、Discord Gatewayに対し適切なステータス管理を行います。
*   **Ear (Whisper)**: あなたの話す言葉をリアルタイムでテキスト化し、聞き取ります。

### 3. 🛡️ The GUARDIAN (システム制御)
*   **Admin Sandbox**: PCの操作権限を持ちながらも、安全なサンドボックス内で動作。
*   **Self-Healing**: 自身のコードにエラーが発生した場合、自律的に修復を試みる「自己修復機能」を搭載。

---

## 🚀 Setup Guide (導入手順)

### 1. 必須要件
*   **OS**: Windows 10 / 11
*   **Python**: 3.11 以上
*   **VoiceVox**: 音声合成に必須 [ダウンロード](https://voicevox.hiroshiba.jp/)
*   **LM Studio**: AIの脳として必須 [ダウンロード](https://lmstudio.ai/)
    *   推奨モデル: `LLaVA` (Vision対応) または `Mistral-Nemo`

### 2. ⚠️ Critical Dependencies (重要: 手動導入ファイル)

Botが「声」を出すために、以下のファイルが**絶対に必要**です。
（ライセンスの都合上、同梱できないため、必ず手動で入れてください）

1.  **`libopus-0.x64.dll`** をWebからダウンロード。
    *   検索: `libopus-0.x64.dll download` (GitHubの `discord-opus` など)
2.  このファイルを、プロジェクトの**ルートフォルダ**（`start_all.bat` がある場所）に配置。

> **Note**: これがない場合、VC接続時に `Timed out` エラーで切断されます。

### 3. インストール
Powershell または CMD で以下を実行：
```bash
pip install -r requirements.txt
```

### 4. 環境設定 (.env)
`.env.example` をコピーして `.env` を作成し、以下を設定してください。

| 変数名 | 説明 | 必須 |
| :--- | :--- | :--- |
| `DISCORD_BOT_TOKEN` | Discord Developer Portalで取得したToken | ✅ |
| `DISCORD_APP_ID` | Application ID | ✅ |
| `ORA_DEV_GUILD_ID` | デバッグ用サーバーID | ✅ |
| `LLM_BASE_URL` | LM StudioのURL (通常 `http://127.0.0.1:1234/v1`) | ✅ |
| `VOICEVOX_API_URL` | VoiceVoxのURL (通常 `http://127.0.0.1:50021`) | ✅ |

---

## 🎮 Command Reference (コマンド一覧)

### 🗣️ Voice & Chat (基本操作)
| コマンド/発言 | 動作 |
| :--- | :--- |
| `join_voice_channel` / `@ORA 来て` | ボイスチャンネルに参加し、読み上げを開始します。 |
| `leave_voice_channel` / `@ORA ばいばい` | ボイスチャンネルから切断します。 |
| `speak` (Slash) | 指定したテキストを強制的に読み上げさせます。 |
| `change_voice` | 声のキャラクターを変更します（ずんだもん、メタンなど）。 |

### 👁️ Vision & Analysis (視覚機能)
| 操作 | 動作 |
| :--- | :--- |
| **画像を添付**して `これ解いて` | 画像を解析し、問題を解きます (Vision API v2)。 |
| **画像の付いたメッセージに返信** | 過去の画像を参照して解析します。 |

### 🛠️ System & Tools (管理者機能)
| ツール名 | 動作 |
| :--- | :--- |
| `get_system_stats` | CPU, メモリ, **GPU (VRAM)** の使用状況を表示します。 |
| `create_channel` | 指定した名前でチャンネルを作成します (Admin限定)。 |
| `create_file` | PC上にテキストファイルを作成します。 |
| `google_search` | Google検索を行い、最新情報を取得します (SerpApi必要)。 |

---

## ⚠️ Troubleshooting (トラブルシューティング)

### Q. VCに入ってこない / 切断される
*   **A.** `libopus-0.x64.dll` がフォルダに入っていますか？
*   **A.** `check_voicevox_status.py` を実行して、VoiceVoxが起動しているか確認してください。

### Q. 「これ解いて」と言っても変な検索をする
*   **A.** LM Studioでロードしているモデルが「Vision非対応 (Text-only)」の可能性があります。
*   **A.** `LLaVA` などの画像対応モデルを使用するか、OCR結果の手動入力が必要です。

---

## 📜 Credits

*   **Core**: Python, Discord.py
*   **Voice**: [VoiceVox](https://voicevox.hiroshiba.jp/) (Zundamon, Metan, etc.)
*   **Brain**: [LM Studio](https://lmstudio.ai/) (Local LLM Inference)
*   **Search**: Google Custom Search API / SerpApi

---
*Created by YoneRai12 | Powered by ORA Architecture*
