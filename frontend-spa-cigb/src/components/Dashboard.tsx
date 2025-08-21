import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import FileUpload from './FileUpload';
import FileList from './FileList';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

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

      <main className="dashboard-main">
        <div className="dashboard-container">
          <div className="dashboard-section">
            <h2>Subir Archivos</h2>
            <p>Suba historias clínicas y fotos al sistema</p>
            <FileUpload />
          </div>

          <div className="dashboard-section">
            <h2>Mis Archivos</h2>
            <p>Lista de archivos subidos</p>
            <FileList />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
