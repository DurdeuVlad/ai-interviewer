import { describe, expect, it, vi } from "vitest";
import { notifyInterviewsChanged, onInterviewsChanged } from "./interviewEvents.js";

describe("interviewEvents", () => {
  it("calls the handler when notified, and stops after unsubscribe", () => {
    const handler = vi.fn();
    const unsubscribe = onInterviewsChanged(handler);

    notifyInterviewsChanged();
    expect(handler).toHaveBeenCalledTimes(1);

    unsubscribe();
    notifyInterviewsChanged();
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
