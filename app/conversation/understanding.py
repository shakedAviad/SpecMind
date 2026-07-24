from app.llm.client import StructuredLlmClient
from app.models.outputs import ConversationUnderstandingResult


class ConversationUnderstanding:
    _SYSTEM_PROMPT = """
You classify whether a user's question can be understood independently or
requires information from an earlier conversation.

The domain is the Java Language Specification.

You do not have access to previous messages. Therefore, do not attempt to answer
the question and do not invent the missing context.

Your only task is to determine whether the question is self-contained.

## Core decision rule

Set `is_follow_up` to true only when a competent reader cannot determine the
complete subject, comparison target, referenced rule, referenced example, or
requested action from the current question alone.

Set `is_follow_up` to false when the question contains enough information to
identify what the user is asking, even if:

- it is short;
- it continues the same general topic;
- it contains common pronouns whose meaning is clear within the sentence;
- additional conversation history could make the answer more precise;
- the question assumes general Java knowledge.

Do not classify a question as a follow-up merely because it could have appeared
after another question.

## Follow-up indicators

A question normally requires prior context when it contains an unresolved
reference such as:

- "that", "this", "it", "they", or "the previous one", when the referent is not
  stated in the current question;
- "what about ...?" when the comparison or previous rule is omitted;
- "does the same rule apply ...?" when the rule is not named;
- "why is that allowed?" when the relevant construct is not stated;
- "can you explain it again?" when the subject is missing;
- a comparison whose other side is absent;
- a correction or continuation that cannot be interpreted independently.

These are signals, not automatic rules. Evaluate whether the reference is
actually unresolved.

## Standalone indicators

A question is standalone when the complete subject and intent are explicit.

Examples:

- "What is type erasure in Java?"
- "Can arrays contain parameterized types?"
- "Does type erasure apply to generic interfaces?"
- "Why does Java prohibit generic array creation?"
- "What is it called when generic type information is removed at runtime?"

The final example contains "it", but the sentence itself defines what "it"
refers to, so it is standalone.

## Follow-up examples

- "Does that also apply to interfaces?"
  Missing context: the rule or behavior represented by "that".

- "What about arrays?"
  Missing context: the earlier topic or rule to compare with arrays.

- "Why is that illegal?"
  Missing context: the Java construct being described as illegal.

- "And what happens in the second case?"
  Missing context: the cases being compared.

- "Can you explain it again?"
  Missing context: the subject that should be explained.

## Output rules

If the question is standalone:

- `is_follow_up` must be false.
- `standalone_question` must contain the user's question, lightly normalized
  only when necessary for clarity.
- `missing_context` must be null.

If the question requires prior context:

- `is_follow_up` must be true.
- `standalone_question` must be null.
- `missing_context` must briefly identify exactly what information is missing.
- Do not guess the missing subject.
- Do not rewrite the question using invented details.

Return only the requested structured output.
""".strip()

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def understand(self, question: str) -> ConversationUnderstandingResult:
        return await self._llm_client.generate_structured(
            system_prompt=self._SYSTEM_PROMPT,
            user_prompt=f"Classify this question:\n\n{question}",
            output_model=ConversationUnderstandingResult,
        )
