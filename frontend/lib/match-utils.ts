/**
 * Utilities for the /match job ranking page.
 */

/** Score thresholds for colour-coding the combined-score bar. */
export const SCORE_GREEN_THRESHOLD = 0.7;
export const SCORE_AMBER_THRESHOLD = 0.4;

/** Return the Tailwind colour token for a combined score in [0, 1]. */
export function scoreColor(score: number): "success" | "warning" | "critical" {
  if (score >= SCORE_GREEN_THRESHOLD) return "success";
  if (score >= SCORE_AMBER_THRESHOLD) return "warning";
  return "critical";
}

/** Format a [0, 1] score as a percentage string e.g. "72%". */
export function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/** Return the hex / Tailwind class used for the progress bar fill. */
export function scoreBarClass(score: number): string {
  if (score >= SCORE_GREEN_THRESHOLD) return "bg-success";
  if (score >= SCORE_AMBER_THRESHOLD) return "bg-warning";
  return "bg-critical";
}
