from __future__ import annotations

import os
from typing import List, Tuple
from fastapi import HTTPException

from openai import OpenAI
from .token_manager import token_manager


def _get_client() -> OpenAI:
    return OpenAI()


def summarize_text(text: str, level: str = "quick") -> str:
    """Summarize text with token usage restrictions"""
    
    # Text length check removed - no restrictions
    
    # Estimate token usage
    estimated_tokens = token_manager.estimate_tokens(text) + 500  # Add buffer for prompt and response
    
    # Check if request is allowed
    can_proceed, error_msg = token_manager.can_make_request(estimated_tokens, "completion")
    if not can_proceed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    style = (
        "Provide a concise bullet list of key insights and a 2-3 sentence overview."
        if level == "quick"
        else "Provide a structured, detailed summary with sections (Overview, Key Points, Examples, Takeaways)"
    )

    messages = [
        {
            "role": "system",
            "content": "You are an expert learning assistant. Summarize clearly and accurately.",
        },
        {
            "role": "user",
            "content": f"Summarize the following transcript. {style}\n\nTranscript:\n{text}",
        },
    ]

    try:
        completion = client.chat.completions.create(model=model, messages=messages)
        
        # Record actual token usage
        usage = completion.usage
        if usage:
            token_manager.record_usage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens
            )
        
        return completion.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings with token usage restrictions"""
    
    # Check total text length
    total_text = " ".join(texts)
    if not token_manager.check_text_length(total_text, "general"):
        raise HTTPException(
            status_code=400, 
            detail=f"Total text too long for embedding. Maximum allowed: {token_manager.max_text_length} characters"
        )
    
    # Estimate token usage for embeddings
    estimated_tokens = token_manager.estimate_tokens(total_text)
    
    # Check if request is allowed
    can_proceed, error_msg = token_manager.can_make_request(estimated_tokens, "embedding")
    if not can_proceed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    client = _get_client()
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    try:
        response = client.embeddings.create(model=embedding_model, input=texts)
        
        # Record token usage (embeddings don't return usage info, so we estimate)
        token_manager.record_usage(prompt_tokens=0, embedding_tokens=estimated_tokens)
        
        return [d.embedding for d in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")


def ask_question_with_context(question: str, context: str) -> Tuple[str, int, int]:
    """Ask a question with context, returning answer and token usage"""
    
    # Text length checks removed - no restrictions
    
    # Estimate token usage
    estimated_tokens = token_manager.estimate_tokens(question + context) + 200  # Add buffer
    
    # Check if request is allowed
    can_proceed, error_msg = token_manager.can_make_request(estimated_tokens, "completion")
    if not can_proceed:
        raise HTTPException(status_code=429, detail=error_msg)
    
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    prompt = (
        "You are a helpful assistant. Answer the question using ONLY the context.\n"
        "If the answer isn't in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You answer strictly from provided context."},
                {"role": "user", "content": prompt},
            ],
        )
        
        # Record actual token usage
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        
        token_manager.record_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        answer = completion.choices[0].message.content or ""
        return answer, prompt_tokens, completion_tokens
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")


