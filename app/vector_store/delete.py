from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FilterSelector
from app.core.config import QDRANT_URL, QDRANT_API_KEY


# Initialize client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Use the correct points selector object
client.delete(
    collection_name="docs",
    points_selector=FilterSelector(
        filter=Filter(must=[])
    )
)

print("✅ All embeddings from 'docs' have been deleted.")
