import { apiClient } from './client';

export interface LoginRequest {
  login_id: string;
  password: string;
}

// 로그인·회원가입 성공 응답 구조 동일
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  role: string;
  site_id: number | null;
}

export interface MeResponse {
  user_id: number;
  role: string;
  site_id: number | null;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export async function loginUser(body: LoginRequest): Promise<LoginResponse> {
  const res = await apiClient.post('/api/v1/auth/login', body);
  return res.data;
}

export async function getMe(): Promise<MeResponse> {
  const res = await apiClient.get('/api/v1/auth/me');
  return res.data;
}

// 성공 시 201 Created + LoginResponse 구조 반환
export async function registerUser(body: RegisterRequest): Promise<LoginResponse> {
  const res = await apiClient.post('/api/v1/auth/register', body);
  return res.data;
}
