import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ErrorBanner from "./ErrorBanner.jsx";

function renderBanner(props) {
  return render(
    <MemoryRouter>
      <ErrorBanner {...props} />
    </MemoryRouter>
  );
}

describe("ErrorBanner", () => {
  it("renders nothing when there is no error", () => {
    const { container } = renderBanner({ error: null });
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a 'View summary' link for an already-ended interview 409", () => {
    renderBanner({
      error: { status: 409, detail: "This interview has already ended." },
      summaryHref: "/interview/1",
    });
    expect(screen.getByRole("link", { name: /view summary/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /try again/i })).not.toBeInTheDocument();
  });

  it("shows a 'Try again' button for a duplicate-answer 409, not a summary link", () => {
    const onRetry = vi.fn();
    renderBanner({
      error: { status: 409, detail: "This question has already been answered." },
      summaryHref: "/interview/1",
      onRetry,
    });
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /view summary/i })).not.toBeInTheDocument();
  });

  it("falls back to the generic message when there's no detail", () => {
    renderBanner({ error: { status: 500 } });
    expect(screen.getByText(/unexpected error/i)).toBeInTheDocument();
  });
});
