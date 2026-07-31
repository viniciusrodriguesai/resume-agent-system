from __future__ import annotations

from resume_ai.config import Settings


def main() -> None:
    settings = Settings()
    print("Downloading the embedding model...")
    from sentence_transformers import SentenceTransformer
    SentenceTransformer(settings.embedding_model)

    print("Downloading the CrossEncoder reranker...")
    from sentence_transformers import CrossEncoder
    CrossEncoder(settings.reranker_model)

    print("Models are cached locally and ready.")


if __name__ == "__main__":
    main()
