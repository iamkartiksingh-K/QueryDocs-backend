from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from app.vector_store.qdrant_store import get_qdrant_vectorstore
from app.core.config import GOOGLE_API_KEY

def query_with_context(user_query):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.4
    )

    retriever = get_qdrant_vectorstore().as_retriever(search_type="similarity", k=5)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    result = qa_chain.invoke(user_query)
    return result
