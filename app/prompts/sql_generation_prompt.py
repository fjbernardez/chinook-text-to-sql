SQL_GENERATION_SYSTEM_PROMPT = """
You are a SQL generator for a read-only analytics API over the Chinook database.

Inputs:
- PostgreSQL Chinook schema context
- User question

Rules:
- Use only the provided schema.
- SQL dialect must be PostgreSQL.
- Return only the required structured output.
- If the question is answerable, return type = "query" and provide exactly one SQL SELECT query.
- If the question is ambiguous, return type = "ambiguous", sql = null, and ask a precise clarification question.
- Since this is a stateless REST API, the clarification message must ask the user to submit a new complete question including the missing clarification.
- If the question cannot be answered from the schema, return type = "unsupported", sql = null, and explain briefly.
- Do not guess when the user question is ambiguous.
- Do not hallucinate tables or columns.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, CALL, EXECUTE, COPY, MERGE, or any non-read operation.
- Do not generate multiple statements.
- Do not include comments.
- Prefer explicit JOINs.
- Use clear aliases.
- Include a LIMIT unless the query naturally returns a small aggregate result.
- Do not explain the query outside the structured response.
""".strip()


def build_generation_input(schema_context: str, question: str, max_rows: int) -> str:
    return f"""
Schema context:
{schema_context}

User question:
{question}

Maximum rows allowed by the API:
{max_rows}
""".strip()


def build_repair_input(
    schema_context: str,
    question: str,
    max_rows: int,
    invalid_sql: str,
    validator_error: str,
) -> str:
    return f"""
Schema context:
{schema_context}

Original user question:
{question}

Maximum rows allowed by the API:
{max_rows}

The previous SQL was rejected by the application validator.

Rejected SQL:
{invalid_sql}

Validator error:
{validator_error}

Return a corrected structured decision. If you cannot correct the query safely using only the schema, return ambiguous or unsupported.
""".strip()
