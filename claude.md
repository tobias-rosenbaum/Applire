# Apliqa — Claude Working Guide

## Authoritative Sources
- Architecture decisions → docs/product/architecture/arc42.md (read this before any architectural work)
- Feature roadmaps → docs/product/

## Project Layout
backend/apliqa/       — FastAPI app (Community Edition)
backend/requirements.txt
docs/product/roadmap  — roadmaps
docs/product/architecture — arc42 documentation
tests/                — readme.md
## Key Commands
docker compose up                                        # start everything
docker compose exec backend alembic upgrade head         # run migrations
pytest                                                   # run tests

## Conventions
- Version: single source of truth is backend/apliqa/__init__.py (__version__)
- Edition gating: check settings.apliqa_edition at service layer
- Cloud-only code: apliqa.cloud.* namespace only — never imported by Community code

## Hard Rules
- No auth enforcement in Community code (AUTH_PROVIDER=none is the Community default)
- Never put billing, multi-tenancy, or OIDC backends in the public repo
- Spec-first: new features need an ADR entry before implementation
- AGPL boundary: Community repo must be self-contained and runnable standalone
- After concluding an iteration, create test scripts according to tests/readme.md
## Known Gotchas
- mistralai==1.2.9 does not exist on PyPI; correct version is 1.3.0
