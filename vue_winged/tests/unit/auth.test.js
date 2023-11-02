import axios from "axios";
import MockAdapter from 'axios-mock-adapter'
import auth from '../../src/axiosAuthentication'

// Define a mock for localStorage
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};

// Mocking axios
const mock = new MockAdapter(axios);

describe('login', () => {
  it('stores the token in localStorage on successful login', () => {
    const token = 'test-token';
    mock.onPost('http://localhost:8000/api/token/').reply(200, { token });

    return auth.login('username', 'password').then(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith('token', token);
    });
  });

  it('returns error message on wrong credentials', () => {
    mock.onPost('http://localhost:8000/api/token/').reply(401, { detail: 'Invalid username or password' });

    return auth.login('wrong-username', 'wrong-password').catch((err) => {
      expect(err.response.data.detail).toBe('Invalid username or password');
    });
  });
  it('handles unexpected server error on login', () => {
  mock.onPost('http://localhost:8000/api/token/').reply(500);

  return auth.login('username', 'password').catch((err) => {
    expect(err.response.status).toBe(500);
  });
});
});


describe('logout', () => {
  it('removes the token from localStorage on logout', () => {
    localStorage.setItem('token', 'test-token');
    auth.logout();
    expect(localStorage.removeItem).toHaveBeenCalledWith('token');
  });
});