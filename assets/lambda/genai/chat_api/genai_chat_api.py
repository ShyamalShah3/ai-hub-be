import json
import logging
import sys
import os
from typing import Any, Dict
import boto3
import json
from botocore.exceptions import ClientError
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from messaging.publishers.websocket import WebSocketPublisher
from messaging.service import MessageDeliveryService
from model.streaming import StreamingCallback
from utils.enums import (
    FunctionResponseFields as funb,
    WebSocketMessageFields as wssm,
)
from factories.provider_factory import ProviderFactory
from functools import lru_cache

# Set up logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)

@lru_cache(maxsize=128)
def get_model_configs() -> Dict[str, str]:
    """
    Fetch model configurations if needed.
    Currently, models are managed via enums, so this function can be expanded if models are stored externally.
    """
    # Placeholder for future enhancements
    return {}

def extract_event_data(event: Dict[str, Any]) -> tuple:
    """
    Extracts the necessary data from the Lambda event.

    Parameters:
        event (dict): The Lambda event.

    Returns:
        tuple: Contains body, session_id, user_input, model_name, and max_tokens.
    """
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse event body: {e}")
        raise ValueError(f"Invalid JSON in event body: {e}")

    session_id = body.get('session_id', 'test-session')
    user_input = body.get('message', '')
    model_name = body.get('model_name', 'CLAUDE_3_5_SONNET')  # Default model
    max_tokens = int(body.get('max_tokens', os.environ.get('DEFAULT_MAX_TOKENS', 1000)))
    temperature = float(body.get('temperature', os.environ.get('DEFAULT_TEMPERATURE', 0.7)))
    
    LOGGER.debug(f"Extracted event data: session_id={session_id}, user_input={user_input}, model_name={model_name}, max_tokens={max_tokens}, temperature={temperature}")
    return body, session_id, user_input, model_name, max_tokens, temperature


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


def initialize_llm(model_name: str, max_tokens: int, temperature: float, streaming_callback: StreamingCallback = None) -> Any:
    """
    Initializes the appropriate LLM based on the model name using the ProviderFactory.

    Parameters:
        model_name (str): The name of the model to instantiate.
        max_tokens (int): The maximum number of tokens for the model response.
        temperature (float): The temperature to set for the selected model.
        streaming_callback (StreamingCallback, optional): Callback handler for streaming responses (required for Bedrock).

    Returns:
        LLM: An instance of a LangChain LLM.
    """

    # Instantiate the factory with necessary parameters
    factory = ProviderFactory(
        model_name=model_name,
        streaming_callback=streaming_callback,
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Get the provider instance
    provider = factory.get_provider()

    # Get the LLM instance from the provider
    llm = provider.get_llm()
    LOGGER.debug(f"LLM initialized for model: {model_name} with max_tokens: {max_tokens} and temperature: {temperature}")
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
        LOGGER.debug(f"Received event: {event}")
        body, session_id, user_input, model_name, max_tokens, temperature  = extract_event_data(event)

        # Attach WebSocketPublisher if available
        attach_websocket_publisher(event, message_service)

        # Initialize the StreamingCallback with message_service
        streaming_callback = StreamingCallback(message_service=message_service)

        # Initialize LLM
        llm = initialize_llm(model_name, max_tokens, temperature, streaming_callback)

        # Get prompt template
        prompt = get_prompt_template()

        if streaming_callback:
            chain = (prompt | llm).with_config(callbacks=[streaming_callback])
        else:
            # For non-streaming models
            chain = (prompt | llm)

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
        )

        if streaming_callback:
            chain_with_history = chain_with_history.with_config(callbacks=[streaming_callback])

        # Generate response using the 'stream' method (for streaming models)
        if streaming_callback:
            LOGGER.info(f"Starting to process user input for session_id: {session_id} with model: {model_name}")
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
        else:
            # Handle non-streaming models
            LOGGER.info(f"Starting to process user input for session_id: {session_id} with model: {model_name}")
            response = chain_with_history.run({"input": user_input}, config={"configurable": {"session_id": session_id}})
            LOGGER.info("Response processing completed.")
            return {
                funb.STATUS_CODE: 200,
                funb.BODY: json.dumps({wssm.MESSAGE: response})
            }

    except ClientError as e:
        LOGGER.error(f"An AWS ClientError occurred: {e.response['Error']['Message']}")
        return {
            funb.STATUS_CODE: 500,
            funb.BODY: json.dumps({'error': str(e)})
        }
    except json.JSONDecodeError as je:
        LOGGER.error(f"JSON Decode Error: {je}")
        return {
            funb.STATUS_CODE: 400,
            funb.BODY: json.dumps({'error': f"Invalid JSON: {str(je)}"})
        }
    except ValueError as ve:
        LOGGER.error(f"ValueError: {ve}")
        return {
            funb.STATUS_CODE: 400,
            funb.BODY: json.dumps({'error': str(ve)})
        }
    except Exception as e:
        LOGGER.exception("An unexpected error occurred")
        return {
            funb.STATUS_CODE: 500,
            funb.BODY: json.dumps({'error': str(e)})
        }
