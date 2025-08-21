import React, { useState, useRef, useEffect } from 'react';
import { FileService } from '../services/fileService';
import './FileUpload.css';

interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  username: string;
}

const FileUpload: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [descriptions, setDescriptions] = useState<string[]>([]);
  const [patientId, setPatientId] = useState<number | ''>('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const response = await FileService.getPatients();
      setPatients(response);
    } catch (error) {
      console.error('Error loading patients:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles(files);
      setDescriptions(new Array(files.length).fill(''));
      setMessage('');
      setError('');
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
    }
  };

  const handleDescriptionChange = (index: number, value: string) => {
    const newDescriptions = [...descriptions];
    newDescriptions[index] = value;
    setDescriptions(newDescriptions);
  };

  const removeFile = (index: number) => {
    const newFiles = [...selectedFiles];
    const newDescriptions = [...descriptions];
    
    newFiles.splice(index, 1);
    newDescriptions.splice(index, 1);
    
    setSelectedFiles(newFiles);
    setDescriptions(newDescriptions);
  };

  const clearForm = () => {
    setSelectedFiles([]);
    setDescriptions([]);
    setPatientId('');
    setError('');
    setMessage('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
        Number(patientId),
        descriptions.filter(desc => desc.trim() !== '')
      );
      
      setMessage(response.message);
      clearForm();
      
      // Trigger refresh of file list
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

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileTypeIcon = (file: File) => {
    const type = file.type;
    if (type.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    if (type.includes('document') || type.includes('word')) return '📝';
    return '📎';
  };

  return (
    <div className="file-upload">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="patient">Paciente *</label>
          <select
            id="patient"
            value={patientId}
            onChange={(e) => setPatientId(Number(e.target.value))}
            disabled={uploading}
            required
          >
            <option value="">Seleccionar paciente...</option>
            {patients.map(patient => (
              <option key={patient.id} value={patient.id}>
                {patient.first_name} {patient.last_name} ({patient.username})
              </option>
            ))}
          </select>
        </div>

        <div 
          className={`upload-area ${selectedFiles.length > 0 ? 'has-files' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
            style={{ display: 'none' }}
            disabled={uploading}
          />
          
          <div className="upload-content">
            {selectedFiles.length > 0 ? (
              <div className="files-list">
                <h4>Archivos seleccionados ({selectedFiles.length})</h4>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <div className="file-icon">{getFileTypeIcon(file)}</div>
                      <div className="file-details">
                        <p className="file-name">{file.name}</p>
                        <p className="file-size">{formatFileSize(file.size)}</p>
                        <input
                          type="text"
                          placeholder="Descripción (opcional)"
                          value={descriptions[index] || ''}
                          onChange={(e) => handleDescriptionChange(index, e.target.value)}
                          className="file-description"
                          disabled={uploading}
                        />
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(index);
                        }}
                        className="remove-file"
                        disabled={uploading}
                      >
                        ✕
                      </button>
                    </div>
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
              </div>
            )}
          </div>
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
