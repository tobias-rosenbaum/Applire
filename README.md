# Applire

<div align="center">

![Applire - AI-Powered CV Optimization](https://cdn.simtheory.ai/image/upload/v1775325052/user_7324/ai-document-processing_492199c1.png)

**Precise. Confident. Future-Ready.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/react-18.x-61dafb.svg)](https://reactjs.org/)

</div>

---

## 🎯 What is Applire?

**Applire** is an AI-powered CV optimization platform that transforms the job application process. Upload your CVs, paste a job description, and let AI create perfectly tailored application documents in seconds.

### The Problem

Job seekers waste **hours** manually adapting CVs for each application:
- 🕐 **Time-consuming**: Rewriting CVs for every role
- 😰 **Stressful**: Uncertainty about what to include/exclude
- 🎯 **Inefficient**: Missing key requirements in job descriptions
- 🌍 **Cultural barriers**: Adapting CVs across different market conventions

### The Solution

Applire uses advanced AI to:
- ✨ **Merge multiple CVs** into a comprehensive master profile
- 🎯 **Analyze job descriptions** and detect skill gaps
- 📊 **Calculate match scores** with transparent gap analysis
- 🚀 **Generate tailored CVs** optimized for ATS systems
- 🌍 **Adapt cultural conventions** (e.g., Indian → DACH pharma standards)
- 🔒 **Privacy-first approach** - your data stays yours

---

## 🚀 Key Features

### For Job Seekers

- **🔄 Multi-CV Consolidation**: Upload 2-4 CVs and automatically merge them into a rich master profile
- **🎯 Smart Gap Detection**: AI identifies missing requirements and suggests improvements
- **📈 Match Scoring**: Get transparent 0-100% match scores with detailed explanations
- **💬 Conversational Interview**: Answer a few questions to close gaps and boost your score
- **🌍 Cultural Adaptation**: Automatic detection and adaptation of CV conventions across markets
- **📄 One-Click Generation**: Create perfectly tailored CVs in seconds

### For Recruiters (B2B)

- **📊 Batch Match Matrix**: Analyze multiple candidates against multiple job descriptions
- **🎯 Kandidatenprofile**: Generate standardized candidate profiles for client submissions
- **📋 Pipeline Management**: Kanban-style tracking of submissions and placements
- **⚡ Efficiency Gains**: Reduce time-to-submission from hours to minutes

---

## 🏗️ Tech Stack

### Backend
- **Python 3.11+**: Modern Python with type hints
- **Django 5.x**: Robust web framework with ORM
- **PostgreSQL**: Relational database for structured data
- **Celery**: Asynchronous task processing
- **Redis**: Caching and message broker

### Frontend
- **React 18.x**: Modern UI with hooks
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tooling

### AI/ML
- **OpenAI GPT-4**: Advanced language understanding
- **LangChain**: LLM orchestration
- **Custom NLP Pipeline**: CV parsing and entity extraction

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Local development orchestration
- **GitHub Actions**: CI/CD pipeline
- **AWS/Azure**: Cloud deployment (configurable)

---

## 📦 Installation

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Redis 7+**
- **Docker & Docker Compose** (recommended)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/applire.git
cd applire

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# - OPENAI_API_KEY=your_key_here
# - DATABASE_URL=postgresql://...

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Manual Setup (Development)

#### Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

#### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Background Workers

```bash
# Start Celery worker
celery -A applire worker -l info

# Start Celery beat (scheduled tasks)
celery -A applire beat -l info
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/applire

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend
VITE_API_URL=http://localhost:8000/api
```

---

## 📚 API Documentation

### Authentication

Applire uses JWT (JSON Web Tokens) for authentication.

```bash
# Register a new user
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Core Endpoints

#### Upload CVs

```bash
POST /api/cv/upload
Content-Type: multipart/form-data

files: [cv1.pdf, cv2.pdf, cv3.pdf]
```

#### Create Master Profile

```bash
POST /api/profile/create
{
  "cv_ids": [1, 2, 3],
  "job_description": "QA Manager role in pharma..."
}
```

#### Analyze Match

```bash
GET /api/match/{profile_id}/{job_id}

Response:
{
  "match_score": 82,
  "status": "strong_fit",
  "gaps": [
    {
      "requirement": "EU GMP Audit Experience",
      "user_has": "ANVISA audits (highly relevant)",
      "severity": "minor"
    }
  ]
}
```

#### Generate Tailored CV

```bash
POST /api/cv/generate
{
  "profile_id": 123,
  "job_id": 456,
  "format": "pdf"
}

Response:
{
  "cv_url": "https://cdn.applire.com/cv/...",
  "download_url": "https://cdn.applire.com/download/..."
}
```

Full API documentation available at `/api/docs` (Swagger UI).

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Frontend Tests

```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

---

## 🗂️ Project Structure

```
applire/
├── backend/
│   ├── applire/              # Django project settings
│   ├── apps/
│   │   ├── cv/               # CV parsing and management
│   │   ├── profile/          # Master profile logic
│   │   ├── matching/         # Gap analysis and scoring
│   │   ├── generation/       # CV generation engine
│   │   └── users/            # User management
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API services
│   │   └── utils/            # Utility functions
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🛣️ Roadmap

### ✅ Completed (Sprint 1-10)

- [x] Multi-CV upload and parsing
- [x] Master profile consolidation
- [x] Job description analysis
- [x] Gap detection and match scoring
- [x] Conversational interview flow
- [x] CV generation (PDF/DOCX)
- [x] Cultural adaptation detection
- [x] B2B batch matching
- [x] Kandidatenprofile generation

### 🚧 In Progress

- [ ] Advanced ATS optimization
- [ ] Multi-language support (German, French, Spanish)
- [ ] LinkedIn profile import
- [ ] Browser extension for one-click applications

### 🔮 Future

- [ ] AI-powered interview preparation
- [ ] Salary negotiation insights
- [ ] Company culture matching
- [ ] Mobile app (iOS/Android)
- [ ] Integration with job boards (LinkedIn, Indeed, StepStone)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow **PEP 8** for Python code
- Use **ESLint** and **Prettier** for TypeScript/React
- Write **tests** for new features
- Update **documentation** as needed
- Keep commits **atomic** and **descriptive**

### Code Style

```bash
# Backend: Format with Black
black .

# Backend: Lint with Flake8
flake8 .

# Frontend: Format with Prettier
npm run format

# Frontend: Lint with ESLint
npm run lint
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **Django** and **React** communities
- All contributors and early adopters
- Pharma industry professionals who provided domain expertise

---

## 📞 Contact & Support

- **Website**: [applire.com](https://applire.com) *(coming soon)*
- **Email**: support@applire.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/applire/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/applire/discussions)

---

<div align="center">

**Built with ❤️ for job seekers and recruiters worldwide**

*Precise. Confident. Future-Ready.*

</div>
