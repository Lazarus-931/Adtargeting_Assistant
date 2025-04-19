# utils/parsing.py
import json
import re
from typing import Dict, Any, Optional


def extract_json(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    try:
        # Look for JSON object pattern in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        # If no JSON found, try to parse the entire response
        return json.loads(response)
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        # Return empty dict if no valid JSON found
        return {}


def format_output(response: str) -> str:
    """Format the LLM response for display"""
    # Clean up response to keep formatted sections
    formatted_response = response
    
    # Remove any JSON blocks if they appear at the end
    json_block_pattern = r'\n```json[\s\S]*```\s*$'
    formatted_response = re.sub(json_block_pattern, '', formatted_response)
    
    # Remove any raw JSON if it appears at the end
    json_pattern = r'\n\{[\s\S]*\}\s*$'
    formatted_response = re.sub(json_pattern, '', formatted_response)
    
    return formatted_response.strip()