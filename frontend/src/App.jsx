/**
 * Main Application Component
 * Portfolio Optimization Web App
 */

import React, { useState, useEffect } from 'react';
import ConfigPanel from './components/ConfigPanel';
import ResultsView from './components/ResultsView';
import { optimizePortfolio, getHealth } from './services/api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    const response = await getHealth();
    if (response.success) {
      setBackendStatus('healthy');
    } else {
      setBackendStatus('offline');
    }
  };

  const handleOptimize = async (config) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const response = await optimizePortfolio(config);

    if (response.success) {
      setResults(response.data);
    } else {
      setError({
        code: response.error,
        message: response.message,
      });
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Portfolio Optimizer
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Build diversified, low-risk stock portfolios with AI-powered optimization
              </p>
            </div>

            {/* Backend Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                backendStatus === 'healthy' ? 'bg-green-500' :
                backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
              }`}></div>
              <span className="text-sm text-gray-600">
                {backendStatus === 'healthy' ? 'API Online' :
                 backendStatus === 'offline' ? 'API Offline' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Backend Offline Warning */}
        {backendStatus === 'offline' && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="text-2xl mr-3">⚠️</div>
              <div className="flex-1">
                <h3 className="font-semibold text-red-900">Backend API Offline</h3>
                <p className="text-sm text-red-800 mt-1">
                  Cannot connect to the backend server. Please ensure the FastAPI server is running at http://localhost:8000
                </p>
                <button
                  onClick={checkBackendHealth}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <ConfigPanel
              onOptimize={handleOptimize}
              isLoading={isLoading}
            />
          </div>

          {/* Results Area */}
          <div className="lg:col-span-2">
            {/* Loading State */}
            {isLoading && (
              <div className="card">
                <div className="flex flex-col items-center justify-center py-16">
                  <svg className="animate-spin h-16 w-16 text-primary-600 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Optimizing Your Portfolio...
                  </h3>
                  <p className="text-gray-600 text-center max-w-md">
                    Analyzing stocks, computing correlations, and finding the optimal diversified portfolio.
                    This may take a few seconds.
                  </p>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
              <div className="card border border-red-200 bg-red-50">
                <div className="flex items-start">
                  <div className="text-3xl mr-4">❌</div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-red-900 mb-2">
                      Optimization Failed
                    </h3>
                    <p className="text-red-800 mb-4">{error.message}</p>

                    {error.code === 'insufficient_return' && (
                      <div className="p-4 bg-white rounded-lg border border-red-200">
                        <p className="text-sm text-gray-700">
                          <strong>Suggestion:</strong> Try lowering your target return or adjusting other parameters.
                          The market conditions may not support the requested return level with acceptable risk.
                        </p>
                      </div>
                    )}

                    {error.code === 'network_error' && (
                      <div className="p-4 bg-white rounded-lg border border-red-200">
                        <p className="text-sm text-gray-700">
                          <strong>Troubleshooting:</strong>
                        </p>
                        <ul className="list-disc list-inside text-sm text-gray-600 mt-2 space-y-1">
                          <li>Ensure the backend server is running (cd backend && uvicorn app.main:app --reload)</li>
                          <li>Check that the server is accessible at http://localhost:8000</li>
                          <li>Verify there are no firewall or CORS issues</li>
                        </ul>
                      </div>
                    )}

                    <button
                      onClick={() => setError(null)}
                      className="mt-4 btn-secondary"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            {results && !isLoading && !error && (
              <ResultsView results={results} />
            )}

            {/* Initial State */}
            {!results && !isLoading && !error && (
              <div className="card">
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="text-6xl mb-6">📊</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-3">
                    Ready to Optimize
                  </h3>
                  <p className="text-gray-600 max-w-md mb-6">
                    Configure your portfolio parameters on the left and click "Optimize Portfolio"
                    to generate a diversified, risk-minimized investment strategy.
                  </p>

                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="font-bold text-blue-900">11 Sectors</div>
                      <div className="text-blue-700">Broad diversification</div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="font-bold text-green-900">Smart Algorithm</div>
                      <div className="text-green-700">AI-powered selection</div>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <div className="font-bold text-purple-900">Risk Minimized</div>
                      <div className="text-purple-700">Correlation-based</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 text-center text-sm text-gray-600">
          <p>
            Portfolio Optimizer v1.0 | Educational Tool for Portfolio Construction
          </p>
          <p className="mt-2">
            Data powered by Yahoo Finance | Not financial advice
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
