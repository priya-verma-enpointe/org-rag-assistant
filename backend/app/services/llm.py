from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def generate_rag_answer(question: str, context_chunks: list) -> str:
    """
    Sends retrieve chunks + question to LLM to generate cited answer.
    """
    if not context_chunks:
        return "I'm sorry, I couldn't find any relevant information in the organization's documents to answer your question."

    # Combine text chunks for context
    formatted_context = "\n\n".join([
        f"[Source: {chunk.file_name}, Page {chunk.page_number}]: {chunk.chunk_content}"
        for chunk in context_chunks
    ])

    system_prompt = """You are an AI assistant for an Organization Knowledge Base. 
Answer the question based strictly ONLY on the provided context below. 
If the context does not contain enough information, state clearly that you don't know based on the provided documents. Do not hallucinate."""

    user_prompt = f"Context:\n{formatted_context}\n\nQuestion: {question}"

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_prompt,
        config={
            "system_instruction": system_prompt,
            "temperature": 0.2
        }
    )

    return response.text