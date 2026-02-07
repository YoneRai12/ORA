import React from 'react';
import {AbsoluteFill, Img, interpolate, useCurrentFrame} from 'remotion';

export type OraCaptionImageProps = {
  imageUrl: string;
  caption?: string;
  durationSec?: number;
  fps?: number;
};

export const OraCaptionImage: React.FC<OraCaptionImageProps> = ({imageUrl, caption}) => {
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <AbsoluteFill style={{opacity: fade}}>
        {imageUrl ? (
          <Img
            src={imageUrl}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              filter: 'brightness(0.85) saturate(1.1)',
            }}
          />
        ) : (
          <AbsoluteFill style={{background: 'linear-gradient(135deg, #111827, #000)'}} />
        )}
      </AbsoluteFill>

      {/* Caption bar */}
      {caption ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            padding: '42px 60px',
            background: 'linear-gradient(180deg, rgba(0,0,0,0.0), rgba(0,0,0,0.75) 40%, rgba(0,0,0,0.88))',
            color: '#fff',
            fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif',
          }}
        >
          <div
            style={{
              fontSize: 44,
              fontWeight: 700,
              lineHeight: 1.15,
              textShadow: '0 8px 24px rgba(0,0,0,0.55)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {caption}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

