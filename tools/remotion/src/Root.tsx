import React from 'react';
import {Composition} from 'remotion';
import {OraCaptionImage} from './compositions/OraCaptionImage';
import {OraTitleCard} from './compositions/OraTitleCard';

type BaseProps = {
  durationSec?: number;
  fps?: number;
};

const calcDuration = (props: BaseProps) => {
  const fps = typeof props.fps === 'number' && props.fps > 0 && props.fps <= 120 ? props.fps : 30;
  const durationSec =
    typeof props.durationSec === 'number' && props.durationSec > 0 && props.durationSec <= 120 ? props.durationSec : 6;
  const durationInFrames = Math.max(1, Math.round(durationSec * fps));
  return {fps, durationInFrames};
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="OraTitleCard"
        component={OraTitleCard}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: 'ORA',
          subtitle: '',
          durationSec: 6,
          fps: 30,
        }}
        calculateMetadata={({props}) => {
          const {fps, durationInFrames} = calcDuration(props as BaseProps);
          return {fps, durationInFrames};
        }}
      />
      <Composition
        id="OraCaptionImage"
        component={OraCaptionImage}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          imageUrl: '',
          caption: '',
          durationSec: 6,
          fps: 30,
        }}
        calculateMetadata={({props}) => {
          const {fps, durationInFrames} = calcDuration(props as BaseProps);
          return {fps, durationInFrames};
        }}
      />
    </>
  );
};

