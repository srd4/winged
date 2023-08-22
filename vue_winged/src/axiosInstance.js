import axios from 'axios'

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',  }
});

// Add a request interceptor to set the token header dynamically
axiosInstance.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Token ${token}`;
  }
  return config;
});

export const refreshAxiosToken = () => {
  const token = localStorage.getItem('token') || '';
  axiosInstance.defaults.headers['Authorization'] = `Token ${token}`;
}


export default axiosInstance