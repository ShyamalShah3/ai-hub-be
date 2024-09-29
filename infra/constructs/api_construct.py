import yaml
from aws_cdk import (
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_dynamodb as ddb,
    aws_lambda as _lambda,
    aws_iam as iam,
    Aws,
    RemovalPolicy
)
from constructs import Construct
from .lambda_construct import LambdaConstruct

class ApiConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_name: str,
        layers,
        architecture: _lambda.Architecture,
        runtime: _lambda.Runtime,
        openai_secret_name: str,
        openai_secret_arn: str,
        max_tokens: str,
        temperature: str
    ):
        super().__init__(scope, id)

        # Create DynamoDB Tables
        connections_dynamodb_table = ddb.Table(
            self,
            f"{stack_name}-ConnectionsTable",
            table_name=f"{stack_name}-ConnectionsTable",
            partition_key=ddb.Attribute(name="connectionId", type=ddb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        )

        chat_history_dynamodb_table = ddb.Table(
            self,
            f"{stack_name}-ChatHistoryTable",
            table_name=f"{stack_name}-ChatHistoryTable",
            partition_key=ddb.Attribute(name="session_id", type=ddb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        )

        # Create the WebSocket API
        self.web_socket_api = apigw.WebSocketApi(
            self,
            f"{stack_name}-WebSocketAPI",
            api_name=f"{stack_name}-WebSocketAPI",
            route_selection_expression="$request.body.action",
        )

        # Create a stage for the WebSocket API
        self.web_socket_stage = apigw.WebSocketStage(
            self,
            f"{stack_name}-WebSocketStage",
            web_socket_api=self.web_socket_api,
            stage_name="production",
            auto_deploy=True,
        )

        # API ARN for permissions
        api_arn = f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{self.web_socket_api.api_id}/{self.web_socket_stage.stage_name}/POST/@connections/*"

        # Create Lambda functions
        connect_handler = self.create_lambda_function(
            id=f"{stack_name}-websocket-connect",
            function_name=f"{stack_name}-websocket-connect",
            code_path="./assets/lambda/websocket/connect",
            handler="app.handler",
            runtime=_lambda.Runtime.NODEJS_20_X,
            architecture=architecture,
            environment={
                "TABLE_NAME": connections_dynamodb_table.table_name,
                "REGION": Aws.REGION
            }
        )

        disconnect_handler = self.create_lambda_function(
            id=f"{stack_name}-websocket-disconnect",
            function_name=f"{stack_name}-websocket-disconnect",
            code_path="./assets/lambda/websocket/disconnect",
            handler="app.handler",
            runtime=_lambda.Runtime.NODEJS_20_X,
            architecture=architecture,
            environment={
                "TABLE_NAME": connections_dynamodb_table.table_name,
                "REGION": Aws.REGION
            }
        )

        default_handler = self.create_lambda_function(
            id=f"{stack_name}-websocket-default",
            function_name=f"{stack_name}-websocket-default",
            code_path="./assets/lambda/websocket/default",
            handler="default.lambda_handler",
            runtime=runtime,
            architecture=architecture,
        )

        chat_handler = self.create_lambda_function(
            id=f"{stack_name}-chat",
            function_name=f"{stack_name}-chat",
            code_path="./assets/lambda/genai/chat_api",
            handler="genai_chat_api.lambda_handler",
            runtime=runtime,
            architecture=architecture,
            layers=layers,
            environment={
                "CHAT_HISTORY_TABLE_NAME": chat_history_dynamodb_table.table_name,
                "REGION": Aws.REGION,
                "OPENAI_SECRET_NAME": openai_secret_name,
                "DEFAULT_MAX_TOKENS": max_tokens,
                "DEFAULT_TEMPERATURE": temperature
            },
        )

        # Grant necessary permissions
        connect_handler.grant_dynamodb_access(connections_dynamodb_table)
        connect_handler.grant_execute_api_access(api_arn)

        disconnect_handler.grant_dynamodb_access(connections_dynamodb_table)
        disconnect_handler.grant_execute_api_access(api_arn)

        default_handler.grant_execute_api_access(api_arn)

        chat_handler.grant_dynamodb_access(chat_history_dynamodb_table)
        chat_handler.grant_execute_api_access(api_arn)
        chat_handler.grant_bedrock_access()
        chat_handler.grant_secrets_manager_access(openai_secret_arn)

        # Add routes to the WebSocket API
        self.web_socket_api.add_route(
            route_key="$connect",
            integration=integrations.WebSocketLambdaIntegration(
                f"{stack_name}-ConnectIntegration",
                connect_handler.function,
            ),
        )
        self.web_socket_api.add_route(
            route_key="$disconnect",
            integration=integrations.WebSocketLambdaIntegration(
                f"{stack_name}-DisconnectIntegration",
                disconnect_handler.function,
            ),
        )
        self.web_socket_api.add_route(
            route_key="$default",
            integration=integrations.WebSocketLambdaIntegration(
                f"{stack_name}-DefaultIntegration",
                default_handler.function,
            ),
        )
        self.web_socket_api.add_route(
            route_key="chat",
            integration=integrations.WebSocketLambdaIntegration(
                f"{stack_name}-ChatIntegration",
                chat_handler.function,
            ),
        )

        # Output the WebSocket API endpoint
        self.ws_api_endpoint = self.web_socket_stage.url

    def create_lambda_function(
        self,
        id: str,
        function_name: str,
        code_path: str,
        handler: str,
        runtime: _lambda.Runtime,
        architecture: _lambda.Architecture,
        layers=None,
        environment=None,
    ) -> LambdaConstruct:
        lambda_construct = LambdaConstruct(
            self,
            id,
            function_name=function_name,
            code_path=code_path,
            handler=handler,
            runtime=runtime,
            architecture=architecture,
            layers=layers,
            environment=environment,
        )
        return lambda_construct