def generate_local_answer(question: str, context: str) -> str:
    """
    Generate a simple answer from retrieved research context.
    This is a lightweight fallback before connecting an LLM.
    """

    if not context.strip():
        return "No relevant research information was found."

    sources = context.split("Source ")

    answer_parts = []

    for source in sources[1:4]:
        lines = source.strip().splitlines()

        content_start = False
        content = []

        for line in lines:
            if line.strip() == "Content:":
                content_start = True
                continue

            if content_start and line.strip():
                content.append(line.strip())

        if content:
            answer_parts.append(" ".join(content))

    if not answer_parts:
        return "Relevant research papers were found, but no usable context was extracted."

    answer = (
        f"Based on the retrieved research papers, {question.lower()} "
        "can be understood from the following research findings:\n\n"
    )

    for index, part in enumerate(answer_parts, start=1):
        answer += f"{index}. {part[:600]}\n\n"

    return answer