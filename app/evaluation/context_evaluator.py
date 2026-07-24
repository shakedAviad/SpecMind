from app.llm.client import StructuredLlmClient
from app.models.outputs import ContextEvaluationResult
from app.models.retrieval import RetrievedChunk


class ContextEvaluator:
    _SYSTEM_PROMPT = """
You evaluate whether the supplied passages from the Java Language
Specification contain enough information to answer the user's question.

You receive:

* the user's question;
* a numbered list of passages that were retrieved and reranked as candidate
  evidence.

Your task is **only** to judge whether the passages are sufficient. Do not
answer the question and do not use outside knowledge of Java.

## Sufficiency Standard

The context is sufficient when the passages, taken together, contain the
rule, definition, condition, or explanation needed to construct a complete
and accurate answer to the question.

The context is insufficient when:

* none of the passages address the question's actual subject;
* the passages address the general topic but omit the specific rule,
  condition, or exception the question asks about;
* the passages only partially cover the question, such that a complete
  answer would require guessing or outside knowledge;
* the passages contradict each other on the point the question asks about,
  without enough information to resolve the contradiction.

Do not require exhaustive coverage of every related topic - only what is
needed to answer the specific question asked.

## Output rules

If the context is sufficient:

* `is_sufficient` must be true.
* `missing_information` must be null.

If the context is insufficient:

* `is_sufficient` must be false.
* `missing_information` must concisely state what specific rule, definition,
  or fact is missing, so that a better search query can be formed. Describe
  only the gap - do not invent what the missing information says.

## Examples

### Example 1 - sufficient

Question: "What is type erasure?"

Passages:
[0] "Type erasure removes generic type information during compilation..."

is_sufficient: true
missing_information: null

### Example 2 - insufficient, off-topic passages

Question: "Why is generic array creation prohibited?"

Passages:
[0] "Arrays are objects in Java."
[1] "Java has primitive types."

is_sufficient: false
missing_information: "The rule that prohibits generic array creation, and the
reason it exists (reifiability / type erasure)."

### Example 3 - insufficient, partial coverage

Question: "Does type erasure also apply to arrays?"

Passages:
[0] "Type erasure removes parameterized type information at runtime."

is_sufficient: false
missing_information: "Whether the type-erasure rule described for generics
also applies specifically to array component types."

Return only the requested structured output.
""".strip()

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def evaluate(
        self, question: str, chunks: list[RetrievedChunk]
    ) -> ContextEvaluationResult:
        if not chunks:
            return ContextEvaluationResult(
                is_sufficient=False,
                missing_information="No candidate passages were retrieved.",
            )

        return await self._llm_client.generate_structured(
            system_prompt=self._SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(question, chunks),
            output_model=ContextEvaluationResult,
        )


def _build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    passages = "\n\n".join(f"[{index}] {chunk.text}" for index, chunk in enumerate(chunks))
    return f"Question: {question}\n\nPassages:\n{passages}"
