import {PrismFullFilm} from './PrismFullFilm';

export const PrismChapter: React.FC<{chapter: string}> = ({chapter}) => <PrismFullFilm chapter={chapter} />;
export const PrismEpilogue: React.FC = () => <PrismFullFilm epilogueOnly />;

