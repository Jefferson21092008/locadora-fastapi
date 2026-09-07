from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from fastapi import Request

def obter_ip_cliente(
    request: Request,
) -> str:
    forwarded_for = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded_for:
        return (
            forwarded_for
            .split(",", 1)[0]
            .strip()
        )

    if request.client:
        return request.client.host

    return "desconhecido"

class RateLimiter:
    def __init__(self):
        self._tentativas = defaultdict(deque)
        self._lock = Lock()

    def atingiu_limite(
        self,
        chave: str,
        limite: int,
        janela_segundos: int,
    ) -> bool:
        agora = monotonic()
        inicio_janela = agora - janela_segundos

        with self._lock:
            tentativas = self._tentativas[chave]

            while (
                tentativas
                and tentativas[0] <= inicio_janela
            ):
                tentativas.popleft()

            return len(tentativas) >= limite

    def registrar(
        self,
        chave: str,
    ):
        with self._lock:
            self._tentativas[chave].append(
                monotonic()
            )

    def limpar(
        self,
        chave: str,
    ):
        with self._lock:
            self._tentativas.pop(
                chave,
                None,
            )

    def limpar_tudo(self):
        with self._lock:
            self._tentativas.clear()


rate_limiter = RateLimiter()