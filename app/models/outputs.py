from pydantic import BaseModel, Field


class ReasoningResult(BaseModel):
    relevant_points: list[str] = Field(
        description=(
            "Concise, specific facts or rules drawn directly from the supplied "
            "passages that bear on the question. Omit anything not relevant to "
            "the question."
        )
    )

    conclusion: str = Field(
        description=(
            "A concise, direct statement of what the passages establish about "
            "the question, based only on the relevant points. State plainly "
            "when the passages do not support an answer, instead of guessing."
        )
    )

    source_chunk_indexes: list[int] = Field(
        description=(
            "Indexes, from the numbered passage list, of every passage that "
            "supports a relevant point or the conclusion."
        )
    )


class RerankResult(BaseModel):
    relevant_chunk_indexes: list[int] = Field(
        description=(
            "Indexes of the candidate passages that provide meaningful support for "
            "answering the question, exactly matching the provided candidate "
            "indexes, ordered from most useful to least useful. Empty when no "
            "passage provides meaningful support."
        )
    )


class ConversationUnderstandingResult(BaseModel):
    is_follow_up: bool = Field(
        description=(
            "True only when the question cannot be fully understood without "
            "information from an earlier conversation."
        )
    )

    standalone_question: str | None = Field(
        default=None,
        description=(
            "The question as a self-contained question when it is already "
            "standalone. Otherwise, null. Do not invent missing context."
        ),
    )

    missing_context: str | None = Field(
        default=None,
        description=(
            "A concise description of the prior information required to understand "
            "the question. Null when the question is standalone."
        ),
    )


class IntentResolution(BaseModel):
    resolved_question: str = Field(
        description=(
            "The user's question restated as a complete, self-contained question, "
            "with any references resolved using only the supplied memory facts. "
            "If the question is already self-contained, restate it unchanged or "
            "with only light normalization. Never invent information that is not "
            "present in the question or the memory facts."
        )
    )

    retrieval_query: str = Field(
        description=(
            "A concise, search-oriented rendering of the resolved question, "
            "suitable for retrieving passages from the Java Language "
            "Specification. May equal the resolved question when it is already "
            "concise and search-friendly."
        )
    )


class ContextEvaluationResult(BaseModel):
    is_sufficient: bool = Field(
        description=(
            "True only when the supplied passages, taken together, contain enough "
            "evidence to construct a complete and accurate answer to the question."
        )
    )

    missing_information: str | None = Field(
        default=None,
        description=(
            "A concise description of the specific rule, definition, or fact that "
            "is missing from the passages, to guide a better search query. Null "
            "when the context is sufficient. Describe the gap; do not invent what "
            "the missing information says."
        ),
    )


class QueryRewriteResult(BaseModel):
    retrieval_query: str = Field(
        description=(
            "A revised search query for retrieving passages from the Java "
            "Language Specification, targeting the described gap in the "
            "previous search results. Must differ meaningfully from the "
            "previous query."
        )
    )
