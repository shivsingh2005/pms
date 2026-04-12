"use client";

import { Component, type ReactNode } from "react";

type DashboardErrorProps = {
  children: ReactNode;
  name?: string;
};

type DashboardErrorState = {
  error: Error | null;
};

export class DashboardError extends Component<DashboardErrorProps, DashboardErrorState> {
  state: DashboardErrorState = { error: null };

  static getDerivedStateFromError(error: Error): DashboardErrorState {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack?: string }) {
    console.error(`[${this.props.name ?? "Dashboard"}] crash:`, error.message, info.componentStack || "");
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-6xl p-8">
          <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950/20">
            <p className="mb-4 text-4xl">⚠️</p>
            <h2 className="font-semibold text-red-700 dark:text-red-400">Dashboard crashed</h2>
            <p className="mt-2 font-mono text-sm text-red-600 dark:text-red-500">{this.state.error.message}</p>
            <button
              onClick={() => this.setState({ error: null })}
              className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm text-white transition hover:bg-red-700"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
