import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, getInterview, startInterview, submitAnswer } from "./client.js";

afterEach(() => {
  vi.unstubAllGlobals();
});

function mockFetchOnce(status, body) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    })
  );
}

describe("api client", () => {
  it("returns parsed JSON on success", async () => {
    mockFetchOnce(201, { interview_id: 1, status: "in_progress", question: "hi" });
    const res = await startInterview("topic");
    expect(res.interview_id).toBe(1);
  });

  it("throws ApiError with the backend detail message on failure", async () => {
    mockFetchOnce(409, { detail: "This interview has already ended." });
    await expect(submitAnswer(1, "answer")).rejects.toMatchObject({
      status: 409,
      detail: "This interview has already ended.",
    });
  });

  it("throws ApiError with a generic message when the body isn't JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("not json");
        },
      })
    );
    const err = await getInterview(1).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(500);
    expect(err.detail).toMatch(/500/);
  });
});
