import numpy as np

from stewardlens.retrieval import SentenceEmbeddingRetriever, TfidfRetriever


class Encoder:
    def encode(self, texts):
        return np.asarray([[1.0, 0.0] if "collision" in text else [0.0, 1.0] for text in texts])


def test_tfidf_retriever_is_stable():
    retriever = TfidfRetriever(["collision", "rejoin"], ["avoidable collision", "unsafe rejoin"])
    assert retriever.search("collision") == ["collision"]


def test_embedding_retriever_falls_back_without_download():
    retriever = SentenceEmbeddingRetriever(
        ["collision", "rejoin"], ["avoidable collision", "unsafe rejoin"]
    )
    assert retriever.backend == "tfidf-fallback"
    assert retriever.search("unsafe rejoin", 1) == ["rejoin"]


def test_embedding_retriever_supports_injected_encoder():
    retriever = SentenceEmbeddingRetriever(
        ["collision", "rejoin"], ["collision", "rejoin"], encoder=Encoder()
    )
    assert retriever.backend == "sentence-embedding"
    assert retriever.search("collision", 1) == ["collision"]
