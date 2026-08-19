export type PredictionScore = {
  category: string;
  probability: number;
};

export type AnalysisResult = {
  predictionId: string;
  category: string;
  confidence: number;
  uncertain: boolean;
  scores: PredictionScore[];
  modelName: string;
  modelVersion: string;

  woundType?: string | null;
  woundTypeConfidence?: number | null;
  woundTypeUncertain?: boolean | null;
  woundTypeScores?: PredictionScore[];
  woundTypeModelName?: string | null;
  woundTypeModelVersion?: string | null;
};