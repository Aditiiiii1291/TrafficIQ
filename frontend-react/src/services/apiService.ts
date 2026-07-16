import client from '../api/client';
import type {
  UploadResponse,
  ProcessRequest,
  ProcessingResult,
  AnalyticsResponse,
  HistoryResponse,
  HistoricalRecordModel
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
}
