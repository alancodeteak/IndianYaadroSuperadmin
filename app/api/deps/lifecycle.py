"""
Dependency injection lifecycle (FastAPI request scope).

- ``Session`` (database): one instance per request via ``get_db_session``; closed
  after the request. Repositories receive this session; they must not cache it.
- Services: stateless except for injected ``repository`` + ``session`` references
  tied to the request; new instance per ``Depends(...)`` resolution — safe.
- Do not attach ``Session`` to module-level or lru_cache’d singletons.
"""
