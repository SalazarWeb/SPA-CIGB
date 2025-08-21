# FastAPI Backend - SPA CIGB

## Descripción

Backend desarrollado con FastAPI para un sistema de gestión de historias clínicas con las siguientes funcionalidades:

- **Autenticación JWT**: Login seguro con tokens
- **Gestión de usuarios**: Pacientes, doctores y administradores
- **Historias clínicas**: Creación, edición y consulta de registros médicos
- **Subida de archivos**: Imágenes y documentos asociados a historias clínicas
- **Control de permisos**: Diferentes niveles de acceso según el rol

## Estructura del proyecto

```
backend-spa-cigb/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación principal FastAPI
│   ├── api/                 # Rutas de la API
│   │   ├── __init__.py
│   │   ├── auth.py          # Autenticación y autorización
│   │   ├── users.py         # Gestión de usuarios
│   │   ├── medical_records.py # Historias clínicas
│   │   └── file_upload.py   # Subida de archivos
│   ├── core/                # Configuración central
│   │   ├── __init__.py
│   │   ├── config.py        # Configuraciones
│   │   ├── database.py      # Conexión a base de datos
│   │   └── security.py      # Funciones de seguridad
│   ├── models/              # Modelos de base de datos
│   │   ├── __init__.py
│   │   └── models.py        # Modelos SQLAlchemy
│   ├── schemas/             # Esquemas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py          # Esquemas de usuario
│   │   ├── medical_record.py # Esquemas de historias clínicas
│   │   └── file.py          # Esquemas de archivos
│   └── services/            # Lógica de negocio
│       ├── __init__.py
│       ├── user_service.py
│       ├── medical_record_service.py
│       └── file_service.py
├── alembic/                 # Migraciones de base de datos
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── uploads/                 # Directorio para archivos subidos
├── requirements.txt         # Dependencias
├── alembic.ini             # Configuración de Alembic
├── .env.example            # Variables de entorno de ejemplo
├── .gitignore
├── run.py                  # Script de inicio
└── README.md
```

## Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate     # En Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar el archivo `.env` con tus configuraciones:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/spa_cigb_db
SECRET_KEY=tu-clave-secreta-muy-segura
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Configurar base de datos PostgreSQL

Crear la base de datos:

```sql
CREATE DATABASE spa_cigb_db;
CREATE DATABASE spa_cigb_test_db;
```

### 5. Ejecutar migraciones

```bash
alembic upgrade head
```

## Uso

### Iniciar el servidor

```bash
# Opción 1: Usando el script run.py
python run.py

# Opción 2: Usando uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

### Documentación de la API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints principales

#### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/register` - Registrar usuario
- `GET /api/auth/me` - Información del usuario actual
- `POST /api/auth/logout` - Cerrar sesión

#### Usuarios
- `GET /api/users/` - Listar usuarios
- `GET /api/users/patients` - Listar pacientes
- `GET /api/users/doctors` - Listar doctores
- `GET /api/users/{user_id}` - Obtener usuario
- `PUT /api/users/{user_id}` - Actualizar usuario

#### Historias clínicas
- `GET /api/medical-records/` - Listar registros médicos
- `POST /api/medical-records/` - Crear registro médico
- `GET /api/medical-records/{record_id}` - Obtener registro específico
- `PUT /api/medical-records/{record_id}` - Actualizar registro
- `DELETE /api/medical-records/{record_id}` - Eliminar registro

#### Archivos
- `POST /api/files/upload` - Subir archivo
- `GET /api/files/` - Listar archivos
- `GET /api/files/{file_id}` - Información del archivo
- `GET /api/files/{file_id}/download` - Descargar archivo
- `DELETE /api/files/{file_id}` - Eliminar archivo

## Roles y permisos

### Paciente
- Ver sus propias historias clínicas
- Subir archivos personales
- Actualizar su perfil

### Doctor
- Crear y editar historias clínicas de pacientes
- Ver lista de pacientes
- Subir archivos asociados a historias clínicas
- Actualizar su perfil

### Administrador
- Acceso completo a todos los recursos
- Gestionar usuarios
- Ver todas las historias clínicas

