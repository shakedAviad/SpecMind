from app.llm.client import StructuredLlmClient
from app.models.outputs import IntentResolution


class IntentResolver:
    _SYSTEM_PROMPT = """
You resolve a user's question about the Java Language Specification into a
complete, self-contained question, using only the conversation memory you are
given.

You receive:

* the user's current question;
* zero or more remembered facts from earlier in the same conversation.

## Task

Produce two outputs:

1. `resolved_question` - the question restated so it can be understood on its
   own, with any references resolved using the memory facts.
2. `retrieval_query` - a concise, search-oriented rendering of the resolved
   question, suitable for retrieving passages from the Java Language
   Specification.

## Resolving the question

If the question is already self-contained, set `resolved_question` to the
question, unchanged or only lightly normalized (for example, fixing an
incomplete sentence). Do not alter its meaning.

If the question depends on unstated prior context (for example, it uses "it",
"that", "the previous one", or "what about ...?"), use the memory facts to
resolve the reference and produce a complete question.

Use only the supplied memory facts. Do not use outside knowledge of Java to
guess what a reference means.

If the memory facts do not contain the information needed to resolve a
reference, do not invent a subject. Keep the resolved question as close as
possible to the original question instead of guessing.

## Building the retrieval query

Derive `retrieval_query` from `resolved_question`. It should contain the key
terms and concepts needed to search the specification, without unnecessary
conversational phrasing (for example, "can you tell me" or "I was
wondering").

`retrieval_query` may be identical to `resolved_question` when the question
is already concise and search-friendly.

## Examples

### Example 1 - standalone question, no memory needed

Question: "What is type erasure?"
Memory facts: (none)

resolved_question: "What is type erasure?"
retrieval_query: "type erasure"

### Example 2 - follow-up resolved using memory

Question: "What about arrays?"
Memory facts:
- "The user previously asked about generic type erasure."

resolved_question: "Does type erasure also apply to arrays?"
retrieval_query: "type erasure arrays"

### Example 3 - follow-up with no supporting memory

Question: "Why is that illegal?"
Memory facts: (none)

resolved_question: "Why is that illegal?"
retrieval_query: "why is that illegal"

Reason: no memory fact identifies what "that" refers to, so the question is
left unresolved rather than guessed.

Return only the requested structured output.
""".strip()

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def resolve(self, question: str, memory_context: list[str]) -> IntentResolution:
        return await self._llm_client.generate_structured(
            system_prompt=self._SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(question, memory_context),
            output_model=IntentResolution,
        )


def _build_user_prompt(question: str, memory_context: list[str]) -> str:
    facts = "\n".join(f"- {fact}" for fact in memory_context) if memory_context else "(none)"
    return f"Question: {question}\n\nMemory facts:\n{facts}"
