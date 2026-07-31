import { describe, expect, it, vi } from "vitest";
import { warnBeforeUnload } from "./beforeUnload.js";

describe("warnBeforeUnload", () => {
  it("prevents default and sets returnValue to trigger the browser's leave-site prompt", () => {
    const event = { preventDefault: vi.fn(), returnValue: undefined };
    warnBeforeUnload(event);
    expect(event.preventDefault).toHaveBeenCalled();
    expect(event.returnValue).toBe("");
  });
});
