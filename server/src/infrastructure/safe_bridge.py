"""
SafeBridge -- fault-tolerant wrapper over HttpCadBridge.

Enables calling any bridge method with exception handling,
auto-reconnect, and inter-call delays to prevent MainThreadExecutor overload.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.infrastructure.http_bridge import HttpCadBridge

logger = logging.getLogger(__name__)

DEFAULT_CALL_DELAY = 0.05  # seconds between calls to avoid queue overload


class SafeBridgeError(Exception):
    """Raised when the bridge becomes permanently unavailable."""


class SafeBridge:
    """Обёртка для безопасного вызова методов HttpCadBridge.

    Каждый вызов обёрнут в try/except. При ошибке логирует и
    возвращает None. После серии ошибок повторно подключается.

    Usage::

        safe = SafeBridge(http)
        result = safe.create_line(x1=0, y1=0, x2=10, y2=10)
        # result — str | None (handle или None при ошибке)
    """

    def __init__(
        self,
        bridge: HttpCadBridge,
        call_delay: float = DEFAULT_CALL_DELAY,
        auto_reconnect: bool = True,
    ) -> None:
        self._bridge = bridge
        self._call_delay = call_delay
        self._auto_reconnect = auto_reconnect
        self._consecutive_errors = 0

    @property
    def bridge(self) -> HttpCadBridge:
        return self._bridge

    @property
    def is_available(self) -> bool:
        return self._bridge.is_available

    def __getattr__(self, name: str) -> Any:
        """Proxy access to HttpCadBridge methods with error protection."""
        fn = getattr(self._bridge, name, None)
        if fn is None or not callable(fn):
            msg = f"HttpCadBridge has no method {name!r}"
            raise AttributeError(msg)

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self._bridge.is_available:
                if self._auto_reconnect:
                    logger.info("SafeBridge: attempting reconnect...")
                    self._bridge.connect()
                if not self._bridge.is_available:
                    logger.warning("SafeBridge.%s skipped: bridge unavailable", name)
                    return None
            try:
                result = fn(*args, **kwargs)
                self._consecutive_errors = 0
                time.sleep(self._call_delay)
                return result
            except Exception as e:
                self._consecutive_errors += 1
                logger.warning("SafeBridge.%s failed: %s", name, e)
                time.sleep(self._call_delay * 2)
                return None

        return wrapper


__all__ = ["DEFAULT_CALL_DELAY", "SafeBridge", "SafeBridgeError"]
