"""Request-scoped state via contextvars.

Replaces 30+ global variables with a single ``ContextVar``
that holds the current ``CadRepository`` and ``UseCaseFactory``.

Each request (tool call) gets its own context, making the server
safe for concurrent SSE connections.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.use_case_factory import UseCaseFactory
    from src.infrastructure.cad_repository import CadRepository

_repo_var: ContextVar[CadRepository | None] = ContextVar("cad_repo", default=None)
_factory_var: ContextVar[UseCaseFactory | None] = ContextVar("uc_factory", default=None)


def get_repository() -> CadRepository:
    """Return the current request's CadRepository, init if needed."""
    repo = _repo_var.get()
    if repo is None:
        from src.infrastructure.cad_repository import CadRepository

        repo = CadRepository()
        repo.connect()
        _repo_var.set(repo)
    return repo


def set_repository(repo: CadRepository) -> None:
    """Set the current request's CadRepository (for testing)."""
    _repo_var.set(repo)


def get_factory() -> UseCaseFactory:
    """Return the current request's UseCaseFactory, init if needed."""
    factory = _factory_var.get()
    if factory is None:
        from src.application.use_case_factory import UseCaseFactory

        repo = get_repository()
        factory = UseCaseFactory(repo)
        _factory_var.set(factory)
    return factory


def set_factory(factory: UseCaseFactory) -> None:
    """Set the current request's UseCaseFactory (for testing)."""
    _factory_var.set(factory)


def reset() -> None:
    """Reset the context (e.g. on disconnect)."""
    _repo_var.set(None)
    _factory_var.set(None)


__all__ = ["get_factory", "get_repository", "reset", "set_factory", "set_repository"]
