# Core Packaging + GHCR CI — Sprint 30 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package Applire Core as an installable Python package and publish a Docker image to GHCR on each GitHub Release.

**Architecture:** `pyproject.toml` in `backend/` enables `pip install -e .` so Cloud's dev virtualenv can import `applire.*` from the Core source tree. A GitHub Actions `release.yml` triggers on GitHub Release events, builds the existing Dockerfile, and pushes `ghcr.io/tobias-rosenbaum/applire-core:vX.Y.Z` to GHCR. The Dockerfile itself does not change.

**Tech Stack:** Python setuptools, GitHub Actions, Docker, GitHub Container Registry (GHCR)

**Prerequisite:** None — this is the first sprint in the Cloud sequence.

**Branch:** Create and work on `sprint-30` off `main`.

---

## File Map

| Action | Path |
|---|---|
| Create | `backend/pyproject.toml` |
| Create | `.github/workflows/release.yml` |

---

### Task 1: Create `backend/pyproject.toml`

**Files:**
- Create: `backend/pyproject.toml`

- [ ] **Step 1: Write `backend/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=70"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "applire"
version = "1.1.0"
requires-python = ">=3.12"
# Dependencies are declared in requirements.txt and installed separately.
# This file exists solely to make `pip install -e .` work for Cloud's dev workflow (ADR-031).
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["applire*"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add pyproject.toml to enable pip install -e . (ADR-031)"
```

---

### Task 2: Verify editable install works

This is a manual verification step — run it in the Cloud virtualenv.

- [ ] **Step 1: Create a throwaway venv and test the install**

```bash
cd /home/apliqa/Documents/Applire/Applire-Cloud
python -m venv .venv-test
source .venv-test/bin/activate
pip install -e ../Applire-Core/backend/
pip install -r ../Applire-Core/backend/requirements.txt
python -c "import applire; print(applire.__version__)"
```

Expected output: `1.1.0`

- [ ] **Step 2: Verify the install is editable (live changes)**

```bash
python -c "import applire.config; print('config OK')"
python -c "from applire.auth import get_auth_provider; print('auth OK')"
deactivate
rm -rf .venv-test
```

Both lines should print without ImportError.

---

### Task 3: Write GitHub Actions `release.yml`

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Release — build and publish Core image

on:
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: tobias-rosenbaum/applire-core

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

Note: `GITHUB_TOKEN` is automatically available in GitHub Actions — no secret to create for Core's GHCR push.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add release workflow — build and push applire-core image to GHCR"
```

---

### Task 4: Merge to main, create first release, verify GHCR

- [ ] **Step 1: Merge sprint-30 to main**

```bash
git checkout main
git merge sprint-30
git push origin main
```

- [ ] **Step 2: Create GitHub Release via CLI**

```bash
gh release create v1.0.0 \
  --title "Applire Core v1.0.0" \
  --notes "First packaged release. Adds pyproject.toml for Cloud editable install (ADR-031) and GHCR CI pipeline (ADR-032)." \
  --target main
```

- [ ] **Step 3: Watch the pipeline**

```bash
gh run watch
```

Wait for the run to show ✓ (green).

- [ ] **Step 4: Verify the image exists on GHCR**

```bash
gh api /user/packages/container/applire-core/versions --jq '.[0].metadata.container.tags'
```

Expected: `["1.0.0","1.0"]`

Sprint A is complete when GHCR shows `ghcr.io/tobias-rosenbaum/applire-core:1.0.0`.
