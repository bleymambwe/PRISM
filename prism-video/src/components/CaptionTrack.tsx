import type {Caption} from '@remotion/captions';
import {Sequence, useCurrentFrame, useVideoConfig} from 'remotion';
import {palette} from '../theme';

const CaptionCue: React.FC<{cue: Caption}> = ({cue}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localMs = (frame / fps) * 1000;
  return (
    <div
      style={{
        position: 'absolute',
        left: 300,
        right: 300,
        bottom: 118,
        display: 'flex',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          maxWidth: 2400,
          color: palette.white,
          backgroundColor: 'rgba(11,23,42,0.92)',
          borderRadius: 18,
          padding: '18px 30px 22px',
          fontSize: 42,
          lineHeight: 1.22,
          fontWeight: 680,
          boxShadow: '0 12px 36px rgba(0,0,0,0.20)',
          borderBottom: `6px solid ${localMs < cue.endMs - cue.startMs ? palette.warning : palette.slate}`,
        }}
      >
        {cue.text.trim()}
      </div>
    </div>
  );
};

export const CaptionTrack: React.FC<{captions: Caption[]; leadFrames: number}> = ({captions, leadFrames}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {captions.map((cue, index) => {
        const from = leadFrames + Math.floor((cue.startMs / 1000) * fps);
        const durationInFrames = Math.max(1, Math.ceil(((cue.endMs - cue.startMs) / 1000) * fps));
        return (
          <Sequence key={`${cue.startMs}-${index}`} from={from} durationInFrames={durationInFrames} layout="none">
            <CaptionCue cue={cue} />
          </Sequence>
        );
      })}
    </>
  );
};

