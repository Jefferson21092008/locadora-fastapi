import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest


HOST = "127.0.0.1"
PORTA = 8765
URL_BASE = f"http://{HOST}:{PORTA}"


@pytest.fixture(
    scope="session"
)
def app_url():
    raiz_projeto = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    processo = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            HOST,
            "--port",
            str(PORTA),
        ],
        cwd=raiz_projeto,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen(
                    f"{URL_BASE}/app/",
                    timeout=1,
                ) as resposta:
                    if resposta.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError(
                "A FastAPI não iniciou "
                "para os testes E2E."
            )

        yield URL_BASE

    finally:
        processo.terminate()

        try:
            processo.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            processo.kill()