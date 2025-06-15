import os
from dotenv import load_dotenv
from openai import OpenAI
from app.vector_store.qdrant_store import get_qdrant_vectorstore
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def query_with_context(user_query: str, user_id: str) -> dict:
    # Step 1: Retrieve only this user's chunks from Qdrant
    vectorstore = get_qdrant_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4,
            "filter": Filter(
                must=[FieldCondition(key="metadata.user_id", match=MatchValue(value=user_id))]
            )
        }
    )

    docs = retriever.invoke(user_query)

    for i, doc in enumerate(docs):
        print(f"🔎 Chunk {i+1}: {doc.page_content[:100]}...")
        print("📎 Metadata:", doc.metadata)


    # Step 2: Build a compact context
    context = "\n\n".join([doc.page_content.strip() for doc in docs if doc.page_content.strip()])

    # Step 3: Format prompt for better reasoning and accuracy
    messages = [
        {
            "role": "system",
            "content": (
                "You are a knowledgeable AI assistant powered by Gemini Flash. "
                "Use the provided context below to answer the user's question as accurately, clearly, and concisely as possible. "
                "If the context does not contain enough information, say so politely."
            )
        },
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\n"
                f"Question: {user_query}\n\n"
                "Answer only using the given context. Be brief and to the point."
            )
        }
    ]

    # Step 4: Call Gemini Flash 2.0 via OpenAI-style SDK
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        response_format={"type": "text"},
        messages=messages
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "source_docs": [doc.metadata for doc in docs]
    }
