"""Playwright PDF renderer for cover letters.

Separated from cover_letter.py to keep the main service file testable
without a Playwright dependency.
"""
import uuid

from playwright.async_api import async_playwright
from sqlalchemy import select

from applire.db.session import AsyncSessionLocal
from applire.models.cover_letter import CoverLetterStatus, GeneratedCoverLetter
from applire.services.cover_letter import get_cover_letter_html


async def render_pdf(cl_id: uuid.UUID) -> bytes:
    """Render the cover letter to PDF using Playwright. Returns raw PDF bytes."""
    async with AsyncSessionLocal() as db:
        html = await get_cover_letter_html(cl_id, db)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
        )
        await browser.close()
    return pdf_bytes
