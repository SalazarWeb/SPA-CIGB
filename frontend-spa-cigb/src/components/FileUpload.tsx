import React, { useState, useRef } from 'react';
import { FileService } from '../services/fileService';
import './FileUpload.css';

const FileUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
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
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      setSelectedFile(files[0]);
      setMessage('');
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError('Por favor seleccione un archivo');
      return;
    }

    setUploading(true);
    setError('');
    setMessage('');

    try {
      const response = await FileService.uploadFile(
        selectedFile,
        description || undefined
      );
      
      setMessage(response.message);
      setSelectedFile(null);
      setDescription('');
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Trigger refresh of file list (you can implement this with a custom event or context)
      window.dispatchEvent(new CustomEvent('fileUploaded'));
      
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Error al subir el archivo. Intente nuevamente.');
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

  return (
    <div className="file-upload">
      <form onSubmit={handleSubmit}>
        <div 
          className={`upload-area ${selectedFile ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
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
