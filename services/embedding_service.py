import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from app_settings import GEMINI_API_KEY
from google import genai
from google.genai import types


# Embedding Service Object (adapted implementation from classes)
class EmbeddingService:
    """
    Service for generating text embeddings using Google Gemini's embedding model.

    Uses gemini-embedding-001 with Matryoshka Representation Learning (MRL)
    to generate flexible-dimension embeddings for semantic search.
    """

    def __init__(self, output_dimensionality: int = 3072):
        """
        Initialize the EmbeddingService.

        Args:
            output_dimensionality: Embedding vector dimensions (128-3072).
                                 Recommended: 768, 1536, or 3072.
                                 Default: 3072 for optimal performance.
        """
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-embedding-001"
        self.output_dimensionality = output_dimensionality

    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed (max 2,048 tokens)

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If text exceeds token limit
            Exception: If API call fails

        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_embedding("Hello world")
            >>> len(embedding)
            768
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.output_dimensionality
                )
            )

            # Extract the embedding values
            embedding = result.embeddings[0].values

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise 

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Note: Due to API rate limits (100 RPM free tier), this processes
        texts sequentially. For production use with many texts, consider
        implementing rate limiting and batching strategies.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text

        Example:
            >>> service = EmbeddingService()
            >>> texts = ["First text", "Second text"]
            >>> embeddings = service.generate_embeddings_batch(texts)
            >>> len(embeddings)
            2
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = self.embed_query(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    print(f"✅ Processed {i + 1}/{len(texts)} embeddings")

            except Exception as e:
                print(f"❌ Failed to embed text {i}: {text[:50]}... Error: {e}")
                # Append None for failed embeddings to maintain index alignment
                embeddings.append(None)

        print(f"✅ Completed: {len([e for e in embeddings if e is not None])}/{len(texts)} embeddings generated")
        return embeddings