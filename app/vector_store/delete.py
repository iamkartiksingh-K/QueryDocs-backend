from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FilterSelector

# Initialize client
client = QdrantClient(
    url="https://f69bf110-493b-4940-bf0a-ae80fbd5a357.europe-west3-0.gcp.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0._aZaavXaH9k6DfQ8F8JXBp2OAUkQEh-pMCR-Y4rcVZ0"
)

# Use the correct points selector object
client.delete(
    collection_name="docs",
    points_selector=FilterSelector(
        filter=Filter(must=[])
    )
)

print("✅ All embeddings from 'docs' have been deleted.")