## Base de datos

### Modelos principales

- **User**: Usuarios del sistema (pacientes, doctores, admins)
- **MedicalRecord**: Historias clínicas
- **UploadedFile**: Archivos subidos al sistema

### Migraciones

Crear nueva migración:
```bash
alembic revision --autogenerate -m "Descripción del cambio"
```

Aplicar migraciones:
```bash
alembic upgrade head
```

## Desarrollo

### Crear usuario administrador inicial

```python
# Ejecutar en una consola de Python
from app.core.database import SessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate

db = SessionLocal()
user_service = UserService(db)

admin_user = UserCreate(
    username="admin",
    email="admin@example.com",
    password="admin123",
    first_name="Admin",
    last_name="User",
    role="admin"
)

user_service.create_user(admin_user)
db.close()
```

### Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

## Deployment

### Usando Docker

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Variables de entorno de producción

```env
ENVIRONMENT=production
SECRET_KEY=clave-secreta-muy-segura-para-produccion
DATABASE_URL=postgresql://user:pass@db:5432/spa_cigb_db
ALLOWED_ORIGINS=https://tudominio.com
```

## Contribuir

1. Fork del repositorio
2. Crear rama para nueva feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la licencia MIT.
  <!--[![Backers on Open Collective](https://opencollective.com/nest/backers/badge.svg)](https://opencollective.com/nest#backer)
  [![Sponsors on Open Collective](https://opencollective.com/nest/sponsors/badge.svg)](https://opencollective.com/nest#sponsor)-->

## Description

[Nest](https://github.com/nestjs/nest) framework TypeScript starter repository.

## Project setup

```bash
$ npm install
```

## Compile and run the project

```bash
# development
$ npm run start

# watch mode
$ npm run start:dev

# production mode
$ npm run start:prod
```

## Run tests

```bash
# unit tests
$ npm run test

# e2e tests
$ npm run test:e2e

# test coverage
$ npm run test:cov
```

## Deployment

When you're ready to deploy your NestJS application to production, there are some key steps you can take to ensure it runs as efficiently as possible. Check out the [deployment documentation](https://docs.nestjs.com/deployment) for more information.

If you are looking for a cloud-based platform to deploy your NestJS application, check out [Mau](https://mau.nestjs.com), our official platform for deploying NestJS applications on AWS. Mau makes deployment straightforward and fast, requiring just a few simple steps:

```bash
$ npm install -g @nestjs/mau
$ mau deploy
```

With Mau, you can deploy your application in just a few clicks, allowing you to focus on building features rather than managing infrastructure.

## Resources

Check out a few resources that may come in handy when working with NestJS:

- Visit the [NestJS Documentation](https://docs.nestjs.com) to learn more about the framework.
- For questions and support, please visit our [Discord channel](https://discord.gg/G7Qnnhy).
- To dive deeper and get more hands-on experience, check out our official video [courses](https://courses.nestjs.com/).
- Deploy your application to AWS with the help of [NestJS Mau](https://mau.nestjs.com) in just a few clicks.
- Visualize your application graph and interact with the NestJS application in real-time using [NestJS Devtools](https://devtools.nestjs.com).
- Need help with your project (part-time to full-time)? Check out our official [enterprise support](https://enterprise.nestjs.com).
- To stay in the loop and get updates, follow us on [X](https://x.com/nestframework) and [LinkedIn](https://linkedin.com/company/nestjs).
- Looking for a job, or have a job to offer? Check out our official [Jobs board](https://jobs.nestjs.com).

## Support

Nest is an MIT-licensed open source project. It can grow thanks to the sponsors and support by the amazing backers. If you'd like to join them, please [read more here](https://docs.nestjs.com/support).

## Stay in touch

- Author - [Kamil Myśliwiec](https://twitter.com/kammysliwiec)
- Website - [https://nestjs.com](https://nestjs.com/)
- Twitter - [@nestframework](https://twitter.com/nestframework)

## License

Nest is [MIT licensed](https://github.com/nestjs/nest/blob/master/LICENSE).
