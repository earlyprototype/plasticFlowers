"""Exercise the Windows launcher with local HTTP servers and a Compose stand-in."""

import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen
import venv


ROOT = Path(__file__).resolve().parents[2]
PORTS = {"Backend": 8010, "Frontend": 3000}


def serve(service):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    control = Path(os.environ["PF_TEST_DIRECTORY"])
    if (control / f"fail-{service}").exists():
        sys.exit(23)
    if service == "Backend":
        for key in ("PLASTICFLOWER_FAKE_LLM", "PLASTICFLOWER_FAKE_EMBEDDINGS"):
            if os.environ.get(key) != "1":
                sys.exit(24)
        if Path(sys.prefix) != control / ".venv":
            sys.exit(25)
    expected_path = "/health" if service == "Backend" else "/"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status = 404 if self.path != expected_path else 200
            if (control / f"hold-{service}").exists():
                status = 503
            self.send_response(status)
            self.end_headers()
            self.wfile.write(b'{"status":"ok","neo4j":"ok"}' if service == "Backend" else b"<html>fixture</html>")
            (control / f"probed-{service}-{status}").touch()

        def log_message(self, *args):
            pass

    with HTTPServer(("127.0.0.1", PORTS[service]), Handler) as server:
        server.timeout = 0.1
        while not (control / f"fail-{service}").exists():
            server.handle_request()
    sys.exit(23)


@unittest.skipUnless(os.name == "nt", "requires Windows PowerShell")
class WindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        for port in PORTS.values():
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                try:
                    probe.bind(("127.0.0.1", port))
                except OSError:
                    self.fail(f"Local port {port} is in use. Stop the demo before running the launcher tests.")
        directory = tempfile.TemporaryDirectory(prefix="windows launcher ", dir=ROOT)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for folder in ("scripts", "docker", "backend", "frontend", "bin"):
            (self.root / folder).mkdir()
        self.write("docker/docker-compose.yml", "services: {}\n")
        self.write("bin/docker.cmd", '@echo off\nexit /b %PF_COMPOSE_EXIT%\n')
        venv.create(self.root / ".venv", with_pip=False)
        shutil.copy2(ROOT / "scripts/start_mvp.ps1", self.root / "scripts")
        shutil.copy2(__file__, self.root / "fixture.py")
        self.write(
            "backend/uvicorn.py",
            "import runpy, sys\n"
            "sys.argv = ['fixture', 'Backend']\n"
            "runpy.run_path('../fixture.py', run_name='__main__')\n",
        )
        self.write("frontend/package.json", '{"scripts":{"dev":"python ../fixture.py Frontend"}}')
        (self.root / "frontend/node_modules").mkdir()
        self.write(
            ".env",
            "NEO4J_PASSWORD=local-only-fixture\nPLASTICFLOWER_FAKE_LLM=0\nPLASTICFLOWER_FAKE_EMBEDDINGS=0\n",
        )
        self.log = self.root / "launcher.log"

    def write(self, path, contents):
        (self.root / path).write_text(contents, encoding="utf-8")

    def launch(self, compose_exit=0):
        # Only forward the variables needed by Windows, Python, and npm.
        allowed = ("SystemRoot", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA", "USERPROFILE")
        env = {key: os.environ[key] for key in allowed if key in os.environ}
        env.update(
            PATH=str(self.root / "bin") + os.pathsep + env["PATH"],
            PF_TEST_DIRECTORY=str(self.root),
            PF_COMPOSE_EXIT=str(compose_exit),
        )
        with self.log.open("w", encoding="utf-8") as out:
            self.process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", str(self.root / "scripts/start_mvp.ps1"), "-FakeMode", "-NoBrowser"],
                cwd=self.root, env=env, stdout=out, stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_launcher)

    def stop_launcher(self):
        if self.process.poll() is None:
            subprocess.run(["taskkill.exe", "/PID", str(self.process.pid), "/T", "/F"], capture_output=True)
            self.process.wait(timeout=10)

    def output(self):
        return self.log.read_text(encoding="utf-8", errors="replace")

    def wait_for(self, predicate):
        deadline = time.monotonic() + 30
        while not predicate():
            if self.process.poll() is not None or time.monotonic() >= deadline:
                self.fail(self.output())
            time.sleep(0.05)

    def assert_failed(self, service, was_ready=False):
        self.assertNotEqual(self.process.wait(timeout=30), 0)
        output = self.output()
        self.assertEqual("MVP Ready!" in output, was_ready, output)
        self.assertRegex(output, rf"(?i){service}[^\r\n]*(?:failed|exited|stopped)", output)

    def test_compose_failure_prevents_ready(self):
        self.launch(compose_exit=17)
        self.assert_failed("Compose")

    def test_fake_mode_rejects_placeholder_password(self):
        self.write(".env", 'NEO4J_PASSWORD="your-neo4j-password-here"\n')
        self.launch()
        self.assertNotEqual(self.process.wait(timeout=10), 0)
        self.assertIn("NEO4J_PASSWORD", self.output())
        self.assertNotIn("Starting Neo4j", self.output())

    def test_backend_start_failure(self):
        self.write("fail-Backend", "")
        self.launch()
        self.assert_failed("Backend")

    def test_frontend_start_failure(self):
        self.write("fail-Frontend", "")
        self.launch()
        self.assert_failed("Frontend")

    def test_both_endpoints_required_and_late_exit_stops_sibling(self):
        for service in PORTS:
            self.write(f"hold-{service}", "")
        self.launch()
        for service in PORTS:
            self.wait_for(lambda: (self.root / f"probed-{service}-503").exists())
            self.assertNotIn("MVP Ready!", self.output())
            (self.root / f"hold-{service}").unlink()
            self.wait_for(lambda: (self.root / f"probed-{service}-200").exists())
        self.wait_for(lambda: "MVP Ready!" in self.output())
        for url in ("http://127.0.0.1:8010/health", "http://127.0.0.1:3000/"):
            with urlopen(url, timeout=2) as response:
                self.assertEqual(response.status, 200)
        self.write("fail-Backend", "")
        self.assert_failed("Backend", was_ready=True)
        with self.assertRaises(URLError):
            urlopen("http://127.0.0.1:3000/", timeout=2)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in PORTS:
        serve(sys.argv[1])
    else:
        unittest.main()
