import axios from 'axios'

localStorage.setItem('token', '8e257f25b53e9414e80f4730bda75ff57c2434e3')

const token = localStorage.getItem('token')

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  }
})

export default axiosInstance