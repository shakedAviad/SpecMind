class MemoryStore:
    def __init__(self) -> None:
        self._facts_by_session: dict[str, list[str]] = {}

    async def get_context(self, session_id: str) -> list[str]:
        return list(self._facts_by_session.get(session_id, []))

    async def add_facts(self, session_id: str, facts: list[str]) -> None:
        self._facts_by_session.setdefault(session_id, []).extend(facts)
