import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export function setAuthUserId(userId: string) {
  apiClient.defaults.headers.common['X-User-Id'] = userId;
}

export function getAuthUserId(): string | undefined {
  return apiClient.defaults.headers.common['X-User-Id'] as string | undefined;
}

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response) {
      console.error('[API Error]', err.response.status, err.response.data);
    } else {
      console.error('[API Error]', err.message);
    }
    return Promise.reject(err);
  }
);
