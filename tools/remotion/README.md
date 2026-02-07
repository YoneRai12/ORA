# ORA Remotion Templates

This folder contains a small Remotion project used by ORA's `remotion_create_video` skill.

## Setup
```bash
cd tools/remotion
npm ci
```

## Manual render (example)
```bash
npx remotion compositions src/index.ts
npx remotion render src/index.ts OraTitleCard out.mp4 --codec=h264 --props=props.json --overwrite
```

