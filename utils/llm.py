# utils/improved_llm.py
import os
import requests
import json
from typing import List, Dict, Any, Optional, Union
import time

class LLMConfig:
    """Configuration for LLM providers"""
    def __init__(self, 
                 provider: str = "ollama", 
                 model: str = "gemma3:27b-it-qat",
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 temperature: float = 0.2,
                 max_tokens: int = 2000,
                 timeout: int = 120):
        
        self.provider = provider.lower()
        self.model = model
        
        # Set API key from arguments or environment
        if api_key:
            self.api_key = api_key
        else:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            else:
                self.api_key = None
        
        # Set API base
        if api_base:
            self.api_base = api_base
        else:
            if self.provider == "ollama":
                self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
            elif self.provider == "openai":
                self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            elif self.provider == "anthropic":
                self.api_base = os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com/v1")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout


class LLMConnector:
    """Unified connector for various LLM providers"""
    
    def __init__(self, config: LLMConfig):
        """Initialize with configuration"""
        self.config = config
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration"""
        # Check provider
        valid_providers = ["ollama", "openai", "anthropic"]
        if self.config.provider not in valid_providers:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}. "
                             f"Supported providers: {', '.join(valid_providers)}")
        
        # Check API key for providers that require it
        if self.config.provider in ["openai", "anthropic"] and not self.config.api_key:
            raise ValueError(f"API key required for {self.config.provider}")
    
    def call(self, 
             prompt: str, 
             context_data: Optional[List[str]] = None,
             system_message: Optional[str] = None) -> str:
        """Call LLM with prompt and optional context, return response"""
        
        # Format context data if provided
        context = ""
        if context_data:
            # Limit context length to avoid token issues
            total_context = "\n".join(context_data)
            if len(total_context) > 10000:  # Adjust based on token limits
                # Truncate or chunk the context
                context = "\n\nRelevant context (truncated):\n" + total_context[:10000]
            else:
                context = "\n\nRelevant context:\n" + total_context

        # Create full prompt
        full_prompt = prompt + context

        # Dispatch to appropriate provider handler
        if self.config.provider == "ollama":
            return self._call_ollama(full_prompt, system_message)
        elif self.config.provider == "openai":
            return self._call_openai(full_prompt, system_message)
        elif self.config.provider == "anthropic":
            return self._call_anthropic(full_prompt, system_message)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _call_ollama(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call Ollama API"""
        url = f"{self.config.api_base}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "temperature": self.config.temperature,
            "stream": False
        }
        
        # Add system message if provided
        if system_message:
            payload["system"] = system_message
        
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json().get("response", "No response from Ollama.")
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return f"Error: {str(e)}"
    
    def _call_openai(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call OpenAI API"""
        url = f"{self.config.api_base}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "No response from OpenAI.")
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return f"Error: {str(e)}"
    
    def _call_anthropic(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call Anthropic API"""
        url = f"{self.config.api_base}/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        # Add system message if provided
        if system_message:
            payload["system"] = system_message
        
        try:
            response = requests
