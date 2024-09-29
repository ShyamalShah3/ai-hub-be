import boto3
from langchain_aws import ChatBedrock
from model.streaming import StreamingCallback
from providers.base_provider import BaseProvider
import os
import logging

class BedrockProvider(BaseProvider):
    """
    Provider implementation for AWS Bedrock Models
    """

    def __init__(self, model_id: str, streaming_callback: StreamingCallback, max_tokens: int = 1000, temperature: float = .7, region: str = None) -> None:
        """
        Initialize the BedrockProvider with necessary parameters.

        Parameters:
            model_id (str): The model identifier for Bedrock.
            streaming_callback (StreamingCallback): Callback handler for streaming responses.
            max_tokens (int, optional): Maximum number of tokens in the model's response. Defaults to 1000.
            temperature (float, optional): Temperature to set for the model. Defaults to 0.7.
            region (str, optional): AWS region where Bedrock is deployed. Defaults to environment variable.
        """
        self.model_id = model_id
        self.streaming_callback = streaming_callback
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.region = region or os.environ.get('REGION', 'us-west-2')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Initialized BedrockProvider with model_id: {self.model_id}, region: {self.region}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")
    
    def get_llm(self) -> ChatBedrock:
        """
        Instantiate and return the ChatBedrock LLM.

        Returns:
            ChatBedrock: An instance of ChatBedrock configured with the specified model and callback.
        """
        try:
            bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
            llm = ChatBedrock(
                client=bedrock_client,
                model_id=self.model_id,
                streaming=True,
                callbacks=[self.streaming_callback],
                model_kwargs={
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            self.logger.debug(f"ChatBedrock LLM initialized with model_id: {self.model_id}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")
            return llm
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock LLM: {e}")
            raise e