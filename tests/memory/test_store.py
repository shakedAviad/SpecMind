from app.memory.store import MemoryStore


async def test_get_context_returns_empty_list_for_unknown_session() -> None:
    store = MemoryStore()

    context = await store.get_context("session-1")

    assert context == []


async def test_add_facts_makes_them_available_via_get_context() -> None:
    store = MemoryStore()

    await store.add_facts("session-1", ["user is asking about generics"])
    context = await store.get_context("session-1")

    assert context == ["user is asking about generics"]


async def test_add_facts_accumulates_across_multiple_calls() -> None:
    store = MemoryStore()

    await store.add_facts("session-1", ["fact one"])
    await store.add_facts("session-1", ["fact two"])
    context = await store.get_context("session-1")

    assert context == ["fact one", "fact two"]


async def test_sessions_are_isolated_from_each_other() -> None:
    store = MemoryStore()

    await store.add_facts("session-1", ["fact for session one"])
    await store.add_facts("session-2", ["fact for session two"])

    assert await store.get_context("session-1") == ["fact for session one"]
    assert await store.get_context("session-2") == ["fact for session two"]


async def test_get_context_returns_a_copy_not_internal_state() -> None:
    store = MemoryStore()
    await store.add_facts("session-1", ["original fact"])

    context = await store.get_context("session-1")
    context.append("mutated externally")

    assert await store.get_context("session-1") == ["original fact"]
