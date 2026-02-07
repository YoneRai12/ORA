import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

export type OraTitleCardProps = {
  title: string;
  subtitle?: string;
  durationSec?: number;
  fps?: number;
};

export const OraTitleCard: React.FC<OraTitleCardProps> = ({title, subtitle}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const y = interpolate(frame, [0, 18], [18, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(circle at 20% 20%, #0ea5e9 0%, #111827 45%, #000 100%)',
        color: '#fff',
        fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif',
      }}
    >
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: 120,
          opacity,
          transform: `translateY(${y}px)`,
        }}
      >
        <div style={{maxWidth: 1400}}>
          <div
            style={{
              fontSize: 96,
              fontWeight: 800,
              letterSpacing: -1.2,
              lineHeight: 1.05,
              textShadow: '0 10px 30px rgba(0,0,0,0.45)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {title}
          </div>
          {subtitle ? (
            <div
              style={{
                marginTop: 28,
                fontSize: 36,
                fontWeight: 500,
                opacity: 0.92,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {subtitle}
            </div>
          ) : null}
          <div
            style={{
              marginTop: 54,
              fontSize: 22,
              opacity: 0.78,
            }}
          >
            ORA Remotion
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

