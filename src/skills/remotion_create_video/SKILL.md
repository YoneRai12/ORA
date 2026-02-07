# Remotion Create Video

Remotion を使って **短い動画（MP4/WebM/GIF）を生成**し、Discord に送信します。
Discord のファイル上限を超える場合は **30分限定のDLページ** を発行します（自動削除）。

## できること（初期）
- タイトルカード動画（テキストだけ）
- 画像 + キャプション動画（URL画像を背景にして字幕を重ねる）

## 使い方
`remotion_create_video(preset="title_card", title="...", subtitle="...", resolution="1080p", output="mp4")`

## 前提
- Node.js が必要です
- 初回は `tools/remotion` で依存を入れてください:
  - `cd tools/remotion`
  - `npm ci` (または `npm install`)

## 環境変数（任意）
- `ORA_REMOTION_PROJECT_DIR` (default: `tools/remotion`)
- `ORA_REMOTION_ENTRY` (default: `src/index.ts`)
- `ORA_REMOTION_RENDER_TIMEOUT_SEC` (default: `900`)

