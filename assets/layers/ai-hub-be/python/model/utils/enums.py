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

class WebSocketMessageActions(str, Enum):
    CLOSE = "close"