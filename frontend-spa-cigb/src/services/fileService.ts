import api from './api';

export interface UploadedFile {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  description?: string;
  file_type: 'photo' | 'medical_record';
  user_id: number;
  patient_id: number;
  medical_record_id?: number;
  created_at: string;
  patient_name?: string;
  uploader_name?: string;
}

export interface FileUploadResponse {
  message: string;
  files: UploadedFile[];
}

export interface Patient {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  address?: string;
  role: string;
}

export class FileService {
  static async uploadFile(
    file: File,
    patientId: number,
    description?: string,
    medicalRecordId?: number
  ): Promise<FileUploadResponse> {
    return this.uploadMultipleFiles(
      [file],
      patientId,
      description ? [description] : undefined,
      medicalRecordId
    );
  }

  static async uploadMultipleFiles(
    files: File[],
    patientId: number,
    descriptions?: string[],
    medicalRecordId?: number,
    photoIds?: number[]
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });
    
    formData.append('patient_record_id', patientId.toString());
    
    if (descriptions) {
      descriptions.forEach(desc => {
        if (desc) formData.append('descriptions', desc);
      });
    }
    
    if (medicalRecordId) {
      formData.append('medical_record_id', medicalRecordId.toString());
    }
    
    if (photoIds) {
      photoIds.forEach(id => {
        formData.append('photo_ids', id.toString());
      });
    }

    const response = await api.post('/files/upload-multiple-to-patient-record', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }

  static async getFiles(
    skip: number = 0,
    limit: number = 100,
    patientId?: number,
    medicalRecordId?: number,
    fileType?: 'photo' | 'medical_record'
  ): Promise<UploadedFile[]> {
    const params: any = { skip, limit };
    
    if (patientId) {
      params.patient_id = patientId;
    }
    
    if (medicalRecordId) {
      params.medical_record_id = medicalRecordId;
    }
    
    if (fileType) {
      params.file_type = fileType;
    }

    const response = await api.get('/files/', { params });
    return response.data;
  }
  
  static async getPatientsWithFiles(): Promise<Patient[]> {
    const response = await api.get('/files/patients');
    return response.data;
  }

  static async getPatients(): Promise<Patient[]> {
    const response = await api.get('/patients/');
    return response.data;
  }

  static async createPatient(patientData: {
    first_name: string;
    last_name: string;
    diagnosis?: string;
    admin_password: string;
  }): Promise<Patient> {
    const response = await api.post('/patients/', {
      ...patientData,
    });
    return response.data;
  }
  
  static async getPatientPhotos(patientId: number): Promise<UploadedFile[]> {
    return this.getFiles(0, 1000, patientId, undefined, 'photo');
  }
  
  static async getPatientMedicalRecords(patientId: number): Promise<UploadedFile[]> {
    return this.getFiles(0, 1000, patientId, undefined, 'medical_record');
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
