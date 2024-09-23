from enum import Enum

class InstructionTypes(str, Enum):
    INGEST = "INGEST"
    RETRIEVE = "RETRIEVE"

class FunctionResponseFields(str, Enum):
    STATUS_CODE = "statusCode"
    HEADERS = "headers"
    BODY = "body"

class ErrorResponseBodyFields(str, Enum):
    ERROR_MESSAGE = "errorMessage"

class WebSocketMessageFields(str, Enum):
    MESSAGE = "message"
    TYPE = "type"
    ACTION = "action"
    FEEDBACK = "feedback"
    DATA = "data"

class WebSocketMessageTypes(str, Enum):
    ERROR = "error"
    MESSAGE = "message"
    STREAM = "stream"
    END = "end"

class WebSocketMessageActions(str, Enum):
    CLOSE = "close"

class Provider(Enum):
    BEDROCK = "bedrock"
    OPENAI = "openai"

class BedrockModel(str,Enum):
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    # CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0" # Issues with OPUS
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    LLAMA_3_1_8B_INSTRUCT = "meta.llama3-1-8b-instruct-v1:0"
    LLAMA_3_1_70B_INSTRUCT = "meta.llama3-1-70b-instruct-v1:0"
    # LLAMA_3_1_405B_INSTRUCT = "meta.llama3-1-405b-instruct-v1:0" # Unauthorized
    MISTRAL_7B_INSTRUCT = "mistral.mistral-7b-instruct-v0:2"
    MISTRAL_8_7B_INSTRUCT = "mistral.mixtral-8x7b-instruct-v0:1"
    MISTRAL_LARGE = "mistral.mistral-large-2402-v1:0"
    MISTRAL_LARGE_2 = "mistral.mistral-large-2407-v1:0"

class OpenAiModel(str,Enum):
    GPT_4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT_4O = "gpt-4o-2024-08-06"
    GPT_4O_MINI = "gpt-4o-mini-2024-07-18"
    # O1_PREVIEW = "o1-preview"
    # O1_MINI_PREVIEW = "o1-mini-preview"
