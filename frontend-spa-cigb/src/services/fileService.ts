import api from './api';

export interface UploadedFile {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  description?: string;
  user_id: number;
  medical_record_id?: number;
  created_at: string;
}

export interface FileUploadResponse {
  message: string;
  file: UploadedFile;
}

export class FileService {
  static async uploadFile(
    file: File,
    description?: string,
    medicalRecordId?: number
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (description) {
      formData.append('description', description);
    }
    
    if (medicalRecordId) {
      formData.append('medical_record_id', medicalRecordId.toString());
    }

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }

  static async getFiles(
    skip: number = 0,
    limit: number = 100,
    medicalRecordId?: number
  ): Promise<UploadedFile[]> {
    const params: any = { skip, limit };
    
    if (medicalRecordId) {
      params.medical_record_id = medicalRecordId;
    }

    const response = await api.get('/files/', { params });
    return response.data;
  }

  static async getFileInfo(fileId: number): Promise<UploadedFile> {
    const response = await api.get(`/files/${fileId}`);
    return response.data;
  }

  static async downloadFile(fileId: number): Promise<Blob> {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  static async deleteFile(fileId: number): Promise<void> {
    await api.delete(`/files/${fileId}`);
  }
}
