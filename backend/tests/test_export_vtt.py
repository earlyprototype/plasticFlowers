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
    speech = {
        "demo": [
            (0.125, 59.9996, "Can you hear me?\r\nYes, clearly.\n\nLet's begin."),
            (59.9996, 3599.9996, "Read <b> & then &amp; aloud."),
            (3599.9996, 3602.75, "One hour in."),
        ],
        "short": [
            (59.9996, 60.0004, "Across the minute."),
            (60.0, 60.0005, "At the minute."),
            (3599.9996, 3600.0004, "Across the hour."),
        ],
        "adjacent": [
            (59.9996, 60.0, "First minute cue."),
            (60.0, 62.0, "Second minute cue."),
            (3599.9996, 3600.0, "First hour cue."),
            (3600.0, 3602.0, "Second hour cue."),
        ],
        "fractional": [
            (59.9996, 60.0004, "First."),
            (60.0004, 62.0, "Second."),
        ],
        "instant": [
            (59.9996, 59.9996, "Instant."),
            (59.9997, 59.9998, "Another short cue."),
            (59.99975, 59.9999, "Overlapping speech."),
        ],
        "empty": [],
    }

    async def get_session(session_id):
        if session_id in speech:
            return SessionSummary(
                id=session_id, name=session_id, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
            )

    async def list_chunks(session_id):
        return [
            TranscriptChunk(id=str(i), session_id=session_id, start_time=start, end_time=end, text=text)
            for i, (start, end, text) in enumerate(speech[session_id])
        ]

    monkeypatch.setattr(export, "get_session_record", get_session)
    monkeypatch.setattr(export, "list_chunks_for_session", list_chunks)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def demo_export(client):
    return await client.get("/api/sessions/demo/export/vtt")


@pytest.fixture
async def short_export(client):
    return await client.get("/api/sessions/short/export/vtt")


@pytest.fixture
async def boundary_export(client, request):
    return await client.get(f"/api/sessions/{request.param}/export/vtt")


def test_boundary_timestamps(demo_export):
    assert demo_export.status_code == 200
    assert demo_export.headers["content-type"].split(";")[0] == "text/vtt"
    assert "00:01:00.000 --> 01:00:00.000" in demo_export.text.splitlines()


async def read_player_cues(vtt):
    data = b64encode(vtt).decode("ascii")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(offline=True)
        await page.set_content(f'<video><track kind="captions" default src="data:text/vtt;base64,{data}"></video>')
        await page.wait_for_function("document.querySelector('track').readyState === 2")
        cues = await page.locator("track").evaluate("""element => Array.from(element.track.cues, cue =>
            [cue.startTime, cue.endTime, cue.getCueAsHTML().textContent])""")
        await browser.close()
        return cues


def player_cues(vtt):
    # The app's Windows selector loop cannot launch Playwright's subprocess.
    loop_factory = asyncio.ProactorEventLoop if sys.platform == "win32" else asyncio.new_event_loop
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        return runner.run(read_player_cues(vtt))


def test_exported_cues_load_in_player(demo_export, tmp_path):
    caption_file = tmp_path / "captions.vtt"
    caption_file.write_bytes(demo_export.content)
    print(f"Caption playback file: {caption_file}")

    assert player_cues(caption_file.read_bytes()) == [
        [0.125, 60, "Can you hear me?\nYes, clearly.\n\nLet's begin."],
        [60, 3600, "Read <b> & then &amp; aloud."],
        [3600, 3602.75, "One hour in."],
    ]


def test_positive_cues_that_round_to_one_timestamp(short_export):
    assert short_export.status_code == 200
    assert player_cues(short_export.content) == [
        [60, 60.001, "Across the minute."],
        [60, 60.001, "At the minute."],
        [3600, 3600.001, "Across the hour."],
    ]


@pytest.mark.parametrize(
    "boundary_export, expected",
    [
        pytest.param(
            "adjacent",
            [
                [60, 60.001, "First minute cue."],
                [60.001, 62, "Second minute cue."],
                [3600, 3600.001, "First hour cue."],
                [3600.001, 3602, "Second hour cue."],
            ],
            id="adjacent-at-minute-and-hour",
        ),
        pytest.param(
            "fractional",
            [[60, 60.001, "First."], [60.001, 62, "Second."]],
            id="adjacent-at-fractional-boundary",
        ),
        pytest.param(
            "instant",
            [
                [60, 60.001, "Instant."],
                [60.001, 60.002, "Another short cue."],
                [60.001, 60.002, "Overlapping speech."],
            ],
            id="equal-endpoints-and-submillisecond-gap",
        ),
    ],
    indirect=["boundary_export"],
)
def test_short_cues_load_in_player(boundary_export, expected):
    assert boundary_export.status_code == 200
    assert player_cues(boundary_export.content) == expected


async def test_empty_session_exports_header_only(client):
    response = await client.get("/api/sessions/empty/export/vtt")
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "text/vtt"
    assert response.content == b"WEBVTT\n\n"


async def test_missing_session_returns_404(client):
    response = await client.get("/api/sessions/missing/export/vtt")
    assert response.status_code == 404
