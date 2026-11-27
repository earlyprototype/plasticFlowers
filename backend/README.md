# backend

FastAPI application for plasticFlower. See `_docs/_dev/_MVP/_structure/01_project_structure.md` for responsibilities.

## Play a session caption export

From `backend/`, with a Python 3.11+ virtual environment active, install the test tools and headless Chromium once.

```sh
python -m pip install -e ".[dev]"
python -m playwright install --with-deps --only-shell chromium
```

Run the offline example. It requests `GET /api/sessions/demo/export/vtt` with three synthetic transcript chunks, saves the response as `captions.vtt`, and loads the file into a Chromium video caption track.

```sh
python -m pytest -q -s tests/test_export_vtt.py
```

To watch the hour change, open a terminal in the directory printed after `Caption playback file`. Use FFmpeg with its `subtitles` filter to make a five-second preview.

```sh
ffmpeg -f lavfi -i "color=s=640x360:r=10:d=5,setpts=PTS+3598/TB,subtitles=captions.vtt,setpts=PTS-STARTPTS" -c:v libx264 -pix_fmt yuv420p caption-preview.mp4
```

Open `caption-preview.mp4` in a video player. The preview starts at session time 00:59:58. It shows `Read <b> & then &amp; aloud.` for two seconds, then `One hour in.` at 01:00:00.
