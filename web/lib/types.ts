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
};
