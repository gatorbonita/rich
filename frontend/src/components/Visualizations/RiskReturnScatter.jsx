/**
 * Risk vs Return Scatter Plot
 * Displays stocks on a risk-return chart
 */

import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts';

const RiskReturnScatter = ({ stocks }) => {
  // Prepare data
  const chartData = stocks.map(stock => ({
    name: stock.ticker,
    risk: stock.volatility * 100,
    return: stock.expected_return * 100,
    sharpe: stock.sharpe_ratio,
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-bold text-gray-900 mb-2">{data.name}</p>
          <p className="text-sm text-gray-600">Return: {data.return.toFixed(2)}%</p>
          <p className="text-sm text-gray-600">Risk: {data.risk.toFixed(2)}%</p>
          <p className="text-sm text-gray-600">Sharpe: {data.sharpe.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart
        margin={{ top: 20, right: 20, bottom: 40, left: 40 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey="risk"
          name="Risk"
          unit="%"
        >
          <Label value="Risk (Volatility %)" offset={-20} position="insideBottom" />
        </XAxis>
        <YAxis
          type="number"
          dataKey="return"
          name="Return"
          unit="%"
        >
          <Label value="Expected Return %" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
        </YAxis>
        <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <Scatter
          name="Stocks"
          data={chartData}
          fill="#3b82f6"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default RiskReturnScatter;
