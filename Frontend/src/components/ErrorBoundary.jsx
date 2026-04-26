import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Boundary Caught Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full min-h-[36rem] flex-col items-center justify-center rounded-[2rem] border border-rose-500/20 bg-rose-500/10 p-8 text-center shadow-glow">
          <h2 className="mb-4 text-xl font-bold text-rose-400">Neural Graph Crash</h2>
          <p className="mb-6 text-sm text-rose-200/70">{this.state.error?.message || "Internal Rendering Error"}</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })}
            className="rounded-xl bg-rose-500 px-6 py-2 text-sm font-bold text-white transition-all hover:bg-rose-400"
          >
            Attempt Re-link
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
