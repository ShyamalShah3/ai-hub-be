from langchain_openai import ChatOpenAI
from model.streaming import StreamingCallback
from providers.base_provider import BaseProvider
import logging
        
class OpenAIProvider(BaseProvider):
    """
    Provider implementation for OpenAI Models
    """

    def __init__(self, model_id: str, api_key: str, streaming_callback: StreamingCallback) -> None:
        """
        Initialize the OpenAIProvider with necessary parameters.

        Parameters:
            model_id (str): The model identifier for OpenAI.
            openai_api_key (str): API key for accessing OpenAI models.
            streaming_callback: Callback handler for streaming responses.
        """
        self.model_id = model_id
        self.api_key = api_key
        self.streaming_callback = streaming_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Initialized OpenAIProvider with model_id: {self.model_id}")
    
    def get_llm(self) -> ChatOpenAI:
        """
        Instantiate and return the ChatOpenAI LLM.

        Returns:
            ChatOpenAI: An instance of ChatOpenAI configured with the specified model.
        """
        try:
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model_id,
                streaming=True,
                callbacks=[self.streaming_callback]
            )
            self.logger.debug(f"ChatOpenAI LLM initialized with model_id: {self.model_id}")
            return llm
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise e