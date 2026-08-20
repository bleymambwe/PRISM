import type {ClaimStatus} from '../types';
import {statusColor} from '../theme';

export const StatusBadge: React.FC<{status: ClaimStatus}> = ({status}) => (
  <div
    style={{
      padding: '12px 22px',
      borderRadius: 999,
      backgroundColor: statusColor[status],
      color: '#FFFFFF',
      fontSize: 22,
      fontWeight: 900,
      letterSpacing: 1.6,
      textTransform: 'uppercase',
    }}
  >
    {status}
  </div>
);

