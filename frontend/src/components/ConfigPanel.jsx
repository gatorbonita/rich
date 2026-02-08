/**
 * Configuration Panel Component
 * Allows users to configure portfolio optimization parameters
 */

import React, { useState } from 'react';

const ConfigPanel = ({ onOptimize, isLoading }) => {
  const [config, setConfig] = useState({
    max_stocks: 10,
    min_return: 0.12,
    risk_window_months: 12,
    return_window_months: 3,
    top_k_per_sector: 5,
    correlation_threshold: 0.75,
  });

  const handleChange = (field, value) => {
    setConfig({ ...config, [field]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onOptimize(config);
  };

  const riskProfiles = {
    low: { min_return: 0.08, correlation_threshold: 0.70 },
    medium: { min_return: 0.12, correlation_threshold: 0.75 },
    high: { min_return: 0.18, correlation_threshold: 0.80 },
  };

  const applyRiskProfile = (profile) => {
    setConfig({ ...config, ...riskProfiles[profile] });
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Portfolio Configuration
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Risk Profile Quick Select */}
        <div>
          <label className="label">Quick Select Risk Profile</label>
          <div className="grid grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => applyRiskProfile('low')}
              className="btn-secondary"
            >
              Low Risk
            </button>
            <button
              type="button"
              onClick={() => applyRiskProfile('medium')}
              className="btn-secondary"
            >
              Medium Risk
            </button>
            <button
              type="button"
              onClick={() => applyRiskProfile('high')}
              className="btn-secondary"
            >
              High Risk
            </button>
          </div>
        </div>

        {/* Number of Stocks */}
        <div>
          <label className="label">
            Number of Stocks: <span className="font-bold">{config.max_stocks}</span>
          </label>
          <input
            type="range"
            min="5"
            max="15"
            step="1"
            value={config.max_stocks}
            onChange={(e) => handleChange('max_stocks', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>5</span>
            <span>10</span>
            <span>15</span>
          </div>
        </div>

        {/* Target Return */}
        <div>
          <label className="label">
            Target Annual Return: <span className="font-bold">{(config.min_return * 100).toFixed(1)}%</span>
          </label>
          <input
            type="range"
            min="0.05"
            max="0.30"
            step="0.01"
            value={config.min_return}
            onChange={(e) => handleChange('min_return', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>5%</span>
            <span>15%</span>
            <span>30%</span>
          </div>
        </div>

        {/* Advanced Options Toggle */}
        <details className="border border-gray-200 rounded-lg p-4">
          <summary className="cursor-pointer font-semibold text-gray-700">
            Advanced Options
          </summary>

          <div className="mt-4 space-y-4">
            {/* Risk Window */}
            <div>
              <label className="label">
                Risk Window (months): {config.risk_window_months}
              </label>
              <input
                type="range"
                min="6"
                max="24"
                step="3"
                value={config.risk_window_months}
                onChange={(e) => handleChange('risk_window_months', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
            </div>

            {/* Return Window */}
            <div>
              <label className="label">
                Return Window (months): {config.return_window_months}
              </label>
              <input
                type="range"
                min="1"
                max="12"
                step="1"
                value={config.return_window_months}
                onChange={(e) => handleChange('return_window_months', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
            </div>

            {/* Correlation Threshold */}
            <div>
              <label className="label">
                Correlation Threshold: {(config.correlation_threshold * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={config.correlation_threshold}
                onChange={(e) => handleChange('correlation_threshold', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <p className="text-xs text-gray-500 mt-1">
                Lower values = more diversification
              </p>
            </div>

            {/* Stocks per Sector */}
            <div>
              <label className="label">
                Top Stocks per Sector: {config.top_k_per_sector}
              </label>
              <input
                type="range"
                min="3"
                max="10"
                step="1"
                value={config.top_k_per_sector}
                onChange={(e) => handleChange('top_k_per_sector', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
            </div>
          </div>
        </details>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Optimizing...
            </span>
          ) : (
            'Optimize Portfolio'
          )}
        </button>
      </form>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-900">
          <strong>How it works:</strong> We analyze stocks across 11 sectors, select top performers,
          and build a diversified portfolio that minimizes risk while targeting your desired return.
        </p>
      </div>
    </div>
  );
};

export default ConfigPanel;
