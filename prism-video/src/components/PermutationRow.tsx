import {OperationCard} from './OperationCard';
import {palette} from '../theme';

const defaultCards = ['RESTATE', 'IDENTIFY', 'PLAN', 'COMPUTE', 'CHECK', 'ANSWER'];

export const PermutationRow: React.FC<{
  cards?: string[];
  eliteIndex?: number;
  compact?: boolean;
}> = ({cards = defaultCards, eliteIndex, compact = false}) => {
  const accents = [palette.primary, palette.theory, palette.positive, palette.warning, palette.negative, palette.slate];
  return (
    <div style={{display: 'flex', gap: compact ? 18 : 28, alignItems: 'center', justifyContent: 'center'}}>
      {cards.map((card, index) => (
        <div key={`${card}-${index}`} style={{scale: compact ? 0.72 : 1, margin: compact ? '-20px -30px' : 0}}>
          <OperationCard label={card} index={index} accent={accents[index % accents.length]} elite={eliteIndex === index} />
        </div>
      ))}
    </div>
  );
};

