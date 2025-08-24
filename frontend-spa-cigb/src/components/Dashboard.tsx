import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import FileUpload from './FileUpload';
import FileList from './FileList';
import PatientFileManager from './PatientFileManager';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeView, setActiveView] = useState<'patients' | 'upload' | 'files'>('patients');

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Sistema de Gestión - CIGB</h1>
          <div className="user-info">
            <span>Bienvenido, {user?.first_name} {user?.last_name}</span>
            <button onClick={handleLogout} className="logout-button">
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      <nav className="dashboard-nav">
        <button 
          className={`nav-button ${activeView === 'patients' ? 'active' : ''}`}
          onClick={() => setActiveView('patients')}
        >
          📁 Archivos por Paciente
        </button>
        <button 
          className={`nav-button ${activeView === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveView('upload')}
        >
          ⬆️ Subir Archivos
        </button>
        <button 
          className={`nav-button ${activeView === 'files' ? 'active' : ''}`}
          onClick={() => setActiveView('files')}
        >
          📄 Mis Archivos
        </button>
      </nav>

      <main className="dashboard-main">
        {activeView === 'patients' && (
          <div className="dashboard-view">
            <PatientFileManager />
          </div>
        )}

        {activeView === 'upload' && (
          <div className="dashboard-view">
            <div className="dashboard-section">
              <h2>Subir Archivos</h2>
              <p>Suba historias clínicas y fotos al sistema.</p>
              <FileUpload />
            </div>
          </div>
        )}

        {activeView === 'files' && (
          <div className="dashboard-view">
            <div className="dashboard-section">
              <h2>Mis Archivos</h2>
              <p>Lista de archivos subidos por esta cuenta.</p>
              <FileList />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
