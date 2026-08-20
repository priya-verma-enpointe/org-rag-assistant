import json
import asyncio
from typing import AsyncGenerator
from google import genai
from app.core.config import settings

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


async def generate_rag_response_stream(
    query: str, 
    context_chunks: list
) -> AsyncGenerator[str, None]:
    """
    Asynchronous generator function that streams Gemini response in SSE format.
    Yields chunks like: data: {"text": "..."}\n\n
    Also yields sources at the start and data: [DONE]\n\n at completion.
    """
    try:
        # 1. Format and yield sources first
        sources = []
        if context_chunks:
            seen_sources = set()
            for chunk in context_chunks:
                source_key = (chunk.file_name, chunk.page_number)
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    sources.append({
                        "file_name": chunk.file_name,
                        "page": chunk.page_number
                    })
        
        yield f"data: {json.dumps({'sources': sources})}\n\n"
        
        # 2. If no context, yield fallback and finish
        if not context_chunks:
            fallback = "I'm sorry, I couldn't find any relevant information in the organization's documents to answer your question."
            yield f"data: {json.dumps({'text': fallback})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 3. Format context chunks
        formatted_context = "\n\n".join([
            f"[Source: {chunk.file_name}, Page {chunk.page_number}]: {chunk.chunk_content}"
            for chunk in context_chunks
        ])

        system_prompt = """You are an AI assistant for an Organization Knowledge Base. 
Answer the question based strictly ONLY on the provided context below. 
If the context does not contain enough information, state clearly that you don't know based on the provided documents. Do not hallucinate."""

        user_prompt = f"Context:\n{formatted_context}\n\nQuestion: {query}"

        # 4. Stream response from Gemini using Google GenAI client.aio
        response_stream = await client.aio.models.generate_content_stream(
            model="gemini-3.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.2
            }
        )
        
        async for chunk in response_stream:
            text = chunk.text or ""
            if text:
                yield f"data: {json.dumps({'text': text})}\n\n"

        yield "data: [DONE]\n\n"

    except asyncio.CancelledError:
        print("Client disconnected, closing streaming generation.")
        raise
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"