"""LLM Provider abstraction supporting Gemini and Groq through LangChain.

Configuration via environment variables:
    LLM_PROVIDER: "gemini" or "groq"
    GEMINI_API_KEY: API key for Google Gemini
    GROQ_API_KEY: API key for Groq
    MODEL_NAME: Model name to use (provider-specific)
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class LLMProviderError(Exception):
    """Raised when LLM provider configuration or invocation fails."""
    pass


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.0,
):
    """Get a LangChain LLM instance based on configuration.
    
    Args:
        provider: Override LLM_PROVIDER env var ("gemini" or "groq")
        model_name: Override MODEL_NAME env var
        temperature: Model temperature (default 0.0 for deterministic output)
    
    Returns:
        A LangChain chat model instance
    
    Raises:
        LLMProviderError: If provider is not configured or fails to initialize
    """
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    
    if provider == "gemini":
        return _get_gemini(model_name, temperature)
    elif provider == "groq":
        return _get_groq(model_name, temperature)
    else:
        raise LLMProviderError(
            f"Unknown LLM provider: '{provider}'. "
            f"Set LLM_PROVIDER to 'gemini' or 'groq'."
        )


def _get_gemini(model_name: Optional[str], temperature: float):
    """Initialize Google Gemini through LangChain."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMProviderError(
            "GEMINI_API_KEY not set. Please set it in your .env file."
        )
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise LLMProviderError(
            "langchain-google-genai is not installed. "
            "Run: pip install langchain-google-genai"
        )
    
    model = model_name or os.getenv("MODEL_NAME", "gemini-2.0-flash")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=False,
        )
        return llm
    except Exception as e:
        raise LLMProviderError(f"Failed to initialize Gemini: {e}")


def _get_groq(model_name: Optional[str], temperature: float):
    """Initialize Groq through LangChain."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMProviderError(
            "GROQ_API_KEY not set. Please set it in your .env file."
        )
    
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        raise LLMProviderError(
            "langchain-groq is not installed. "
            "Run: pip install langchain-groq"
        )
    
    model = model_name or os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
    
    try:
        llm = ChatGroq(
            model=model,
            groq_api_key=api_key,
            temperature=temperature,
        )
        return llm
    except Exception as e:
        raise LLMProviderError(f"Failed to initialize Groq: {e}")
