import { Component, ErrorInfo, ReactNode } from "react";

type State = { hasError: boolean };

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Page error", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-red-400/30 bg-red-950/40 p-8">
          <h2 className="text-lg font-semibold text-red-100">Something went wrong</h2>
          <p className="mt-2 text-sm text-red-200/80">The page hit an unexpected error while rendering data.</p>
          <button onClick={() => this.setState({ hasError: false })} className="mt-4 rounded-lg bg-red-400 px-4 py-2 font-semibold text-red-950">
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
