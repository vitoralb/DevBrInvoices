import time


class RateLimiter:
    """
    Controlador de taxa para garantir um limite máximo de requisições por segundo.
    Para 4 req/s, o intervalo mínimo entre requisições é de 0.25s.
    """

    def __init__(self, max_per_second: float = 4.0):
        self.max_per_second = max_per_second
        self.interval = 1.0 / max_per_second if max_per_second > 0 else 0.0
        self.last_call = 0.0

    def wait(self):
        if self.interval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            sleep_time = self.interval - elapsed
            time.sleep(sleep_time)
        self.last_call = time.monotonic()
