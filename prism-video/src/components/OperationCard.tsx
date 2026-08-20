import {Easing, Interactive, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {palette} from '../theme';

export const OperationCard: React.FC<{
  label: string;
  index: number;
  accent?: string;
  elite?: boolean;
}> = ({label, index, accent = palette.primary, elite = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`Operation ${label}`}
      style={{
        width: 250,
        height: 160,
        borderRadius: 26,
        backgroundColor: '#FFFFFF',
        border: elite ? `8px solid ${palette.gold}` : `5px solid ${accent}`,
        boxShadow: '0 24px 55px rgba(11, 23, 42, 0.14)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 12,
        color: palette.ink,
        opacity: interpolate(frame, [index * 5, index * 5 + 14], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
        scale: spring({frame: frame - index * 5, fps, config: {damping: 16, stiffness: 120}}),
      }}
    >
      <div style={{fontSize: 24, color: accent, fontWeight: 800, letterSpacing: 2}}>
        {String(index + 1).padStart(2, '0')}
      </div>
      <div style={{fontSize: 35, lineHeight: 1.05, fontWeight: 750, textAlign: 'center', padding: '0 14px'}}>
        {label}
      </div>
      {elite ? <div style={{fontSize: 18, fontWeight: 900, color: palette.gold}}>ELITE · PROTECTED</div> : null}
    </Interactive.Div>
  );
};

