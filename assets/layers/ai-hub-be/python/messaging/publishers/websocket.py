from typing import Any
import boto3
from messaging.publishers.base import BasePublisher

class WebSocketPublisher(BasePublisher):
    def __init__(self, endpoint_url: str, connection_id: str) -> None:
        self._client = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)
        self._connection_id = connection_id
        super().__init__()

    def publish(self, payload: Any) -> None:
        self._client.post_to_connection(
            Data=payload.encode('utf-8'),
            ConnectionId=self._connection_id,
        )
