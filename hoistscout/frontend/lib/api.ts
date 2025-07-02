import axios from 'axios';
import { getSession } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password })),
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post('/api/auth/register', data),
  refresh: (refreshToken: string) =>
    api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  getProfile: () => api.get('/api/auth/profile'),
};

// Websites API
export const websitesApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/api/websites', { params }),
  create: (data: any) => api.post('/api/websites', data),
  get: (id: number) => api.get(`/api/websites/${id}`),
  update: (id: number, data: any) => api.put(`/api/websites/${id}`, data),
  delete: (id: number) => api.delete(`/api/websites/${id}`),
  test: (id: number) => api.post(`/api/websites/${id}/test`),
};

// Opportunities API
export const opportunitiesApi = {
  search: (params: {
    query?: string;
    category?: string;
    location?: string;
    min_value?: number;
    max_value?: number;
    deadline_after?: string;
    deadline_before?: string;
    website_ids?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/api/opportunities', { params }),
  get: (id: number) => api.get(`/api/opportunities/${id}`),
  stats: () => api.get('/api/opportunities/stats'),
  export: (data: any) => api.post('/api/opportunities/export', data),
};

// Jobs API
export const jobsApi = {
  create: (data: { website_id: number; job_type?: string; priority?: number }) =>
    api.post('/api/scraping/jobs', data),
  list: (params?: {
    status?: string;
    website_id?: number;
    limit?: number;
    offset?: number;
  }) => api.get('/api/scraping/jobs', { params }),
  get: (id: number) => api.get(`/api/scraping/jobs/${id}`),
  cancel: (id: number) => api.post(`/api/scraping/jobs/${id}/cancel`),
  logs: (id: number) => api.get(`/api/scraping/jobs/${id}/logs`),
};

// Health API
export const healthApi = {
  check: () => api.get('/api/health'),
  ready: () => api.get('/api/health/ready'),
  live: () => api.get('/api/health/live'),
};