import React, { useState, useRef, useEffect } from 'react';
import { FileService, Patient, UploadedFile } from '../services/fileService';
import './FileUpload.css';

interface FileUploadProps {
  onUploadComplete?: () => void;
  selectedPatientId?: number;
  medicalRecordId?: number;
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onUploadComplete, 
  selectedPatientId,
  medicalRecordId 
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [descriptions, setDescriptions] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientId, setPatientId] = useState<number | null>(selectedPatientId || null);
  const [availablePhotos, setAvailablePhotos] = useState<UploadedFile[]>([]);
  const [selectedPhotoIds, setSelectedPhotoIds] = useState<number[]>([]);
  const [showPhotoSelector, setShowPhotoSelector] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPatients();
    if (selectedPatientId) {
      setPatientId(selectedPatientId);
    }
  }, [selectedPatientId]);

  useEffect(() => {
    if (patientId && medicalRecordId) {
      loadPatientPhotos();
    }
  }, [patientId, medicalRecordId]);

  const loadPatients = async () => {
    try {
      const patientsData = await FileService.getPatientsWithFiles();
      setPatients(patientsData);
    } catch (error) {
      console.error('Error al cargar pacientes:', error);
    }
  };

  const loadPatientPhotos = async () => {
    if (!patientId) return;
    
    try {
      const photos = await FileService.getPatientPhotos(patientId);
      setAvailablePhotos(photos);
    } catch (error) {
      console.error('Error al cargar fotos:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles(files);
      setDescriptions(new Array(files.length).fill(''));
      setMessage('');
      setError('');
      
      // Mostrar selector de fotos si se está subiendo una historia clínica
      const hasNonImageFiles = files.some(file => !file.type.startsWith('image/'));
      setShowPhotoSelector(hasNonImageFiles && !!medicalRecordId);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setSelectedFiles(files);
      setDescriptions(new Array(files.length).fill(''));
      setMessage('');
      setError('');
      
      const hasNonImageFiles = files.some(file => !file.type.startsWith('image/'));
      setShowPhotoSelector(hasNonImageFiles && !!medicalRecordId);
    }
  };

  const handleDescriptionChange = (index: number, value: string) => {
    const newDescriptions = [...descriptions];
    newDescriptions[index] = value;
    setDescriptions(newDescriptions);
  };

  const handlePhotoSelection = (photoId: number) => {
    setSelectedPhotoIds(prev => 
      prev.includes(photoId)
        ? prev.filter(id => id !== photoId)
        : [...prev, photoId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedFiles.length === 0) {
      setError('Por favor seleccione al menos un archivo');
      return;
    }

    if (!patientId) {
      setError('Por favor seleccione un paciente');
      return;
    }

    setUploading(true);
    setError('');
    setMessage('');

    try {
      const response = await FileService.uploadMultipleFiles(
        selectedFiles,
        patientId,
        descriptions.filter(desc => desc.trim() !== ''),
        medicalRecordId,
        selectedPhotoIds.length > 0 ? selectedPhotoIds : undefined
      );
      
      setMessage(response.message);
      clearForm();
      
      if (onUploadComplete) {
        onUploadComplete();
      }
      
      window.dispatchEvent(new CustomEvent('filesUploaded'));
      
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Error al subir los archivos. Intente nuevamente.');
      }
    } finally {
      setUploading(false);
    }
  };

  const clearForm = () => {
    setSelectedFiles([]);
    setDescriptions([]);
    setSelectedPhotoIds([]);
    setShowPhotoSelector(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return '🖼️';
    if (file.type === 'application/pdf') return '📄';
    if (file.type.includes('word') || file.type.includes('document')) return '📝';
    return '📎';
  };

  return (
    <div className="file-upload">
      <form onSubmit={handleSubmit}>
        {/* Selector de Paciente */}
        {!selectedPatientId && (
          <div className="form-group">
            <label htmlFor="patient">Paciente *</label>
            <select
              id="patient"
              value={patientId || ''}
              onChange={(e) => setPatientId(Number(e.target.value) || null)}
              required
              disabled={uploading}
            >
              <option value="">Seleccionar paciente...</option>
              {patients.map(patient => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Área de subida de archivos */}
        <div 
          className={`upload-area ${selectedFiles.length > 0 ? 'has-files' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
            multiple
            style={{ display: 'none' }}
            disabled={uploading}
          />
          
          <div className="upload-content">
            {selectedFiles.length > 0 ? (
              <div className="files-list">
                <h4>Archivos seleccionados ({selectedFiles.length}):</h4>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">{getFileIcon(file)}</span>
                      <div className="file-details">
                        <p className="file-name">{file.name}</p>
                        <p className="file-size">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <input
                      type="text"
                      placeholder="Descripción (opcional)"
                      value={descriptions[index] || ''}
                      onChange={(e) => handleDescriptionChange(index, e.target.value)}
                      className="file-description"
                      disabled={uploading}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="upload-prompt">
                <div className="upload-icon">⬆️</div>
                <p>Arrastra y suelta archivos aquí o <span>haz clic para seleccionar</span></p>
                <p className="supported-formats">
                  Formatos soportados: JPG, PNG, PDF, DOC, DOCX, TXT
                </p>
                <p className="multiple-files-notice">
                  ✨ ¡Ahora puedes subir múltiples archivos a la vez!
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Selector de fotos para asociar con historia clínica */}
        {showPhotoSelector && availablePhotos.length > 0 && (
          <div className="photo-selector">
            <h4>Asociar fotos existentes a esta historia clínica:</h4>
            <div className="photos-grid">
              {availablePhotos.map(photo => (
                <div 
                  key={photo.id} 
                  className={`photo-item ${selectedPhotoIds.includes(photo.id) ? 'selected' : ''}`}
                  onClick={() => handlePhotoSelection(photo.id)}
                >
                  <div className="photo-preview">
                    <img 
                      src={`/api/files/${photo.id}/download`} 
                      alt={photo.original_filename}
                      style={{ width: '60px', height: '60px', objectFit: 'cover' }}
                    />
                  </div>
                  <p className="photo-name">{photo.original_filename}</p>
                  {selectedPhotoIds.includes(photo.id) && (
                    <div className="selection-indicator">✓</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        <div className="upload-actions">
          <button
            type="button"
            onClick={clearForm}
            disabled={uploading || selectedFiles.length === 0}
            className="clear-button"
          >
            Limpiar
          </button>
          
          <button
            type="submit"
            disabled={uploading || selectedFiles.length === 0 || !patientId}
            className="upload-button"
          >
            {uploading ? 'Subiendo...' : `Subir ${selectedFiles.length} archivo(s)`}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;
            accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
            style={{ display: 'none' }}
            disabled={uploading}
          />
          
          <div className="upload-content">
            {selectedFile ? (
              <div className="file-info">
                <div className="file-icon">📄</div>
                <div className="file-details">
                  <p className="file-name">{selectedFile.name}</p>
                  <p className="file-size">{formatFileSize(selectedFile.size)}</p>
                </div>
              </div>
            ) : (
              <div className="upload-prompt">
                <div className="upload-icon">⬆️</div>
                <p>Arrastra y suelta un archivo aquí o <span>haz clic para seleccionar</span></p>
                <p className="supported-formats">
                  Formatos soportados: JPG, PNG, PDF, DOC, DOCX, TXT
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description">Descripción (opcional)</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Agregue una descripción para el archivo"
            rows={3}
            disabled={uploading}
          />
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        <div className="upload-actions">
          <button
            type="button"
            onClick={() => {
              setSelectedFile(null);
              setDescription('');
              setError('');
              setMessage('');
              if (fileInputRef.current) {
                fileInputRef.current.value = '';
              }
            }}
            disabled={uploading || !selectedFile}
            className="clear-button"
          >
            Limpiar
          </button>
          
          <button
            type="submit"
            disabled={uploading || !selectedFile}
            className="upload-button"
          >
            {uploading ? 'Subiendo...' : 'Subir Archivo'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;
