"""Google Gemini LLM client configuration with rate limiting and error handling."""
import logging
import os
import time
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel


class GeminiClient:
    """Wrapper for Google Gemini with rate limiting and retry logic."""
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.1,
        max_retries: int = 3,
        api_key: Optional[str] = None
    ):
        """Initialize Gemini client.
        
        Args:
            model_name: Gemini model to use (gemini-2.5-pro or gemini-1.5-flash)
            temperature: Sampling temperature (lower = more deterministic)
            max_retries: Maximum number of retries for API calls
            api_key: Google AI Studio API key (uses env var if not provided)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Please set it in .env file or environment variables."
            )
        
        logging.info(f"Initializing Gemini client with model: {model_name}")
        self._client = self._create_client()
    
    def _create_client(self) -> BaseChatModel:
        """Create ChatGoogleGenerativeAI instance."""
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            google_api_key=self.api_key,
            convert_system_message_to_human=True,  # Gemini compatibility
            max_retries=self.max_retries
        )
    
    def get_model(self) -> BaseChatModel:
        """Get the underlying LangChain chat model.
        
        Returns:
            ChatGoogleGenerativeAI instance ready for use in LangGraph.
        """
        return self._client
    
    def invoke_with_retry(self, messages, max_attempts: Optional[int] = None):
        """Invoke model with exponential backoff retry logic.
        
        Args:
            messages: Messages to send to the model
            max_attempts: Override default max_retries
            
        Returns:
            Model response
            
        Raises:
            Exception: If all retry attempts fail
        """
        attempts = max_attempts or self.max_retries
        last_error = None
        
        for attempt in range(attempts):
            try:
                response = self._client.invoke(messages)
                return response
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                    logging.warning(
                        f"Rate limit hit, attempt {attempt + 1}/{attempts}. "
                        f"Waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                else:
                    # For other errors, shorter wait
                    logging.warning(
                        f"API error on attempt {attempt + 1}/{attempts}: {e}"
                    )
                    if attempt < attempts - 1:
                        time.sleep(0.5)
        
        # All retries failed
        logging.error(f"All {attempts} attempts failed. Last error: {last_error}")
        raise last_error


def get_gemini_model(
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.1
) -> BaseChatModel:
    """Convenience function to get a configured Gemini model.
    
    Args:
        model_name: Gemini model to use
        temperature: Sampling temperature
        
    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    client = GeminiClient(model_name=model_name, temperature=temperature)
    return client.get_model()

