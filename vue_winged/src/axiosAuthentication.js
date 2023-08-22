import axios from 'axios'
import refreshAxiosToken from './axiosInstance'

function login(username, password) {
  return axios.post('http://localhost:8000/api/token/', { username, password })
    .then(response => {
      const token = response.data.token;
      localStorage.setItem('token', token);
    });
}

function logout() {
  localStorage.removeItem('token');
  refreshAxiosToken();
}


export default { login, logout };