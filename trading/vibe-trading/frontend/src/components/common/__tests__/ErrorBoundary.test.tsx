import React from "react";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "../ErrorBoundary";

function Thrower({ message }: { message: string }): React.ReactElement {
  throw new Error(message);
}

// Suppress React error boundary console.error in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (typeof args[0] === "string" && args[0].includes("ErrorBoundary")) return;
    originalError(...args);
  };
});
afterAll(() => {
  console.error = originalError;
});

describe("ErrorBoundary", () => {
  it("renders children normally when no error", () => {
    render(
      <ErrorBoundary>
        <div>Hello World</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders default fallback with error message on error", () => {
    render(
      <ErrorBoundary>
        <Thrower message="Something broke" />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something broke")).toBeInTheDocument();
  });

  it("renders custom fallback when provided", () => {
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <Thrower message="ignored" />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Custom fallback")).toBeInTheDocument();
    expect(screen.queryByText("ignored")).not.toBeInTheDocument();
  });

  it("shows default message when error has no message", () => {
    function ThrowEmpty(): React.ReactElement {
      throw {};
    }
    render(
      <ErrorBoundary>
        <ThrowEmpty />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });
});
