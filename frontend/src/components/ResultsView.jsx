/**
 * Results View Component
 * Displays portfolio optimization results
 */

import React from 'react';
import StockCard from './StockCard';
import SectorDonut from './Visualizations/SectorDonut';
import CorrelationHeatmap from './Visualizations/CorrelationHeatmap';
import RiskReturnScatter from './Visualizations/RiskReturnScatter';

const ResultsView = ({ results }) => {
  const {
    portfolio,
    expected_return,
    risk_score,
    sharpe_ratio,
    max_drawdown,
    sector_breakdown,
    correlation_score,
    stock_details,
    alternatives,
    warnings,
    metadata,
  } = results;

  // Format percentage
  const pct = (value) => (value * 100).toFixed(2);

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Optimized Portfolio
          </h2>
          <div className="text-sm text-gray-500">
            Generated in {metadata.optimization_time_ms}ms
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <div className="text-3xl font-bold text-primary-700">
              {pct(expected_return)}%
            </div>
            <div className="text-sm text-gray-600 mt-1">Expected Return</div>
          </div>

          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-700">
              {pct(risk_score)}%
            </div>
            <div className="text-sm text-gray-600 mt-1">Risk (Volatility)</div>
          </div>

          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-700">
              {sharpe_ratio.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 mt-1">Sharpe Ratio</div>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-3xl font-bold text-purple-700">
              {pct(max_drawdown)}%
            </div>
            <div className="text-sm text-gray-600 mt-1">Max Drawdown</div>
          </div>
        </div>

        {/* Diversification Score */}
        <div className="p-4 bg-gradient-to-r from-primary-50 to-accent-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-700">Diversification Score</div>
              <div className="text-xs text-gray-500 mt-1">
                Average correlation: {pct(correlation_score)}%
                {' • '}
                {Object.keys(sector_breakdown).length} sectors represented
              </div>
            </div>
            <div className="text-3xl font-bold text-primary-700">
              {correlation_score < 0.4 ? 'Excellent' : correlation_score < 0.6 ? 'Good' : 'Fair'}
            </div>
          </div>
        </div>

        {/* Warnings */}
        {warnings && warnings.length > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="font-semibold text-yellow-900 mb-2">⚠️ Warnings</div>
            <ul className="list-disc list-inside space-y-1">
              {warnings.map((warning, idx) => (
                <li key={idx} className="text-sm text-yellow-800">{warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Sector Allocation</h3>
          <SectorDonut data={sector_breakdown} />
        </div>

        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Risk vs Return</h3>
          <RiskReturnScatter stocks={stock_details} />
        </div>
      </div>

      {/* Stock Cards */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Portfolio Holdings ({portfolio.length} stocks)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stock_details.map((stock) => (
            <StockCard key={stock.ticker} stock={stock} />
          ))}
        </div>
      </div>

      {/* Alternative Portfolios */}
      {alternatives && alternatives.length > 0 && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Alternative Portfolios
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Here are other high-quality portfolios that also meet your criteria
          </p>

          <div className="space-y-4">
            {alternatives.map((alt, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold text-gray-900">
                    Option {idx + 2}
                  </div>
                  <div className="flex space-x-4 text-sm">
                    <span>Return: <strong>{pct(alt.expected_return)}%</strong></span>
                    <span>Risk: <strong>{pct(alt.risk_score)}%</strong></span>
                    <span>Sharpe: <strong>{alt.sharpe_ratio.toFixed(2)}</strong></span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {alt.portfolio.map((ticker) => (
                    <span key={ticker} className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-medium">
                      {ticker}
                    </span>
                  ))}
                </div>

                {/* Sector breakdown for alternative */}
                <div className="mt-3 text-xs text-gray-500">
                  Sectors: {Object.entries(alt.sector_breakdown).map(([sector, count]) =>
                    `${sector} (${count})`
                  ).join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="card bg-gray-50 border border-gray-300">
        <div className="flex items-start space-x-3">
          <div className="text-2xl">⚠️</div>
          <div className="flex-1 text-sm text-gray-700">
            <strong>Disclaimer:</strong> This is an educational tool for portfolio construction and analysis.
            Past performance does not guarantee future results. This is not financial advice.
            Always consult with a qualified financial advisor before making investment decisions.
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsView;
