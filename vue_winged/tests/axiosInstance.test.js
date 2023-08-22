import axiosInstance from '../src/axiosInstance';
import { refreshAxiosToken } from '../src/axiosInstance';
import MockAdapter from "axios-mock-adapter"


const mock = new MockAdapter(axiosInstance);

it('has the correct base configuration', () => {
    expect(axiosInstance.defaults.headers['Content-Type']).toBe('application/json');
    expect(axiosInstance.defaults.baseURL).toBe('http://localhost:8000');
  });


it('adds token to headers if it exists', () => {
    // Mock localStorage
    global.localStorage = {
        getItem: jest.fn(() => 'test-token'),
    };

    // Define the mock behavior
    mock.onGet('/some-endpoint').reply(200);

    // Make the actual request
    return axiosInstance.get('/some-endpoint').then(() => {
    // Check the request that was actually sent
    expect(mock.history.get[0].headers['Authorization']).toBe('Token test-token');
    });
});

it('refreshes the token header', () => {
    const newToken = 'another-test-token';

    global.localStorage = {
      getItem: jest.fn(() => newToken),
    };
  
    refreshAxiosToken();
  
    expect(axiosInstance.defaults.headers['Authorization']).toBe(`Token ${newToken}`);
});
