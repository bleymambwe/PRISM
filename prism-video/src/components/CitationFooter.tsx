import {palette} from '../theme';

export const CitationFooter: React.FC<{source: string; graphId?: string; chapter: string}> = ({source, graphId, chapter}) => (
  <div
    style={{
      position: 'absolute',
      left: 110,
      right: 110,
      bottom: 48,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontSize: 23,
      color: palette.slate,
      letterSpacing: 0.3,
    }}
  >
    <div>{chapter}</div>
    <div style={{maxWidth: 2300, textAlign: 'right'}}>{graphId ? `${graphId} · ` : ''}{source}</div>
  </div>
);

