import {Audio} from '@remotion/media';
import {AbsoluteFill, Easing, Interactive, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {CaptionTrack} from '../components/CaptionTrack';
import {CitationFooter} from '../components/CitationFooter';
import {MiniChart} from '../components/MiniChart';
import {PermutationRow} from '../components/PermutationRow';
import {StatusBadge} from '../components/StatusBadge';
import {palette, statusColor} from '../theme';
import type {PrismScene} from '../types';

const LEAD_FRAMES = 12;

const Visual: React.FC<{scene: PrismScene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (scene.visual === 'cards' || scene.visual === 'mutation') {
    return <PermutationRow cards={scene.visual === 'mutation' ? ['SWAP', 'INSERT', 'INVERT', 'SCRAMBLE', 'PORTFOLIO', 'ADAPT'] : undefined} compact />;
  }
  if (scene.visual === 'algorithm') {
    const labels = ['sample', 'decode', 'evaluate', 'select', 'mutate', 'replace'];
    return <div style={{display: 'flex', alignItems: 'center', gap: 24}}>{labels.map((label, index) => <div key={label} style={{display: 'flex', alignItems: 'center', gap: 24}}><div style={{width: 300, height: 170, borderRadius: 28, border: `5px solid ${index === 4 ? palette.theory : palette.primary}`, backgroundColor: '#FFFFFF', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: 38, fontWeight: 800, opacity: interpolate(frame, [index * 9, index * 9 + 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}), scale: spring({frame: frame - index * 9, fps, config: {damping: 18}})}}>{label}</div>{index < labels.length - 1 ? <div style={{fontSize: 52, color: palette.slate}}>→</div> : null}</div>)}</div>;
  }
  if (scene.visual === 'theory') {
    return <div style={{display: 'flex', alignItems: 'center', gap: 110}}><div style={{width: 550, height: 300, border: `6px dashed ${palette.theory}`, borderRadius: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 45, fontWeight: 800, color: palette.theory}}>transient states</div><div style={{fontSize: 90, color: palette.slate}}>→</div><div style={{width: 550, height: 300, border: `8px double ${palette.positive}`, borderRadius: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 45, fontWeight: 850, color: palette.positive}}>optimum retained</div></div>;
  }
  if (scene.visual === 'protocol') {
    return <div style={{display: 'flex', gap: 24}}>{['variance', 'resolution', 'locality', 'method', 'verify'].map((label, index) => <div key={label} style={{width: 370, height: 250, borderRadius: 26, backgroundColor: index === 3 ? palette.warning : palette.primary, color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', fontSize: 43, fontWeight: 850, opacity: interpolate(frame, [index * 8, index * 8 + 14], [0.2, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>{index + 1}<br />{label}</div>)}</div>;
  }
  if (scene.visual === 'correction') {
    return <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center'}}><div style={{fontSize: 67, fontWeight: 850, color: palette.negative, textDecoration: 'line-through', textDecorationThickness: 9}}>earlier headline</div><div style={{fontSize: 74, fontWeight: 900, color: palette.positive}}>audited conclusion</div></div>;
  }
  if (scene.visual === 'supernet') {
    return <PermutationRow cards={['LINEAR', 'DEEP MLP', 'TANH', 'SIGMOID', 'MEDIUM MLP']} compact />;
  }
  if (scene.visual === 'table') {
    return <div style={{width: 2200, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', border: `5px solid ${palette.primary}`, borderRadius: 28, overflow: 'hidden'}}>{['question', 'evidence', 'decision', scene.sampleSize, scene.finding, scene.downstreamDecision].map((cell, index) => <div key={index} style={{minHeight: 150, padding: 32, fontSize: index < 3 ? 35 : 31, fontWeight: index < 3 ? 900 : 650, color: index < 3 ? '#FFFFFF' : palette.ink, backgroundColor: index < 3 ? palette.primary : index % 2 ? '#FFFFFF' : '#EEF1F5', borderRight: `2px solid ${palette.slate}`, display: 'flex', alignItems: 'center'}}>{cell}</div>)}</div>;
  }
  return <MiniChart graphId={scene.graphId} />;
};

export const DocumentaryScene: React.FC<{scene: PrismScene; audioDurationInFrames: number; captions: PrismScene['captionCues']}> = ({scene, audioDurationInFrames, captions}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  const dark = scene.visual === 'cards' || scene.visual === 'conclusion';
  return (
    <AbsoluteFill style={{width: 3840, height: 2160, scale: width / 3840, transformOrigin: 'top left', backgroundColor: dark ? palette.ink : palette.paper, fontFamily: 'Arial, Helvetica, sans-serif', color: dark ? palette.white : palette.ink, overflow: 'hidden'}}>
      <div style={{position: 'absolute', width: 1200, height: 1200, borderRadius: 600, right: -300, top: -500, backgroundColor: statusColor[scene.claimStatus], opacity: 0.08}} />
      <Interactive.Div name="Scene title" style={{position: 'absolute', left: 110, right: 110, top: 76, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', opacity: interpolate(frame, [0, 18, durationInFrames - 18, durationInFrames - 1], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)})}}>
        <div>
          <div style={{fontSize: 26, letterSpacing: 4, textTransform: 'uppercase', fontWeight: 850, color: dark ? '#AFC6DF' : palette.primary}}>{scene.chapter} · {scene.chapterTitle}</div>
          <div style={{fontSize: 78, lineHeight: 1.05, fontWeight: 900, marginTop: 18, maxWidth: 2700}}>{scene.title}</div>
        </div>
        <StatusBadge status={scene.claimStatus} />
      </Interactive.Div>
      <div style={{position: 'absolute', left: 110, right: 110, top: 330, bottom: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', scale: interpolate(frame, [0, 18], [0.965, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)})}}>
        <Visual scene={scene} />
      </div>
      {scene.equations?.length ? <div style={{position: 'absolute', left: 140, right: 140, bottom: 292, display: 'flex', justifyContent: 'center', fontFamily: 'Georgia, Times New Roman, serif', fontSize: 48, color: dark ? '#FFFFFF' : palette.theory}}>{scene.equations[0].displayText}</div> : null}
      <div style={{position: 'absolute', left: 110, right: 110, bottom: 210, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24}}>
        <div style={{borderLeft: `10px solid ${statusColor[scene.claimStatus]}`, padding: '12px 22px', backgroundColor: dark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.74)', borderRadius: 12, fontSize: 26}}><strong>Finding</strong> · {scene.finding}</div>
        <div style={{borderLeft: `10px solid ${palette.slate}`, padding: '12px 22px', backgroundColor: dark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.74)', borderRadius: 12, fontSize: 26}}><strong>Limitation</strong> · {scene.limitation}</div>
      </div>
      <Sequence from={LEAD_FRAMES} durationInFrames={audioDurationInFrames} layout="none">
        <Audio src={staticFile(scene.audio)} />
      </Sequence>
      <CaptionTrack captions={captions} leadFrames={LEAD_FRAMES} />
      <CitationFooter source={scene.source} graphId={scene.graphId} chapter={`${scene.chapter} · ${scene.id}`} />
    </AbsoluteFill>
  );
};
