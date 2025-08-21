import React, { useState, useEffect } from 'react';
import { FileService, UploadedFile, Patient } from '../services/fileService';
import FileUpload from './FileUpload';
import './PatientFileManager.css';

interface PatientFileManagerProps {
  selectedPatientId?: number;
}

const PatientFileManager: React.FC<PatientFileManagerProps> = ({ selectedPatientId }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [photos, setPhotos] = useState<UploadedFile[]>([]);
  const [medicalRecords, setMedicalRecords] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'photos' | 'medical_records' | 'upload'>('photos');

  useEffect(() => {
    loadPatients();
    
    // Escuchar evento de archivos subidos
    const handleFilesUploaded = () => {
      if (selectedPatient) {
        loadPatientFiles(selectedPatient.id);
      }
    };
    
    window.addEventListener('filesUploaded', handleFilesUploaded);
    return () => window.removeEventListener('filesUploaded', handleFilesUploaded);
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      const patient = patients.find(p => p.id === selectedPatientId);
      if (patient) {
        setSelectedPatient(patient);
        loadPatientFiles(selectedPatientId);
      }
    }
  }, [selectedPatientId, patients]);

  const loadPatients = async () => {
    try {
      const patientsData = await FileService.getPatientsWithFiles();
      setPatients(patientsData);
    } catch (error) {
      setError('Error al cargar pacientes');
      console.error(error);
    }
  };

  const loadPatientFiles = async (patientId: number) => {
    setLoading(true);
    try {
      const [photosData, medicalRecordsData] = await Promise.all([
        FileService.getPatientPhotos(patientId),
        FileService.getPatientMedicalRecords(patientId)
      ]);
      
      setPhotos(photosData);
      setMedicalRecords(medicalRecordsData);
      setError('');
    } catch (error) {
      setError('Error al cargar archivos del paciente');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePatientSelect = (patient: Patient) => {
    setSelectedPatient(patient);
    loadPatientFiles(patient.id);
  };

  const handleDownload = async (fileId: number, filename: string) => {
    try {
      const blob = await FileService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error al descargar archivo:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="patient-file-manager">
      <div className="sidebar">
        <h3>Pacientes</h3>
        <div className="patients-list">
          {patients.map(patient => (
            <div
              key={patient.id}
              className={`patient-item ${selectedPatient?.id === patient.id ? 'selected' : ''}`}
              onClick={() => handlePatientSelect(patient)}
            >
              <div className="patient-info">
                <h4>{patient.first_name} {patient.last_name}</h4>
                <p>{patient.email}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="main-content">
        {selectedPatient ? (
          <>
            <div className="patient-header">
              <h2>{selectedPatient.first_name} {selectedPatient.last_name}</h2>
              <p>Archivos del paciente</p>
            </div>

            <div className="tabs">
              <button
                className={`tab ${activeTab === 'photos' ? 'active' : ''}`}
                onClick={() => setActiveTab('photos')}
              >
                Fotos ({photos.length})
              </button>
              <button
                className={`tab ${activeTab === 'medical_records' ? 'active' : ''}`}
                onClick={() => setActiveTab('medical_records')}
              >
                Historias Clínicas ({medicalRecords.length})
              </button>
              <button
                className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('upload')}
              >
                Subir Archivos
              </button>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {loading && (
              <div className="loading">
                Cargando archivos...
              </div>
            )}

            {activeTab === 'photos' && (
              <div className="files-grid">
                {photos.length === 0 ? (
                  <p className="no-files">No hay fotos para este paciente</p>
                ) : (
                  photos.map(photo => (
                    <div key={photo.id} className="file-card photo-card">
                      <div className="file-preview">
                        <img
                          src={`/api/files/${photo.id}/download`}
                          alt={photo.original_filename}
                          className="photo-thumbnail"
                        />
                      </div>
                      <div className="file-info">
                        <h4>{photo.original_filename}</h4>
                        <p className="file-meta">
                          {formatFileSize(photo.file_size)} • {formatDate(photo.created_at)}
                        </p>
                        {photo.description && (
                          <p className="file-description">{photo.description}</p>
                        )}
                        <button
                          onClick={() => handleDownload(photo.id, photo.original_filename)}
                          className="download-btn"
                        >
                          Descargar
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'medical_records' && (
              <div className="files-list">
                {medicalRecords.length === 0 ? (
                  <p className="no-files">No hay historias clínicas para este paciente</p>
                ) : (
                  medicalRecords.map(record => (
                    <div key={record.id} className="file-card record-card">
                      <div className="file-icon">
                        📄
                      </div>
                      <div className="file-info">
                        <h4>{record.original_filename}</h4>
                        <p className="file-meta">
                          {formatFileSize(record.file_size)} • {formatDate(record.created_at)}
                        </p>
                        {record.description && (
                          <p className="file-description">{record.description}</p>
                        )}
                        <div className="file-actions">
                          <button
                            onClick={() => handleDownload(record.id, record.original_filename)}
                            className="download-btn"
                          >
                            Descargar
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'upload' && (
              <div className="upload-section">
                <FileUpload
                  selectedPatientId={selectedPatient.id}
                  onUploadComplete={() => {
                    loadPatientFiles(selectedPatient.id);
                    setActiveTab('photos');
                  }}
                />
              </div>
            )}
          </>
        ) : (
          <div className="no-patient-selected">
            <h3>Seleccione un paciente</h3>
            <p>Elija un paciente de la lista para ver sus archivos</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientFileManager;
