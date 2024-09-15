import json
from langchain_core.callbacks import BaseCallbackHandler
from messaging.service import MessageDeliveryService
from model.postprocess import clean_answer
from utils.enums import WebSocketMessageFields as wssm
from utils.enums import WebSocketMessageTypes as wsst

class BedrockStreamingCallback(BaseCallbackHandler):
    """
    Custom Bedrock streaming callback to be used with RunnableWithMessageHistory and BedrockChat
    """

    def __init__(self, message_service: MessageDeliveryService):
        self.current_response = ""
        self.message_service = message_service

    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        """Called when LLM starts running."""
        self.current_response = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """
        Runs on each new token produced by LLM. Concatenates tokens and posts to message_service
        """
        self.current_response += token
        serialized_response_body = json.dumps({
            wssm.MESSAGE: clean_answer(self.current_response) + "...",
            wssm.TYPE: wsst.STREAM,
        })
        self.message_service.post(payload=serialized_response_body)

    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM generation ends."""
        serialized_response_body = json.dumps({
            wssm.MESSAGE: clean_answer(self.current_response),
            wssm.TYPE: wsst.END,
        })
        self.message_service.post(payload=serialized_response_body)

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM encounters an error."""
        serialized_response_body = json.dumps({
            wssm.MESSAGE: f"Error occurred: {str(error)}",
            wssm.TYPE: wsst.ERROR,
        })
        self.message_service.post(payload=serialized_response_body)
