import type {Caption} from '@remotion/captions';

export type ClaimStatus =
  | 'concept'
  | 'completed'
  | 'corrected'
  | 'negative'
  | 'boundary'
  | 'planned';

export type EquationCue = {
  displayText: string;
  spokenText: string;
};

export type GraphSource = {
  artifact: string;
  rowCount?: number;
  filters?: string[];
  transforms?: string[];
  xAxis?: string;
  yAxis?: string;
};

export type PrismScene = {
  id: string;
  chapter: string;
  chapterTitle: string;
  title: string;
  visual: string;
  audio: string;
  durationInFrames: number;
  spokenText: string;
  captionCues: Caption[];
  equations?: EquationCue[];
  chartData?: unknown;
  graphId?: string;
  graphSource?: GraphSource;
  finding: string;
  limitation: string;
  downstreamDecision: string;
  claimStatus: ClaimStatus;
  source: string;
  sampleSize: string;
  caveat: string;
  altDescription: string;
  paperFigures?: number[];
  paperTables?: number[];
  algorithms?: number[];
  isEpilogue?: boolean;
};

export type FilmDefinition = {
  title: string;
  fps: number;
  scenes: PrismScene[];
};

export type AudioManifest = {
  generatedAt: string;
  sampleRate: number;
  voice: string;
  scenes: Record<
    string,
    {
      durationSeconds: number;
      durationInFrames: number;
      peakDbfs: number;
      captions: Caption[];
    }
  >;
};

export type GraphPoint = {x: number; y: number; label?: string; series?: string};
export type GraphExtract = {
  id: string;
  kind: 'bar' | 'line' | 'scatter' | 'histogram' | 'heatmap' | 'interval';
  title: string;
  xLabel: string;
  yLabel: string;
  sample: string;
  points: GraphPoint[];
  source: GraphSource;
  summary: string;
};

