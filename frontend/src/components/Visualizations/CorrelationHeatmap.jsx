/**
 * Correlation Heatmap (Simplified)
 * Note: Full heatmap would require more complex rendering
 * This shows average correlation as a simple metric
 */

import React from 'react';

const CorrelationHeatmap = ({ correlationScore }) => {
  // Determine color based on correlation
  const getColor = (score) => {
    if (score < 0.3) return 'bg-green-500';
    if (score < 0.5) return 'bg-yellow-500';
    if (score < 0.7) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getRating = (score) => {
    if (score < 0.3) return 'Low Correlation - Excellent Diversification';
    if (score < 0.5) return 'Moderate Correlation - Good Diversification';
    if (score < 0.7) return 'High Correlation - Fair Diversification';
    return 'Very High Correlation - Limited Diversification';
  };

  const percentage = (correlationScore * 100).toFixed(1);

  return (
    <div className="flex flex-col items-center justify-center h-64">
      {/* Correlation Score Circle */}
      <div className={`w-32 h-32 rounded-full ${getColor(correlationScore)} flex items-center justify-center mb-4`}>
        <div className="text-center text-white">
          <div className="text-3xl font-bold">{percentage}%</div>
          <div className="text-xs">Avg Correlation</div>
        </div>
      </div>

      {/* Rating */}
      <div className="text-center">
        <div className="text-lg font-semibold text-gray-900 mb-2">
          {getRating(correlationScore)}
        </div>
        <div className="text-sm text-gray-600">
          Lower correlation means stocks move independently,
          <br />
          providing better risk reduction through diversification.
        </div>
      </div>
    </div>
  );
};

export default CorrelationHeatmap;
