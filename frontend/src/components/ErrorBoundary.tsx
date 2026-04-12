'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  componentName?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.error(
      `ErrorBoundary caught error in ${this.props.componentName || 'component'}:`,
      error,
      errorInfo
    )
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900 p-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-semibold text-red-700 dark:text-red-400 text-sm">
                Something went wrong
              </h3>
              <p className="text-xs text-red-600 dark:text-red-500 mt-1 break-words">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="mt-3 text-xs text-red-600 underline hover:no-underline"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// HOC version for easy wrapping
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) {
  return function WrappedComponent(props: P) {
    return (
      <ErrorBoundary componentName={componentName}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
