# Applire

<div align="center">

![Applire - AI-Powered CV Intelligence Platform](https://cdn.simtheory.ai/image/upload/v1775325052/user_7324/ai-document-processing_492199c1.png)

# Applire

**Open-Source Career Intelligence Platform for the DACH Market**

*Transform hours of CV tailoring into seconds. Upload your CVs, paste a job description, and let AI guide you through an intelligent interview to create perfectly matched application documents.*

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub Stars](https://img.shields.io/github/stars/applire/applire?style=social)](https://github.com/applire/applire)

[ Quick Start](#-installation) • [ Documentation](docs/) • [ Community](#-community--support) • [ Report Bug](https://github.com/applire/applire/issues)

</div>

---

##  What is Applire?

**Applire** is an open-source AI platform that combines deep career intelligence with DACH-specific cultural expertise to automate high-quality CV tailoring.

Built for **all job seekers in the DACH market**, with unmatched depth in regulated industries (Pharma, GxP, Medtech) — a specialization that proves our precision for every user.

Unlike generic CV builders, Applire:
- 易 **Learns from you**: Builds a persistent Master Profile that gets smarter with every CV you upload
-  **Interviews you intelligently**: Asks targeted questions to fill gaps between your experience and job requirements
-  **Tailors with precision**: Generates culturally appropriate CVs optimized for DACH recruiters and ATS systems
- 烙 **Agent-first design**: Accessible to AI assistants via the Model Context Protocol (MCP)
-  **Privacy by design**: GDPR-compliant, self-hosted, full data sovereignty

**In 3 simple steps:**
1.  Upload 2-4 versions of your CV
2.  Paste the job description
3.  Answer a few intelligent questions → ✨ Get a perfectly tailored CV

---

##  Who is Applire for?

Applire serves diverse personas across the DACH job market:

###  **Marcus - The Expert**
Experienced professional with deep domain expertise who needs precision tailoring for demanding roles. Values efficiency and quality over hand-holding.

###  **Priya - The Relocator**
International candidate moving to DACH who needs cultural "translation" of their career history to meet local CV conventions and recruiter expectations.

###  **Jason - The Recruiter**
Professional headhunter who needs to efficiently generate high-quality, tailored CVs for clients across various industries.

### ✏️ **Felix - The Finetuner**
Any user who wants surgical, section-level control over their CV. Trusts AI to draft but wants to fine-tune the output to sound authentic and personal.

### 烙 **Kaile - The AI Agent**
AI assistant (Claude, ChatGPT, custom agents) calling Applire on behalf of human users via MCP or REST API for seamless career intelligence integration.

---

##  Key Features

### 易 Intelligent Master Profile

- **Multi-CV Consolidation**: Upload multiple CVs and automatically merge them into a rich, conflict-aware Master Profile
- **Additive Enrichment**: Every CV upload, interview session, and edit enriches your profile — it never overwrites, only accumulates
- **Source Tracking**: Full audit trail of where every piece of information came from
- **Conflict Resolution**: Smart detection of factual contradictions (dates, degrees) with user-controlled resolution

###  Job-First Analysis & Gap Detection

- **Deep JD Analysis**: Extracts requirements, skills, cultural signals, and industry context from job descriptions
- **Transparent Gap Scoring**: 0-100% match score with detailed explanations of what's missing
- **Categorized Gaps**: 
  - **Category A** (Hard blockers): Must-have requirements you don't meet
  - **Category B** (Confirmation needed): You likely have this, but it's not stated clearly
  - **Category C** (Exploratory): Soft requirements worth discussing

###  Conversational Interview Orchestrator

- **Two Modes**:
  - **Targeted Mode** (for experienced users): Focuses on filling specific gaps identified in your profile
  - **Guided Mode** (for new users): Systematically builds your profile section by section
- **Stateful Backend**: Pause and resume anytime — your progress is saved server-side
- **Smart Completion**: Automatically detects when you're done or when all gaps are resolved
- **Profile Updates**: Every answer enriches your Master Profile in real-time

###  CV Generation & Fine-Tuning

- **ATS-Optimized PDFs**: Generated via Playwright/Chromium with CSS-based themes
- **Live Browser Preview**: See exactly what your CV will look like before downloading
- **Section-Level Editing**: Fine-tune individual sections (introduction, positions, skills) with live re-rendering
- **Dual Save Path**: Save edits to your Master Profile (permanent) or just to this CV (one-time)
- **AI-Assisted Editing**: Optional "Let Kaile help" for targeted gap completion within the editor
- **Cultural Adaptation**: Automatic detection and formatting for German, Austrian, and Swiss CV conventions

###  DACH Cultural Intelligence

- **Market-Specific Formatting**: Lebenslauf vs. international CV formats
- **Cultural Signal Detection**: Identifies when a CV needs adaptation (e.g., Indian → German pharma standards)
- **Multilingual Support**: German, English, with French and Spanish planned
- **Regulatory Industry Depth**: Specialized knowledge for Pharma, GxP, Medtech roles (optional premium layer)

###  Privacy & GDPR Compliance

- **Privacy by Design** (GDPR Art. 25): Minimal data collection, encryption at rest
- **Automated Retention**: Daily cron job enforces TTLs:
  - Uploaded files: 7 days
  - Interview sessions: 30 days
  - Generated CVs: 90 days (human) / 24 hours (agent)
- **Right to Erasure** (GDPR Art. 17): One-click full data deletion
- **Self-Hosted**: Your data never leaves your infrastructure

---

## 烙 Built for the AI Agent Era

Applire is the first career platform optimized for **AI agents as customers**:

### Model Context Protocol (MCP)
- **Seamless Integration**: First-class support for Claude Desktop, ChatGPT, Cursor, and custom AI agents
- **Stateful Sessions**: Agents can pause, resume, and recover from interruptions
- **Flow Orchestrator**: Guides agents through the correct sequence (JD analysis → CV import → gap analysis → interview → generation)
- **Async Generation**: Non-blocking CV generation with polling-based status checks

### REST API
- **Full HTTP API**: Programmatic access for remote integrations
- **OpenAPI Documentation**: Interactive Swagger UI at `/docs`
- **Usage-Based Pricing**: Pay-per-CV model for agent-driven workflows (future)

### Agent Workflow Example
```bash
# Start MCP server (stdio transport)
python -m applire.mcp

# Agent calls:
1. start_flow() → flow_id
2. analyze_jd(text="Senior Python Engineer...") → job_id
3. analyze_gaps(job_id) → gap_report
4. run_interview(session_id, message="I have 5 years...") → next_question
5. generate_cv(job_id) → cv_id (async)
6. get_cv_status(cv_id) → {status: "ready", pdf_url: "..."}
```

---

## ️ Architecture & Tech Stack

### Backend

- **Python 3.12+**: Modern async Python with type hints
- **FastAPI**: High-performance async web framework
- **PostgreSQL 16**: JSONB for flexible Master Profile schema
- **Pydantic**: Type-safe data validation and serialization
- **SQLAlchemy 2.0**: Async ORM with full type support
- **Alembic**: Database migrations

### Frontend

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **ShadCN/UI**: Accessible component library
- **Tailwind CSS**: Utility-first styling

### AI/ML

- **Mistral AI** (default): EU-hosted LLM with strong German proficiency (`mistral-large-latest`)
- **LLM Provider Abstraction**: Pluggable backends for Mistral, OpenAI, Ollama (self-hosted)
- **Custom State Machine**: 4-node async interview orchestrator (no LangGraph dependency)
- **Playwright**: Headless Chromium for PDF generation

### Infrastructure

- **Docker & Docker Compose**: Containerized deployment
- **PostgreSQL 16**: Primary database with JSONB support
- **Retention Worker**: Daily cron for GDPR TTL enforcement
- **GitHub Actions**: CI/CD pipeline with pytest and Playwright E2E tests

### Agent Integration

- **Model Context Protocol (MCP)**: stdio transport for local AI agents
- **REST API**: Full HTTP API for remote integrations
- **Flow Orchestrator**: State machine for multi-step agent workflows
- **Session Recovery**: Agents can resume interrupted sessions via `flow_id`

---

##  Installation

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 16+**
- **Docker & Docker Compose** (recommended)
- **LLM API Key**: Mistral AI (default), OpenAI, or Ollama (local)

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/applire/applire.git
cd applire

# Copy environment template
cp .env.example .env

# Edit .env and configure:
# - LLM_PROVIDER=mistral (or openai, ollama)
# - MISTRAL_API_KEY=your_key_here (or OPENAI_API_KEY)
# - DATABASE_URL=postgresql://applire:password@db:5432/applire

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Manual Setup (Development)

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn applire.main:app --reload --port 8001
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

#### Retention Worker (GDPR Compliance)

```bash
# The retention worker runs as a daily cron in Docker Compose
# For manual execution:
python -m applire.retention
```

---

##  Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM Provider (mistral, openai, ollama)
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your_mistral_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here  # Alternative
# OLLAMA_BASE_URL=http://localhost:11434   # For local Ollama

# Database
DATABASE_URL=postgresql://applire:password@localhost:5432/applire

# Backend
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
APPLIRE_BASE_URL=http://localhost:8001

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001

# Storage (local by default)
UPLOAD_DIR=./data/uploads

# OCR Backend (mistral_vision or tesseract)
OCR_BACKEND=mistral_vision

# Auth (none for Community Edition single-user mode)
AUTH_PROVIDER=none
```

### LLM Provider Options

Applire supports multiple LLM backends via a pluggable abstraction layer:

| Provider | Configuration | Use Case |
|----------|---------------|----------|
| **Mistral AI** (default) | `LLM_PROVIDER=mistral`<br>`MISTRAL_API_KEY=...` | EU-hosted, GDPR-native, strong German proficiency |
| **OpenAI** | `LLM_PROVIDER=openai`<br>`OPENAI_API_KEY=...` | High quality, widely available |
| **Ollama** (local) | `LLM_PROVIDER=ollama`<br>`OLLAMA_BASE_URL=http://localhost:11434` | Fully offline, no API costs, privacy-first |

---

##  API Documentation

### REST API

Full OpenAPI documentation available at `http://localhost:8001/docs` (Swagger UI).

#### Core Endpoints

```bash
# Job Description Analysis
POST /api/job/analyze
{
  "text": "Senior Software Engineer role...",
  "url": "https://example.com/job"  # Optional
}

# CV Upload & Profile Enrichment
POST /api/profile/upload
Content-Type: multipart/form-data
files: [cv1.pdf, cv2.pdf]
job_id: <optional-job-id>  # For JD-aware extraction

# Gap Analysis
POST /api/gap/analyze
{
  "job_id": "uuid",
  "profile_id": "uuid"  # Optional, uses current user's profile by default
}

# Start Interview Session
POST /api/session
{
  "job_id": "uuid",
  "mode": "targeted"  # or "guided", or auto-detected
}

# Send Interview Message
POST /api/session/{session_id}/message
{
  "message": "I have 5 years of experience with Python and FastAPI..."
}

# Generate CV
POST /api/cv/generate
{
  "job_id": "uuid",
  "format": "german_lebenslauf",  # or "international"
  "theme": "classic_german"
}

# Check CV Generation Status
GET /api/cv/{cv_id}/status
# Returns: { "status": "pending" | "ready" | "failed", "pdf_url": "..." }

# Download CV
GET /api/cv/{cv_id}/pdf
```

### Model Context Protocol (MCP)

Applire exposes an MCP server for AI agents:

```bash
# Start MCP server (stdio transport)
python -m applire.mcp
```

#### MCP Tools

| Tool | Description |
|------|-------------|
| `start_flow(job_id?)` | Create or resume a flow session |
| `analyze_jd(text?, url?)` | Analyze a job description |
| `analyze_gaps(job_id)` | Detect gaps between profile and JD |
| `run_interview(session_id, message)` | Send a message in an interview session |
| `generate_cv(job_id, options?)` | Initiate async CV generation |
| `get_cv_status(cv_id)` | Poll CV generation status |
| `advance_flow(flow_id, step, artifact_id?)` | Advance to next step in flow |
| `get_flow_state(flow_id)` | Get current flow state and available actions |

#### MCP Resources

- `profile://current` — User's Master Profile
- `job://{job_id}` — Job analysis
- `cv://{cv_id}` — Generated CV
- `flow://{flow_id}` — Flow session state

---

## 離 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage (enforces ≥75% threshold)
pytest --cov=applire --cov-fail-under=75

# Generate HTML coverage report
pytest --cov=applire --cov-report=html
```

### Frontend Tests

```bash
# Run unit tests
npm test

# Run E2E tests (Playwright)
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui
```

### CI/CD Pipeline

GitHub Actions runs:
1. Backend unit tests (pytest, ≥75% coverage)
2. Backend integration tests (Docker stack)
3. E2E tests (Playwright)

All tiers must pass before merge.

---

## ️ Project Structure

```
applire/
├── backend/
│   ├── applire/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── services/            # Business logic layer
│   │   │   ├── interview/       # Interview Orchestrator (state machine)
│   │   │   ├── flow/            # Flow Orchestrator
│   │   │   ├── profile/         # Master Profile merge logic
│   │   │   ├── cv/              # CV generation & section editing
│   │   │   └── gap/             # Gap analysis
│   │   ├── providers/           # LLM, Auth, Storage abstractions
│   │   ├── mcp/                 # Model Context Protocol server
│   │   ├── retention/           # GDPR retention worker
│   │   └── templates/           # Jinja2 CV templates
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # React components
│   ├── lib/                     # Utilities and API clients
│   └── public/
├── docs/
│   ├── architecture/
│   │   ├── arc42.md             # Architecture documentation
│   │   └── ADR.md               # Architecture Decision Records
│   └── deployment.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ️ Roadmap
## ️ Roadmap

### ✅ Current Release (MVP)

- [x] Multi-CV upload and parsing (PDF, DOCX, images via OCR)
- [x] Master Profile consolidation with conflict resolution
- [x] Job description analysis (text + URL scraping)
- [x] Gap detection and match scoring
- [x] Conversational interview flow (Targeted + Guided modes)
- [x] CV generation (PDF via Playwright)
- [x] CV Section Editor (Finetuner) with live preview and AI-assisted editing
- [x] Cultural adaptation detection (DACH-specific)
- [x] MCP Server (stdio transport for AI agents)
- [x] Flow Orchestrator (state machine for user journey)
- [x] GDPR Retention Worker (automated TTL enforcement)

###  Next Up

**Application Document Completeness**
- [ ] **Cover Letter Generation**: AI-powered cover letter creation based on JD + Master Profile, with optional motivation interview
- [ ] **Photo Management**: Upload and extract application photos from CVs (DACH-specific requirement)

**Core Experience Improvements**
- [ ] **Gap Interview Refinement**: Enhanced question quality and relevance through fine-tuning
- [ ] **Additional CV Layouts**: Expanding template library (Modern Swiss, International, Academic, etc.)

**Market Expansion**
- [ ] **European Country Support**: Gradual rollout beyond DACH (France, Italy, Spain, Portugal, Poland) with localized formats, cultural adaptations, and language support

**Developer Experience**
- [ ] **REST API Public Release**: Full HTTP API with comprehensive documentation
- [ ] **MCP Marketplace Listing**: Distribution via Anthropic, OpenAI, and Cursor marketplaces

###  Future Vision

**Career Intelligence Platform (Post-MVP Validation)**
- [ ] **Mock Interview Preparation**: AI-powered practice sessions with role-specific questions and feedback
- [ ] **Gamification Elements**: Profile completeness scores, interview readiness tracking, achievement system
- [ ] **Career Path Advisory**: Skill gap analysis and training recommendations (informational service)
- [ ] **Job Search & Recommendation**: Curated job suggestions based on Master Profile
- [ ] **One-Click Application**: Full document package generation and submission
- [ ] **Mobile App**: iOS and Android native applications
---

## 欄 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow **PEP 8** for Python code (enforced by `black` and `flake8`)
- Use **TypeScript** for all frontend code
- Write **tests** for new features (≥75% coverage for backend)
- Update **documentation** as needed (arc42.md, ADRs)
- Keep commits **atomic** and **descriptive**
- Sign commits with **DCO** (`git commit -s`)

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

### Contributor License Agreement (CLA)

For contributions to core service logic (`applire/services/`, `applire/models/`, `applire/routers/`), we require a signed CLA. This allows us to maintain the open-core business model while keeping the Community Edition fully open-source.

- **DCO** (Developer Certificate of Origin): Required for all commits (`git commit -s`)
- **CLA** (Contributor License Agreement): Required for core logic contributions (signed once via CLA Assistant)

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

##  Community & Support

### Get Help

-  **[Documentation](docs/)** - Architecture, ADRs, deployment guides
-  **[GitHub Issues](https://github.com/applire/applire/issues)** - Report bugs and request features
-  **[GitHub Discussions](https://github.com/applire/applire/discussions)** - Ask questions and share ideas

### Stay Updated

-  **[Twitter](https://twitter.com/applire)** - Follow for updates and announcements
-  **[Blog](https://applire.com/blog)** - Product updates, tutorials, and case studies

---

##  License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

### Why AGPL?

We chose AGPL to ensure that:
- ✅ **The software remains free and open source** - Always accessible to everyone
- ✅ **Modifications must be shared** - Even when used as a service (SaaS)
- ✅ **The community benefits** - All improvements flow back to the project
- ✅ **Your privacy is protected** - Full transparency in how your data is processed
- ✅ **No vendor lock-in** - You control your data and infrastructure

### Commercial Licensing

For organizations that cannot comply with AGPL requirements (e.g., proprietary SaaS offerings), we offer commercial licenses with:
- Proprietary use rights
- Custom SLA and support
- Priority feature development
- Legal indemnification

 Contact **licensing@applire.com** for details.

---

##  Acknowledgments

- **Mistral AI** for EU-hosted LLM infrastructure
- **FastAPI** and **Next.js** communities
- All contributors and early adopters
- DACH industry professionals who provided domain expertise
- The open-source community for inspiration and tools

---

##  Contact & Support

- **Website**: [applire.com](https://applire.com)
- **Email**: support@applire.com
- **Issues**: [GitHub Issues](https://github.com/applire/applire/issues)
- **Discussions**: [GitHub Discussions](https://github.com/applire/applire/discussions)
- **Security**: security@applire.com (for responsible disclosure)

---

<div align="center">

**Built with ❤️ for job seekers in the DACH market**

*Open-source career intelligence. Privacy-first. Agent-ready.*

[⭐ Star us on GitHub](https://github.com/applire/applire) • [ Follow on Twitter](https://twitter.com/applire)

</div>
