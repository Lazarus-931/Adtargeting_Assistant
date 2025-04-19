# utils/llm.py
import os
import json
from typing import Dict, Any, List, Optional

# Import your preferred LLM client
# For example, OpenAI
import openai


def get_llm_client():
    """Get the LLM client with API key"""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


def call_llm(prompt: str, context_data: Optional[List[str]] = None) -> str:
    """Call LLM with prompt and optional context, return response"""
    client = get_llm_client()
    
    # Format context data if provided
    context = ""
    if context_data:
        context = "\n\nRelevant context:\n" + "\n".join(context_data)
    
    # Create full prompt
    full_prompt = prompt + context
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Use your preferred model
            messages=[
                {"role": "system", "content": "You are a specialized audience segmentation assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,  # Lower temperature for more consistent results
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return f"Error: {str(e)}"