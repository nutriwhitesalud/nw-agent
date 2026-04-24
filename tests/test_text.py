from company_agent.common.text import chunk_markdown


def test_chunk_markdown_returns_chunks_for_long_text() -> None:
    text = "\n\n".join([f"Paragraph {index} " + ("x" * 120) for index in range(12)])
    chunks = chunk_markdown(text, max_chars=300, overlap_chars=60)

    assert len(chunks) >= 2
    assert chunks[0].index == 0
    assert all(chunk.text for chunk in chunks)

