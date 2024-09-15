import json
import logging
import sys
import os
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_aws import ChatBedrock
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from messaging.publishers.websocket import WebSocketPublisher
from messaging.service import MessageDeliveryService
from model.streaming import BedrockStreamingCallback
from utils.enums import (
    FunctionResponseFields as funb,
    WebSocketMessageFields as wssm,
    WebSocketMessageTypes as wsst,
)

# Set up logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


def extract_event_data(event: Dict[str, Any]) -> tuple:
    """
    Extracts the necessary data from the Lambda event.

    Parameters:
        event (dict): The Lambda event.

    Returns:
        tuple: Contains body, session_id, and user_input.
    """
    body = json.loads(event.get('body', '{}'))
    session_id = body.get('session_id', 'test-session')
    user_input = body.get('message', '')
    LOGGER.debug(f"Extracted event data: session_id={session_id}, user_input={user_input}")
    return body, session_id, user_input


def attach_websocket_publisher(event: Dict[str, Any], message_service: MessageDeliveryService) -> None:
    """
    Attaches a WebSocketPublisher to the message service if possible.

    Parameters:
        event (dict): The Lambda event.
        message_service (MessageDeliveryService): The message delivery service.
    """
    try:
        connection_id = event['requestContext']['connectionId']
        endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
        message_service.attach(WebSocketPublisher(endpoint_url=endpoint_url, connection_id=connection_id))
        LOGGER.info(f"WebSocketPublisher attached with connection_id: {connection_id}")
    except KeyError:
        LOGGER.warning("RequestContext not present in event. WebSocketPublisher not attached.")


def initialize_llm(streaming_callback: BedrockStreamingCallback) -> ChatBedrock:
    """
    Initializes the Bedrock LLM.

    Parameters:
        streaming_callback (BedrockStreamingCallback): The streaming callback.

    Returns:
        ChatBedrock: The initialized LLM.
    """
    bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ['REGION'])
    llm = ChatBedrock(
        client=bedrock_client,
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        streaming=True,
        callbacks=[streaming_callback]
    )
    LOGGER.debug("Initialized Bedrock LLM with model_id 'anthropic.claude-3-5-sonnet-20240620-v1:0'")
    return llm


def get_prompt_template() -> ChatPromptTemplate:
    """
    Creates the chat prompt template with a messages placeholder for history.

    Returns:
        ChatPromptTemplate: The chat prompt template.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    LOGGER.debug("Created chat prompt template with message placeholders for history.")
    return prompt


def get_session_history(session_id: str) -> DynamoDBChatMessageHistory:
    """
    Retrieves the chat message history for a given session.

    Parameters:
        session_id (str): The session ID.

    Returns:
        DynamoDBChatMessageHistory: The chat message history.
    """
    history = DynamoDBChatMessageHistory(
        table_name=os.environ['CHAT_HISTORY_TABLE_NAME'],
        session_id=session_id,
        primary_key_name="session_id"
    )
    LOGGER.debug(f"Retrieved session history for session_id: {session_id}")
    return history


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda function handler for processing chat messages.

    Parameters:
        event (dict): The Lambda event payload.
        context: The Lambda runtime information.

    Returns:
        dict: The response object containing status code and body.
    """
    # Initialize message delivery service
    message_service = MessageDeliveryService()

    try:
        # Extract data from the event
        body, session_id, user_input = extract_event_data(event)

        # Attach WebSocketPublisher if available
        attach_websocket_publisher(event, message_service)

        # Initialize the BedrockStreamingCallback with message_service
        streaming_callback = BedrockStreamingCallback(message_service=message_service)

        # Initialize LLM
        llm = initialize_llm(streaming_callback)

        # Get prompt template
        prompt = get_prompt_template()

        # Create the runnable chain and include callbacks
        chain = (prompt | llm).with_config(callbacks=[streaming_callback])

        # Wrap the chain with message history and include callbacks
        chain_with_history = RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=get_session_history,
            input_messages_key="input",
            history_messages_key="history",
            history_factory_config=[
                {
                    "id": "session_id",
                    "annotation": str,
                    "name": "Session ID",
                    "description": "Unique identifier for the session.",
                    "default": "",
                    "is_shared": True,
                }
            ]
        ).with_config(callbacks=[streaming_callback])

        # Generate response using the 'stream' method
        LOGGER.info(f"Starting to process user input for session_id: {session_id}")
        for _ in chain_with_history.stream(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        ):
            pass  # The streaming_callback handles the message delivery

        LOGGER.info("Response streaming completed.")
        return {
            funb.STATUS_CODE: 200,
            funb.BODY: json.dumps({wssm.MESSAGE: 'Response streaming started'})
        }

    except ClientError as e:
        LOGGER.error(f"An AWS ClientError occurred: {e.response['Error']['Message']}")
        return {
            funb.STATUS_CODE: 500,
            funb.BODY: json.dumps({'error': str(e)})
        }
    except Exception as e:
        LOGGER.exception("An unexpected error occurred")
        return {
            funb.STATUS_CODE: 500,
            funb.BODY: json.dumps({'error': str(e)})
        }