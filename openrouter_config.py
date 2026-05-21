"""
OpenRouter Configuration Module

This module provides configuration and client setup for OpenRouter API integration.
OpenRouter provides access to multiple LLM providers through a unified OpenAI-compatible API.
"""

import os
import time
from openai import OpenAI, AuthenticationError, RateLimitError
from typing import Optional, Callable, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

class OpenRouterConfig:
    """Configuration class for OpenRouter API settings with role-based model selection."""
    
    # Role-based model configuration
    # All roles use Gemini Flash 3 for speed
    ROLE_MODELS = {
        "narration": "google/gemini-3-flash-preview",
        "spark_generation": "google/gemini-3-flash-preview",
        "decision_making": "google/gemini-3-flash-preview",
        "scene_creation": "google/gemini-3-flash-preview",
        "action_interpretation": "google/gemini-3-flash-preview",
        "coordination": "google/gemini-3-flash-preview",
        "data_management": "google/gemini-3-flash-preview",
        "output_formatting": "google/gemini-3-flash-preview",
        "memory_creation": "google/gemini-3-flash-preview",
        "layout_generation": "google/gemini-3-flash-preview",
        "default": "google/gemini-3-flash-preview"
    }
    
    # OpenRouter API settings
    BASE_URL = "https://openrouter.ai/api/v1"
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Get OpenRouter API key from environment variables."""
        # 1. Try standard env var
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            return key.strip()
        return None
    
    @classmethod
    def create_client(cls) -> OpenAI:
        """Create and return an OpenRouter client."""
        api_key = cls.get_api_key()
        if not api_key:
            # Detailed error to help debug
            env_path = os.path.abspath(".env")
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is not set.\n"
                f"Please check your .env file at: {env_path}\n"
                "It should contain: OPENROUTER_API_KEY=sk-or-v1-..."
            )
        
        return OpenAI(
            base_url=cls.BASE_URL,
            api_key=api_key,
        )
    
    @classmethod
    def get_model_for_role(cls, role: str) -> str:
        """Get the model name for a specific role."""
        return cls.ROLE_MODELS.get(role, cls.ROLE_MODELS["default"])
    
    @classmethod
    def get_default_model(cls) -> str:
        """Get the default model name."""
        return cls.ROLE_MODELS["default"]
    
    @classmethod
    def create_role_client(cls, role: str) -> OpenAI:
        """Create and return an OpenRouter client configured for a specific role."""
        return cls.create_client()

# Convenience functions for creating clients
def create_openrouter_client() -> OpenAI:
    """Create and return an OpenRouter client with default model."""
    return OpenRouterConfig.create_client()

def create_role_client(role: str) -> OpenAI:
    """Create and return an OpenRouter client for a specific role."""
    return OpenRouterConfig.create_role_client(role)

# ============================================================================
# CENTRALIZED RETRY CONFIGURATION
# ============================================================================
# All LLM calls should use these settings for consistency

class RetryConfig:
    """Centralized retry configuration for all LLM calls."""
    
    # Default retry settings
    MAX_RETRIES = 5  # Number of retry attempts
    INITIAL_DELAY = 0.1  # Initial delay in seconds (fast retries)
    DELAY_MULTIPLIER = 1.0  # Multiply delay by (attempt + 1) * this value
    TEMP_INCREMENT = 0.05  # Increase temperature by this much per retry
    
    # Specific overrides for different call types
    CRITICAL_MAX_RETRIES = 10  # For critical calls like internal voice
    QUICK_MAX_RETRIES = 3  # For quick coordination calls
    
    @classmethod
    def get_delay(cls, attempt: int) -> float:
        """Calculate delay for a given attempt number (0-indexed)."""
        return cls.INITIAL_DELAY * (attempt + 1) * cls.DELAY_MULTIPLIER
    
    @classmethod
    def get_temperature_adjustment(cls, base_temp: float, attempt: int) -> float:
        """Calculate adjusted temperature for a given attempt."""
        return base_temp + (attempt * cls.TEMP_INCREMENT)


def retry_with_backoff(func: Callable, max_retries: int = 3, initial_delay: float = 1.0) -> Any:
    """
    Retry a function with exponential backoff on rate limit or auth errors.
    
    Args:
        func: Function to retry (should be a lambda that calls the API)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
    
    Returns:
        The result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except (AuthenticationError, RateLimitError) as e:
            last_exception = e
            
            # Check if it's a "User not found" 401 error (likely rate limiting)
            if isinstance(e, AuthenticationError) and "User not found" in str(e):
                if attempt < max_retries:
                    # Silent retry for rate limits
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            
            # For other auth errors or if we've exhausted retries, raise immediately
            raise
        except Exception as e:
            # For non-rate-limit errors, raise immediately
            raise
    
    # If we get here, all retries failed
    raise last_exception


def robust_llm_call(
    client: OpenAI,
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    max_retries: int = None,
    response_format: dict = None,
    timeout: int = 30,
    call_name: str = "LLM call"
) -> Optional[str]:
    """
    Make a robust LLM call with consistent retry logic.
    
    Args:
        client: OpenAI client
        messages: List of message dicts
        model: Model to use (defaults to coordination model)
        temperature: Base temperature
        max_tokens: Max tokens for response
        max_retries: Override default retry count
        response_format: Optional response format (e.g., {"type": "json_object"})
        timeout: Request timeout in seconds
        call_name: Name for logging purposes
        
    Returns:
        Response content string, or None if all retries fail
    """
    if max_retries is None:
        max_retries = RetryConfig.MAX_RETRIES
    
    if model is None:
        model = OpenRouterConfig.get_model_for_role("coordination")
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Adjust temperature for retries
            adjusted_temp = RetryConfig.get_temperature_adjustment(temperature, attempt)
            
            # Build call kwargs
            call_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": adjusted_temp,
                "max_tokens": max_tokens,
                "timeout": timeout
            }
            if response_format:
                call_kwargs["response_format"] = response_format
            
            response = client.chat.completions.create(**call_kwargs)
            
            # Handle potential None responses from some models
            if not response or not response.choices:
                last_error = "No choices in response"
                if attempt < max_retries - 1:
                    delay = RetryConfig.get_delay(attempt)
                    print(f"\033[93m⚠️ [{call_name}] No choices in response (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s...\033[0m")
                    time.sleep(delay)
                continue
            
            message = response.choices[0].message
            content = message.content if message else None
            
            # Some reasoning models put content in reasoning_content
            if not content and hasattr(message, 'reasoning_content') and message.reasoning_content:
                content = message.reasoning_content
            
            if content and content.strip():
                return content.strip()
            
            # Empty response - retry
            last_error = "Empty response from LLM"
            if attempt < max_retries - 1:
                delay = RetryConfig.get_delay(attempt)
                print(f"\033[93m⚠️ [{call_name}] Empty response (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s...\033[0m")
                time.sleep(delay)
                
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                delay = RetryConfig.get_delay(attempt)
                print(f"\033[93m⚠️ [{call_name}] Attempt {attempt + 1}/{max_retries} failed: {e}, retrying in {delay:.1f}s...\033[0m")
                time.sleep(delay)
    
    # All retries exhausted
    print(f"\033[93m⚠️ [{call_name}] Failed after {max_retries} attempts: {last_error}\033[0m")
    return None
