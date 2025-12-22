import os
from app_settings import GEMINI_API_KEY
from google import genai
from google.genai import types
from langfuse import observe

# Embedding Service Object (adapted implementation from classes)
class EmbeddingService:
    '''
    Service for generating text embeddings using Google Gemini's embedding model (gemini-embedding-001).
    '''
    def __init__(self, output_dimensionality: int = 3072):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-embedding-001"
        self.output_dimensionality = output_dimensionality

    @observe(as_type="embedding")
    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given prompt/article/title.
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
        Generate embeddings for multiple inputs.
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = self.embed_query(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(texts)} embeddings")

            except Exception as e:
                print(f"Failed to embed text {i}: {text[:50]}... Error: {e}")
                # Append None for failed embeddings to maintain index alignment
                embeddings.append(None)

        print(f"Completed: {len([e for e in embeddings if e is not None])}/{len(texts)} embeddings generated")
        return embeddings