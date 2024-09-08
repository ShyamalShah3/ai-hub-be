import json

from langchain.callbacks.base import BaseCallbackHandler
from messaging.service import MessageDeliveryService
from model.postprocess import clean_answer
from utils.enums import WebSocketMessageFields as wssm
from utils.enums import WebSocketMessageTypes as wsst

class BedrockStreamingCallback(BaseCallbackHandler):
    """
    Custom Bedrock streaming callback to be specified in `callbacks` for langchain.llms.bedrock.Bedrock
    """

    def __init__(self, message_service: MessageDeliveryService):
        self.concatenated_answer = ""
        self.message_service = message_service

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """
        Runs on each new token produced by LLM. Concatenates tokens produced by LLM so far and posts to message_service
        Requires setting streaming==True in the langchain.llms.bedrock.Bedrock class to be executed
        """
        self.concatenated_answer += token
        serialized_response_body = json.dumps(
            {
                wssm.MESSAGE: clean_answer(self.concatenated_answer) + "...",
                wssm.TYPE: wsst.STREAM,
            }
        )
        self.message_service.post(payload=serialized_response_body)
