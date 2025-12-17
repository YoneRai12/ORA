# Self-Optimizing Discord Bot Architecture Proposal

## 概要
Discordでの対話を通じてユーザーに最適化し続けるAIエージェント。
「オンライン最適化（メモリ）」と「オフライン最適化（学習）」の2つのループを回すことで、即応性と継続的な成長を両立させる。

## アーキテクチャ構成

### 1. Discord Bot (Interface)
*   **Role**: ユーザーとの接点。ログ収集とフィードバックの入り口。
*   **Features**:
    *   `on_message`: ユーザー発言とBot返答を `jsonl` に保存。
    *   `Feedback`: リアクション（👍/👎）や `/good`, `/bad` コマンドで嗜好を記録。

### 2. Memory Store (Online Optimization)
*   **Role**: チャット中の即時適応。重み更新なしで振る舞いを変える。
*   **Components**:
    *   **Short-term**: 直近N会話の要約。
    *   **Long-term**: ユーザーの固定ルール、価値観、禁止事項。
    *   **Retrieval**: Embedding検索で文脈に関連するメモリをプロンプトに注入。

### 3. Inference Server (Execution)
*   **Role**: 高速で安定した推論。
*   **Engine**: vLLM または llama.cpp server (RTX5090活用)。
*   **Mechanism**:
    *   Base Model + LoRA Adapter (Current)。
    *   Adapterの更新を検知してHot Reload。

### 4. Nightly Trainer (Offline Optimization)
*   **Role**: じわじわ賢くなる学習プロセス。
*   **Process**:
    *   **Data Gen**: ログからSFT（会話）とDPO（フィードバック）用データを生成。
    *   **Training**: QLoRAで軽量学習。
    *   **Evaluation**: 回帰テスト（Prompt集）と禁止事項テスト。
    *   **Update**: 合格したら `adapters/next` を `adapters/current` にアトミック差し替え。

### 5. Phoenix Manager (Reliability)
*   **Role**: 学習パイプラインの守護神。
*   **Features**:
    *   Trainerのクラッシュ/ハング検知 & 再起動。
    *   OOM時のパラメータ自動調整（Batch size減など）。
    *   **Shadow Patching**: 学習スクリプトのバグを影武者パッチで修正。
    *   **Safety**: AllowlistをTrainer周りに限定し、暴走を防ぐ。

## 確認事項（設計確定のため）
1.  **VRAM容量**: 32GB / 48GB?
2.  **OS**: Windows / Linux?
3.  **Base Model**: GPT / OSS (Size)?
4.  **Response Time**: 目標秒数?
5.  **Log Scope**: DM含む / Serverのみ?
6.  **Training Freq**: 毎日 / 深夜 / 週1?
7.  **Feedback**: リアクション / コマンド?
