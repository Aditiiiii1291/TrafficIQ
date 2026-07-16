import client from '../api/client';
import type {
  UploadResponse,
  ProcessRequest,
  ProcessingResult,
  AnalyticsResponse,
  HistoryResponse,
  HistoricalRecordModel,
  UserCreate,
  UserLogin,
  UserUpdate,
  UserPasswordChange,
  UserResponse,
  TokenResponse
} from '../types';

export class ApiService {
  static async uploadVideo(file: File, onUploadProgress?: (progressEvent: any) => void): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await client.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress
    });
    return response.data;
  }

  static async processVideo(request: ProcessRequest): Promise<ProcessingResult> {
    const response = await client.post<ProcessingResult>('/process', request);
    return response.data;
  }

  static async getAnalytics(): Promise<AnalyticsResponse> {
    const response = await client.get<AnalyticsResponse>('/analytics');
    return response.data;
  }

  static async getHistory(filters: {
    date_filter?: string;
    congestion_level?: string;
    recommendation?: string;
  } = {}): Promise<HistoryResponse> {
    const response = await client.get<HistoryResponse>('/history', {
      params: {
        date_filter: filters.date_filter || undefined,
        congestion_level: filters.congestion_level || 'ALL',
        recommendation: filters.recommendation || 'ALL',
      },
    });
    return response.data;
  }

  static async getResult(id: string): Promise<HistoricalRecordModel> {
    const response = await client.get<HistoricalRecordModel>(`/results/${encodeURIComponent(id)}`);
    return response.data;
  }

  static async register(user: UserCreate): Promise<UserResponse> {
    const response = await client.post<UserResponse>('/auth/register', user);
    return response.data;
  }

  static async login(credentials: UserLogin): Promise<TokenResponse> {
    const response = await client.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  }

  static async logout(): Promise<any> {
    const response = await client.post('/auth/logout');
    return response.data;
  }

  static async getMe(): Promise<UserResponse> {
    const response = await client.get<UserResponse>('/auth/me');
    return response.data;
  }

  static async updateProfile(profile: UserUpdate): Promise<UserResponse> {
    const response = await client.put<UserResponse>('/auth/profile', profile);
    return response.data;
  }

  static async changePassword(pwd: UserPasswordChange): Promise<any> {
    const response = await client.put('/auth/change-password', pwd);
    return response.data;
  }

  static async deleteAccount(): Promise<any> {
    const response = await client.delete('/auth/account');
    return response.data;
  }
}
