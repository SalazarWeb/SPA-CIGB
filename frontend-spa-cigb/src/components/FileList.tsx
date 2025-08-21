import React, { useState, useEffect } from 'react';
import { FileService, UploadedFile } from '../services/fileService';
import './FileList.css';

const FileList: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadFiles = async () => {
    try {
      setLoading(true);
      const filesData = await FileService.getFiles();
      setFiles(filesData);
      setError('');
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Error al cargar los archivos');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();

    // Listen for file upload events to refresh the list
    const handleFileUploaded = () => {
      loadFiles();
    };

    window.addEventListener('fileUploaded', handleFileUploaded);
    
    return () => {
      window.removeEventListener('fileUploaded', handleFileUploaded);
    };
  }, []);

  const handleDownload = async (fileId: number, filename: string) => {
    try {
      const blob = await FileService.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error al descargar el archivo:', error);
    }
  };

  const handleDelete = async (fileId: number) => {
    if (!window.confirm('¿Está seguro de que desea eliminar este archivo?')) {
      return;
    }

    try {
      await FileService.deleteFile(fileId);
      await loadFiles(); // Refresh the list
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Error al eliminar el archivo');
      }
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
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
    if (mimeType.includes('text')) return '📃';
    return '📁';
  };

  if (loading) {
    return (
      <div className="file-list-loading">
        <div className="loading-spinner"></div>
        <p>Cargando archivos...</p>
      </div>
    );
  }

  return (
    <div className="file-list">
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {files.length === 0 ? (
        <div className="no-files">
          <div className="no-files-icon">📂</div>
          <p>No hay archivos subidos aún</p>
          <p className="no-files-subtitle">Suba su primer archivo usando el formulario de arriba</p>
        </div>
      ) : (
        <div className="files-grid">
          {files.map((file) => (
            <div key={file.id} className="file-card">
              <div className="file-header">
                <div className="file-icon-large">
                  {getFileIcon(file.mime_type)}
                </div>
                <div className="file-info">
                  <h3 className="file-title">{file.original_filename}</h3>
                  <p className="file-size">{formatFileSize(file.file_size)}</p>
                </div>
              </div>

              {file.description && (
                <div className="file-description">
                  <p>{file.description}</p>
                </div>
              )}

              <div className="file-meta">
                <p className="file-date">
                  Subido: {formatDate(file.created_at)}
                </p>
                <p className="file-type">
                  Tipo: {file.mime_type}
                </p>
              </div>

              <div className="file-actions">
                <button
                  onClick={() => handleDownload(file.id, file.original_filename)}
                  className="download-button"
                  title="Descargar archivo"
                >
                  ⬇️ Descargar
                </button>
                <button
                  onClick={() => handleDelete(file.id)}
                  className="delete-button"
                  title="Eliminar archivo"
                >
                  🗑️ Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="files-footer">
        <button onClick={loadFiles} className="refresh-button">
          🔄 Actualizar
        </button>
        <p className="files-count">
          Total: {files.length} archivo{files.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
};

export default FileList;
