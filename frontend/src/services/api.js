/**
 * API service for communicating with the backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds (first run can take longer due to data fetching)
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Optimize portfolio based on configuration
 * @param {Object} config - Optimization configuration
 * @returns {Promise} - Optimization result
 */
export const optimizePortfolio = async (config) => {
  try {
    const response = await api.post('/api/optimize', config);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Optimization error:', error);

    if (error.response) {
      // Server responded with error
      return {
        success: false,
        error: error.response.data?.error || 'optimization_error',
        message: error.response.data?.message || error.response.data?.detail?.message || 'Optimization failed',
        status: error.response.status
      };
    } else if (error.request) {
      // No response received
      return {
        success: false,
        error: 'network_error',
        message: 'Cannot connect to server. Please ensure the backend is running.'
      };
    } else {
      // Error setting up request
      return {
        success: false,
        error: 'unknown_error',
        message: error.message || 'An unknown error occurred'
      };
    }
  }
};

/**
 * Get health status of the API
 * @returns {Promise} - Health status
 */
export const getHealth = async () => {
  try {
    const response = await api.get('/api/health');
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Health check error:', error);
    return {
      success: false,
      error: 'health_check_failed',
      message: 'Backend is not responding'
    };
  }
};

/**
 * Get stock universe
 * @returns {Promise} - Universe data
 */
export const getUniverse = async () => {
  try {
    const response = await api.get('/api/universe');
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Get universe error:', error);
    return {
      success: false,
      error: 'universe_error',
      message: 'Failed to load stock universe'
    };
  }
};

/**
 * Get information about a specific stock
 * @param {string} ticker - Stock ticker symbol
 * @returns {Promise} - Stock information
 */
export const getStock = async (ticker) => {
  try {
    const response = await api.get(`/api/stock/${ticker}`);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Get stock error:', error);
    return {
      success: false,
      error: 'stock_error',
      message: `Failed to load information for ${ticker}`
    };
  }
};

/**
 * Validate configuration before optimization
 * @param {Object} config - Configuration to validate
 * @returns {Promise} - Validation result
 */
export const validateConfig = async (config) => {
  try {
    const response = await api.post('/api/validate', config);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Validation error:', error);
    return {
      success: false,
      error: 'validation_error',
      message: 'Configuration validation failed'
    };
  }
};

export default {
  optimizePortfolio,
  getHealth,
  getUniverse,
  getStock,
  validateConfig,
};
