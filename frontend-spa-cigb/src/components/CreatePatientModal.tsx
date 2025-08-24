import React, { useState } from 'react';
import './CreatePatientModal.css';

interface CreatePatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPatientCreated: (patient: any) => void;
}

const CreatePatientModal: React.FC<CreatePatientModalProps> = ({
  isOpen,
  onClose,
  onPatientCreated,
}) => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    diagnosis: '',
    admin_password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.admin_password) {
      setError('Debe ingresar su contraseña para verificar la operación');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { FileService } = await import('../services/fileService');
      
      const newPatient = await FileService.createPatient({
        first_name: formData.first_name,
        last_name: formData.last_name,
        diagnosis: formData.diagnosis,
        admin_password: formData.admin_password,
      });

      onPatientCreated(newPatient);
      onClose();
      resetForm();
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Error al crear el paciente. Intente nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: '',
      last_name: '',
      diagnosis: '',
      admin_password: '',
    });
    setError('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Agregar Nuevo Paciente</h2>
          <button 
            className="close-button" 
            onClick={handleClose}
            disabled={loading}
          >
            ✕
          </button>
        </div>

        <div className="info-section">
          <p><strong>Nota:</strong> Este formulario registra un nuevo paciente en el sistema para asociar archivos médicos.</p>
        </div>

        <form onSubmit={handleSubmit} className="patient-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">Nombre *</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                disabled={loading}
                placeholder="Nombre del paciente"
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Apellidos *</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
                disabled={loading}
                placeholder="Apellidos del paciente"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="diagnosis">Diagnóstico *</label>
            <textarea
              id="diagnosis"
              name="diagnosis"
              value={formData.diagnosis}
              onChange={handleChange}
              required
              disabled={loading}
              rows={3}
              placeholder="Diagnóstico inicial del paciente"
            />
          </div>

          <div className="form-group security-section">
            <label htmlFor="admin_password">Su contraseña para confirmar *</label>
            <input
              type="password"
              id="admin_password"
              name="admin_password"
              value={formData.admin_password}
              onChange={handleChange}
              required
              disabled={loading}
              placeholder="Ingrese su contraseña actual"
            />
            <small className="form-help">
              Por seguridad, debe confirmar su contraseña para crear un nuevo paciente
            </small>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="cancel-button"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="submit-button"
            >
              {loading ? 'Creando...' : 'Crear Paciente'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePatientModal;
