from langchain_openai import ChatOpenAI
from model.streaming import StreamingCallback
from providers.base_provider import BaseProvider
import logging

class OpenAIProvider(BaseProvider):
    """
    Provider implementation for OpenAI Models
    """
    def __init__(self, model_id: str, api_key: str, streaming_callback: StreamingCallback, max_tokens: int = 1000, temperature: float = .7) -> None:
        """
        Initialize the OpenAIProvider with necessary parameters.
        Parameters:
        model_id (str): The model identifier for OpenAI.
        api_key (str): API key for accessing OpenAI models.
        streaming_callback: Callback handler for streaming responses.
        max_tokens (int, optional): Maximum number of tokens in the model's response. Defaults to 1000.
        temperature (float, optional): Temperature to set for the model. Defaults to 0.7.
        """
        self.model_id = model_id
        self.api_key = api_key
        self.streaming_callback = streaming_callback
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Initialized OpenAIProvider with model_id: {self.model_id}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")

    def get_llm(self) -> ChatOpenAI:
        """
        Instantiate and return the ChatOpenAI LLM.
        Returns:
        ChatOpenAI: An instance of ChatOpenAI configured with the specified model and token limit.
        """
        try:
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model_id,
                streaming=True,
                callbacks=[self.streaming_callback],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            self.logger.debug(f"ChatOpenAI LLM initialized with model_id: {self.model_id}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")
            return llm
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise e