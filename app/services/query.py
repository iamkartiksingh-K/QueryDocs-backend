import os
from dotenv import load_dotenv
from openai import OpenAI
from app.vector_store.qdrant_store import get_qdrant_vectorstore

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
print(API_KEY)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def query_with_context(user_query: str) -> dict:
    # Step 1: Retrieve similar documents from Qdrant
    vectorstore = get_qdrant_vectorstore()
    retriever = vectorstore.as_retriever(search_type="similarity", k=4)
    docs = retriever.get_relevant_documents(user_query)

    # Step 2: Build context from docs
    context = "\n\n".join([doc.page_content for doc in docs])

    # Step 3: Format prompt
    system_prompt = "You are an AI assistant using Gemini Flash. Use the provided context to answer the question accurately."

    messages = [
        { "role": "system", "content": system_prompt },
        { "role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}" }
    ]

    # Step 4: Call Gemini Flash 2.0 using OpenAI-style interface
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        response_format={"type": "text"},  # or "json_object" if needed
        messages=messages
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "source_docs": [doc.metadata for doc in docs]
    }
