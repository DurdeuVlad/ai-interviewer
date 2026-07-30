import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ChatBubble from "./ChatBubble.jsx";

describe("ChatBubble", () => {
  it("aligns user messages to the right", () => {
    render(
      <ChatBubble sender="user">
        <span>hello</span>
      </ChatBubble>
    );
    const bubble = screen.getByText("hello").closest("div").parentElement;
    expect(bubble).toHaveStyle({ justifyContent: "flex-end" });
  });

  it("aligns assistant messages to the left", () => {
    render(
      <ChatBubble sender="assistant">
        <span>hi there</span>
      </ChatBubble>
    );
    const bubble = screen.getByText("hi there").closest("div").parentElement;
    expect(bubble).toHaveStyle({ justifyContent: "flex-start" });
  });
});
