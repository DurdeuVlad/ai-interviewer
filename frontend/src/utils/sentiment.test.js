import { describe, expect, it } from "vitest";
import { sentimentLabel } from "./sentiment.js";

describe("sentimentLabel", () => {
  it.each([
    [0.8, "very positive"],
    [0.5, "very positive"],
    [0.3, "positive"],
    [0.05, "positive"],
    [0.0, "neutral"],
    [-0.04, "neutral"],
    [-0.05, "negative"],
    [-0.3, "negative"],
    [-0.5, "very negative"],
    [-0.9, "very negative"],
  ])("scores %s as %s", (score, expected) => {
    expect(sentimentLabel(score)).toBe(expected);
  });
});
