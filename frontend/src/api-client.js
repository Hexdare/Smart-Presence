import { CapacitorHttp } from '@capacitor/http';
import { Capacitor } from '@capacitor/core';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, '') || "";

console.log('API Client initialized with backend URL:', BACKEND_URL);

class ApiClient {
  static async request(url, options = {}) {
    const fullUrl = `${BACKEND_URL}${url}`;
    console.log('API Request:', options.method || 'GET', fullUrl);
    
    if (Capacitor.isNativePlatform()) {
      try {
        // Use Capacitor HTTP for mobile
        const response = await CapacitorHttp.request({
          url: fullUrl,
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...options.headers
          },
          data: options.body ? JSON.parse(options.body) : undefined,
          connectTimeout: 10000,
          readTimeout: 10000
        });
        
        console.log('Mobile API Response:', response.status, response.data);
        
        return {
          ok: response.status >= 200 && response.status < 300,
          status: response.status,
          json: async () => response.data,
          text: async () => JSON.stringify(response.data)
        };
      } catch (error) {
        console.error('Mobile API Error:', error);
        throw new Error(`Network request failed: ${error.message}`);
      }
    } else {
      // Use fetch for web
      try {
        const response = await fetch(fullUrl, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...options.headers
          }
        });
        
        console.log('Web API Response:', response.status);
        return response;
      } catch (error) {
        console.error('Web API Error:', error);
        throw error;
      }
    }
  }

  static async get(url, headers = {}) {
    return this.request(url, { method: 'GET', headers });
  }

  static async post(url, data, headers = {}) {
    return this.request(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
  }

  static async put(url, data, headers = {}) {
    return this.request(url, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data)
    });
  }

  static async delete(url, headers = {}) {
    return this.request(url, { method: 'DELETE', headers });
  }

  // Test connectivity
  static async testConnection() {
    try {
      console.log('Testing backend connection...');
      const response = await this.get('/health');
      console.log('Connection test successful:', response.status);
      return true;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }
}

export default ApiClient;