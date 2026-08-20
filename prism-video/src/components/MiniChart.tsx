import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import graphExtractsRaw from '../data/graphExtracts.json';
import {palette} from '../theme';
import type {GraphExtract} from '../types';

const graphExtracts = graphExtractsRaw as Record<string, GraphExtract>;

const fallback: GraphExtract = {
  id: 'summary',
  kind: 'bar',
  title: 'Reported summary reconstruction',
  xLabel: 'Compared condition',
  yLabel: 'Reported value',
  sample: 'See source note',
  points: [
    {x: 0, y: 0.32, label: 'question'},
    {x: 1, y: 0.66, label: 'measure'},
    {x: 2, y: 0.91, label: 'finding'},
  ],
  source: {artifact: 'production brief'},
  summary: 'Only explicitly reported summary values are reconstructed.',
};

export const MiniChart: React.FC<{graphId?: string}> = ({graphId}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const graph = (graphId && graphExtracts[graphId]) || fallback;
  const points = graph.points.slice(0, 240);
  const maxY = Math.max(1e-6, ...points.map((p) => p.y));
  const minY = Math.min(0, ...points.map((p) => p.y));
  const rangeY = Math.max(1e-6, maxY - minY);
  const seriesNames = [...new Set(points.map((p) => p.series || 'PRISM'))];
  const colors = [palette.primary, palette.theory, palette.positive, palette.warning, palette.negative, palette.slate];
  return (
    <div style={{width: 2500, height: 1040, backgroundColor: '#FFFFFF', borderRadius: 34, padding: '58px 70px 70px', boxShadow: '0 28px 80px rgba(11,23,42,0.12)', position: 'relative'}}>
      <div style={{fontSize: 49, fontWeight: 850, color: palette.ink}}>{graph.title}</div>
      <div style={{fontSize: 25, color: palette.slate, marginTop: 8}}>n = {graph.sample}</div>
      <svg width="2360" height="780" viewBox="0 0 2360 780" role="img" aria-label={graph.summary}>
        <line x1="150" y1="680" x2="2270" y2="680" stroke={palette.ink} strokeWidth="4" />
        <line x1="150" y1="100" x2="150" y2="680" stroke={palette.ink} strokeWidth="4" />
        <text x="1210" y="760" textAnchor="middle" fontSize="31" fill={palette.ink}>{graph.xLabel}</text>
        <text x="36" y="390" textAnchor="middle" fontSize="31" fill={palette.ink} transform="rotate(-90 36 390)">{graph.yLabel}</text>
        {points.map((point, index) => {
          const x = 170 + (index / Math.max(1, points.length - 1)) * 2070;
          const baseY = 680 - ((Math.max(0, point.y) - minY) / rangeY) * 560;
          const color = colors[Math.max(0, seriesNames.indexOf(point.series || 'PRISM')) % colors.length];
          const progress = interpolate(frame, [8 + index * 0.12, Math.min(durationInFrames - 1, 28 + index * 0.12)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          if (graph.kind === 'bar' || graph.kind === 'histogram' || graph.kind === 'interval') {
            const barWidth = Math.max(5, 1980 / Math.max(12, points.length));
            return <rect key={index} x={x - barWidth / 2} y={680 - (680 - baseY) * progress} width={barWidth} height={(680 - baseY) * progress} rx="4" fill={color} opacity="0.83" />;
          }
          return <circle key={index} cx={x} cy={680 - (680 - baseY) * progress} r={points.length > 100 ? 5 : 10} fill={color} opacity="0.85" />;
        })}
      </svg>
      <div style={{position: 'absolute', left: 220, right: 100, bottom: 32, display: 'flex', gap: 38}}>
        {seriesNames.slice(0, 6).map((name, index) => <div key={name} style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: 22, color: palette.ink}}><span style={{width: 18, height: 18, borderRadius: 5, backgroundColor: colors[index % colors.length]}} />{name}</div>)}
      </div>
    </div>
  );
};
