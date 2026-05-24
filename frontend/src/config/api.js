// API Configuration for development and production
const isDevelopment = process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

export const API_BASE_URL = isDevelopment 
  ? 'http://127.0.0.1:8000'
  : 'https://stock-simulator-predictor.onrender.com';

export default API_BASE_URL;
