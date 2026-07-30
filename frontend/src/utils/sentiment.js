// Mirrors backend/app/cli.py's _sentiment_label bucketing.
export function sentimentLabel(score) {
  if (score >= 0.5) return "very positive";
  if (score >= 0.05) return "positive";
  if (score <= -0.5) return "very negative";
  if (score <= -0.05) return "negative";
  return "neutral";
}
