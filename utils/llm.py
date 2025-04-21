# utils/llm.py
import requests
from typing import List, Optional

def call_llm(prompt: str, context_data: Optional[List[str]] = None) -> str:
    """Call Ollama Gemini 3:27B model with prompt and optional context, return response"""
    # Format context data if provided
    context = ""
    if context_data:
        context = "\n\nRelevant context:\n" + "\n".join(context_data)

    # Create full prompt
    full_prompt = prompt + context

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma3:27b-it-qat",
        "prompt": full_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "No response from Ollama.")
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"Error: {str(e)}"