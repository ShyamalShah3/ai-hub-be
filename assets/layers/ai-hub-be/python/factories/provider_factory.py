from providers.base_provider import BaseProvider
from providers.bedrock_provider import BedrockProvider
from providers.openai_provider import OpenAIProvider
# from providers.google_provider import GoogleProvider
from utils.enums import Provider, BedrockModel, OpenAiModel
from model.streaming import StreamingCallback
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

class ProviderFactory:
    """
    Factory class to instantiate AI model providers based on the provider type.
    """

    def __init__(self, model_name: str, streaming_callback: StreamingCallback = None, max_tokens: int = 1000, temperature: float = 0.7) -> None:
        """
        Initialize the ProviderFactory with necessary parameters.
        
        Parameters:
        model_name (str): The name of the model to instantiate.
        streaming_callback (StreamingCallback, optional): Callback handler for streaming responses.
        api_key (str, optional): API key for OpenAI models.
        max_tokens (int, optional): Maximum number of tokens in the model's response. Defaults to 1000.
        temperature (float, optional): Temperature to set for the model. Defaults to 0.7.
        """
        self.model_name = model_name
        self.provider = self._get_provider_type()
        self.streaming_callback = streaming_callback
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"ProviderFactory initialized with model_name: {self.model_name}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")
    
    def _get_provider_type(self):
        if self.model_name in BedrockModel.__members__:
            return Provider.BEDROCK
        elif self.model_name in OpenAiModel.__members__:
            return Provider.OPENAI
        # elif self.model_name in GoogleModel.__members__:
        #     return Provider.GOOGLE
        else:
            raise ValueError(f"{self.model_name} is not a currently supported model")
        
    def _get_api_key(self, provider: Provider) -> str:
        """
        Retrieves the API key for the specified provider from AWS Secrets Manager.
        
        Parameters:
            provider (Provider): The provider for which to retrieve the API key.
        
        Returns:
            str: The API key for the provider.
        
        Raises:
            ClientError: If there is an error retrieving the secret.
            KeyError: If the secret or key is not found.
        """
        secret_name_mapping = {
            Provider.OPENAI: os.environ.get("OPENAI_SECRET_NAME"),
            Provider.GOOGLE: os.environ.get("GOOGLE_SECRET_NAME"),
            # Add other providers here
        }

        secret_name = secret_name_mapping.get(provider)
        if not secret_name:
            raise ValueError(f"No secret name configured for provider: {provider}")

        client = boto3.client('secretsmanager')
        try:
            self.logger.info(f"Attempting to retrieve secret: {secret_name}")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)

            # Extract and parse the secret string
            secret_string = get_secret_value_response['SecretString']
            self.logger.debug(f"Secret string retrieved: {secret_string}")

            # Parse the JSON string to get the actual value
            secret_dict = json.loads(secret_string)
            api_key = secret_dict.get("api_key")

            if not api_key:
                raise KeyError(f"'api_key' not found in secret '{secret_name}'")
            
            self.logger.info(f"Successfully retrieved API key for provider: {provider}")
            return api_key
        except ClientError as e:
            self.logger.error(f"Error retrieving secret named {secret_name}: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from secret '{secret_name}': {e}")
            raise e
        except KeyError as e:
            self.logger.error(str(e))
            raise e
    
    def get_provider(self) -> BaseProvider:
        """
        Determine the provider based on the model name and instantiate the corresponding provider.
        
        Returns:
            BaseProvider: An instance of a provider implementing BaseProvider.
        
        Raises:
            ValueError: If the provider for the given model is unsupported or not found.
        """
        if self.provider == Provider.BEDROCK:
            model_id = BedrockModel[self.model_name].value
            self.logger.debug(f"Model '{self.model_name}' identified as Bedrock model with ID '{model_id}'")
            if not self.streaming_callback:
                raise ValueError("Streaming callback is required for Bedrock Models")
            return BedrockProvider(model_id=model_id, streaming_callback=self.streaming_callback, max_tokens=self.max_tokens, temperature=self.temperature)
        
        elif self.provider == Provider.OPENAI:
            model_id = OpenAiModel[self.model_name].value
            self.logger.debug(f"Model '{self.model_name}' identified as OpenAi model with ID '{model_id}'")
            api_key = self._get_api_key(self.provider)
            if not self.streaming_callback:
                raise ValueError("Streaming callback is required for OpenAi Models")
            return OpenAIProvider(model_id=model_id, api_key=api_key, streaming_callback=self.streaming_callback, max_tokens=self.max_tokens, temperature=self.temperature)
        
        # elif self.provider == Provider.GOOGLE:
        #     model_id = GoogleModel[self.model_name].value
        #     self.logger.debug(f"Model '{self.model_name}' identified as Google AI model with ID '{model_id}'")
        #     api_key = self._get_api_key(self.provider)
        #     if not self.streaming_callback:
        #         raise ValueError("Streaming callback is required for Google AI Models")
        #     return GoogleProvider(model_id=model_id, api_key=api_key, streaming_callback=self.streaming_callback, max_output_tokens=self.max_tokens, temperature=self.temperature)
        
        else:
            self.logger.error(f"Unsupported or unknown model name: {self.model_name}")
            raise ValueError(f"Unsupported or unknown model name: {self.model_name}")
