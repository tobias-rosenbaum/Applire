# Changelog

All notable changes to Applire are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.31.0-beta] – 2026-05-05 (First public release)

### Added
- AI-powered CV tailoring for the DACH job market (Germany, Austria, Switzerland)
- CV section editor with smart gap analysis and interview preparation
- Job description URL ingestion with skill extraction
- Cover letter generation
- Multilingual UI (de/en) via next-intl
- CV export to PDF with multiple color profiles and templates
- Photo management (upload, crop, remove)
- LLM review layer with OpenRouter / Mistral AI support
- Comprehensive CI/CD pipeline (GitHub Actions, GHCR)
- Docker Compose setup for self-hosting
- Offline mode with service worker
- MCP server integration (Kaile agent channel)
- AGPL-3.0 Community Edition open-source release

### Tech Stack
- Backend: FastAPI 0.115, Python 3.12, SQLAlchemy 2, Alembic
- Frontend: Next.js 15.2, React 19, TypeScript 5, Tailwind CSS 4
- AI: OpenRouter (multi-model), Mistral AI, MCP tool integration
- Database: SQLite (dev), PostgreSQL (prod)

[Unreleased]: https://github.com/tobias-rosenbaum/Applire/compare/v0.31.0-beta...HEAD
[0.31.0-beta]: https://github.com/tobias-rosenbaum/Applire/releases/tag/v0.31.0-beta
