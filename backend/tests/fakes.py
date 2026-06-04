from __future__ import annotations

from typing import Any, Dict, List


def _normalise_query(query: str) -> str:
    return " ".join(query.split())


class FakeResult:
    def __init__(self, records: List[Dict[str, Any]]):
        self._records = records
        self._iterator = iter(records)

    async def single(self) -> Dict[str, Any] | None:
        return self._records[0] if self._records else None

    async def consume(self) -> None:
        pass

    def __aiter__(self):
        self._iterator = iter(self._records)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeTx:
    def __init__(self, driver: "FakeNeo4jDriver"):
        self.driver = driver

    async def run(self, query: str, **params: Any) -> FakeResult:
        self.driver.calls.append({"query": _normalise_query(query), "params": params})
        if not self.driver.responses:
            raise AssertionError("No stubbed Neo4j response available")
        return FakeResult(self.driver.responses.pop(0))


class FakeSession:
    def __init__(self, driver: "FakeNeo4jDriver"):
        self.driver = driver

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def execute_write(self, func, *args):
        tx = FakeTx(self.driver)
        return await func(tx, *args)

    async def execute_read(self, func, *args):
        tx = FakeTx(self.driver)
        return await func(tx, *args)


class FakeNeo4jDriver:
    """In-memory stub mimicking the AsyncDriver API shape used in Gate 3 tests."""

    def __init__(self, responses: List[List[Dict[str, Any]]]):
        self.responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def session(self) -> FakeSession:
        return FakeSession(self)


__all__ = ["FakeNeo4jDriver"]
