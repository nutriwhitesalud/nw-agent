from company_agent.rag_api.search import SearchHit, reciprocal_rank_fuse


def test_reciprocal_rank_fuse_merges_rankings() -> None:
    lexical = [
        SearchHit(
            chunk_id="a",
            document_id="doc-1",
            chunk_index=0,
            title="Doc A",
            content="A",
            source_uri="doc-a",
            metadata={},
            score=0.9,
        ),
        SearchHit(
            chunk_id="b",
            document_id="doc-2",
            chunk_index=0,
            title="Doc B",
            content="B",
            source_uri="doc-b",
            metadata={},
            score=0.8,
        ),
    ]
    semantic = [
        SearchHit(
            chunk_id="b",
            document_id="doc-2",
            chunk_index=0,
            title="Doc B",
            content="B",
            source_uri="doc-b",
            metadata={},
            score=0.7,
        )
    ]

    fused = reciprocal_rank_fuse({"lexical": lexical, "semantic": semantic}, top_k=2)

    assert fused[0].chunk_id == "b"
    assert fused[0].matched_by == {"lexical", "semantic"}

