from app.llm.client import StructuredLlmClient
from app.models.outputs import QueryRewriteResult


class RetrievalQueryRewriter:
    _SYSTEM_PROMPT = """
You revise a search query used to retrieve passages from the Java Language
Specification, after an earlier search failed to find enough evidence to
answer the user's question.

You receive:

* the user's question;
* the previous search query, which did not retrieve sufficient evidence;
* a description of what information was missing from the results, if
  available.

## Task

Produce a single revised search query, `retrieval_query`, that is more
likely to retrieve the missing information.

## Rewriting rules

Base the new query on the missing-information description, not only on the
original question - target the specific gap that was identified.

Prefer precise terminology likely to appear in the specification itself
(for example, defined terms, rule names, or section-level concepts) over
vague or conversational phrasing.

Do not simply repeat the previous query unchanged. Change it meaningfully -
rephrase it, use different or more specific terms, or focus on a narrower
aspect of the topic.

Stay within the scope of the original question. Do not introduce a new
subject that the question did not ask about.

If no missing-information description is available, revise the query to be
more specific and precise than the previous one, based on the question
alone.

## Examples

### Example 1

Question: "Why is generic array creation prohibited?"
Previous query: "generic array creation prohibited"
Missing information: "The rule that prohibits generic array creation, and
the reason it exists (reifiability / type erasure)."

retrieval_query: "reifiable types array store exception generic array
creation"

### Example 2

Question: "Does type erasure also apply to arrays?"
Previous query: "type erasure arrays"
Missing information: "Whether the type-erasure rule described for generics
also applies specifically to array component types."

retrieval_query: "array component type reifiable generic type erasure"

Return only the requested structured output.
""".strip()

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def rewrite(
        self,
        question: str,
        previous_query: str,
        missing_information: str | None,
    ) -> QueryRewriteResult:
        return await self._llm_client.generate_structured(
            system_prompt=self._SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(question, previous_query, missing_information),
            output_model=QueryRewriteResult,
        )


def _build_user_prompt(question: str, previous_query: str, missing_information: str | None) -> str:
    missing = missing_information if missing_information else "(not specified)"
    return (
        f"Question: {question}\n\n"
        f"Previous query: {previous_query}\n\n"
        f"Missing information: {missing}"
    )
