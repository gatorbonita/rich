/**
 * Stock Card Component
 * Displays information about a single stock in the portfolio
 */

import React from 'react';

const StockCard = ({ stock }) => {
  const { ticker, sector, weight, expected_return, volatility, sharpe_ratio } = stock;

  // Sector colors
  const sectorColors = {
    'Technology': 'bg-blue-100 text-blue-800 border-blue-300',
    'Financials': 'bg-green-100 text-green-800 border-green-300',
    'Healthcare': 'bg-red-100 text-red-800 border-red-300',
    'Consumer Discretionary': 'bg-purple-100 text-purple-800 border-purple-300',
    'Energy': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'Industrials': 'bg-gray-100 text-gray-800 border-gray-300',
    'Materials': 'bg-orange-100 text-orange-800 border-orange-300',
    'Real Estate': 'bg-pink-100 text-pink-800 border-pink-300',
    'Utilities': 'bg-teal-100 text-teal-800 border-teal-300',
    'Communication Services': 'bg-indigo-100 text-indigo-800 border-indigo-300',
    'Consumer Staples': 'bg-lime-100 text-lime-800 border-lime-300',
  };

  const sectorColor = sectorColors[sector] || 'bg-gray-100 text-gray-800 border-gray-300';

  // Sharpe rating
  const getSharpeRating = (sharpe) => {
    if (sharpe > 1.5) return { label: 'Excellent', color: 'text-green-600' };
    if (sharpe > 1.0) return { label: 'Good', color: 'text-blue-600' };
    if (sharpe > 0.5) return { label: 'Fair', color: 'text-yellow-600' };
    return { label: 'Poor', color: 'text-red-600' };
  };

  const sharpeRating = getSharpeRating(sharpe_ratio);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{ticker}</h3>
          <span className={`inline-block px-2 py-1 text-xs font-semibold rounded border mt-1 ${sectorColor}`}>
            {sector}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary-600">
            {(weight * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">Portfolio Weight</div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div>
          <div className="text-xs text-gray-500">Expected Return</div>
          <div className="text-lg font-semibold text-gray-900">
            {(expected_return * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">Volatility</div>
          <div className="text-lg font-semibold text-gray-900">
            {(volatility * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Sharpe Ratio */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Sharpe Ratio</span>
          <span className={`text-sm font-semibold ${sharpeRating.color}`}>
            {sharpe_ratio.toFixed(2)} - {sharpeRating.label}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StockCard;
