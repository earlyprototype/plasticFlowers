import asyncio
import sys
from base64 import b64encode
from datetime import datetime, timezone

import httpx
import pytest
from playwright.async_api import async_playwright

from app.api import export
from app.main import app
from app.models import SessionSummary, TranscriptChunk


@pytest.fixture
async def client(monkeypatch):
    speech = [
        (0.125, 59.9996, "Can you hear me?\r\nYes, clearly.\n\nLet's begin."),
        (59.9996, 3599.9996, "Read <b> & then &amp; aloud."),
        (3599.9996, 3602.75, "One hour in."),
    ]
    chunks = {
        "demo": [
            TranscriptChunk(id=str(i), session_id="demo", start_time=start, end_time=end, text=text)
            for i, (start, end, text) in enumerate(speech)
        ],
        "empty": [],
    }

    async def get_session(session_id):
        if session_id in chunks:
            return SessionSummary(
                id=session_id, name=session_id, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
            )

    async def list_chunks(session_id):
        return chunks[session_id]

    monkeypatch.setattr(export, "get_session_record", get_session)
    monkeypatch.setattr(export, "list_chunks_for_session", list_chunks)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def demo_export(client):
    return await client.get("/api/sessions/demo/export/vtt")


def test_boundary_timestamps(demo_export):
    assert demo_export.status_code == 200
    assert demo_export.headers["content-type"].split(";")[0] == "text/vtt"
    assert "00:01:00.000 --> 01:00:00.000" in demo_export.text.splitlines()


async def read_player_cues(caption_file):
    data = b64encode(caption_file.read_bytes()).decode("ascii")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(offline=True)
        await page.set_content(f'<video><track kind="captions" default src="data:text/vtt;base64,{data}"></video>')
        await page.wait_for_function("document.querySelector('track').readyState === 2")
        cues = await page.locator("track").evaluate("""element => Array.from(element.track.cues, cue =>
            [cue.startTime, cue.endTime, cue.getCueAsHTML().textContent])""")
        await browser.close()
        return cues


def test_exported_cues_load_in_player(demo_export, tmp_path):
    caption_file = tmp_path / "captions.vtt"
    caption_file.write_bytes(demo_export.content)
    print(f"Caption playback file: {caption_file}")

    # The app's Windows selector loop cannot launch Playwright's subprocess.
    loop_factory = asyncio.ProactorEventLoop if sys.platform == "win32" else asyncio.new_event_loop
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        cues = runner.run(read_player_cues(caption_file))
    assert cues == [
        [0.125, 60, "Can you hear me?\nYes, clearly.\n\nLet's begin."],
        [60, 3600, "Read <b> & then &amp; aloud."],
        [3600, 3602.75, "One hour in."],
    ]


async def test_empty_session_exports_header_only(client):
    response = await client.get("/api/sessions/empty/export/vtt")
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "text/vtt"
    assert response.content == b"WEBVTT\n\n"


async def test_missing_session_returns_404(client):
    response = await client.get("/api/sessions/missing/export/vtt")
    assert response.status_code == 404
