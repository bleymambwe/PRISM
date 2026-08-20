import {AbsoluteFill} from 'remotion';
import {PermutationRow} from '../components/PermutationRow';
import {palette} from '../theme';

export const PrismThumbnail: React.FC<{variant?: number}> = ({variant = 1}) => (
  <AbsoluteFill style={{backgroundColor: variant === 2 ? palette.paper : palette.ink, color: variant === 2 ? palette.ink : palette.white, padding: 150, fontFamily: 'Arial, Helvetica, sans-serif', justifyContent: 'center'}}>
    <div style={{fontSize: 42, letterSpacing: 8, fontWeight: 900, color: palette.warning}}>THE PAPER, EXPLAINED</div>
    <div style={{fontSize: 156, lineHeight: 0.94, fontWeight: 950, margin: '28px 0 75px', maxWidth: 2600}}>Same components.<br /><span style={{color: palette.positive}}>Different order.</span><br />Different result.</div>
    <PermutationRow compact />
    <div style={{fontSize: 42, marginTop: 82, fontWeight: 700}}>PRISM · Blessings Mambwe · ML Collective</div>
  </AbsoluteFill>
);

