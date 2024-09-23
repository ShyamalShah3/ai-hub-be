from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
)
from constructs import Construct

class LambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        function_name: str,
        code_path: str,
        handler: str,
        runtime: _lambda.Runtime,
        architecture: _lambda.Architecture,
        layers=None,
        environment=None,
        timeout=Duration.minutes(15),
        memory_size=256,
    ):
        super().__init__(scope, id)

        self.function = _lambda.Function(
            self,
            id,
            function_name=function_name,
            code=_lambda.Code.from_asset(code_path),
            handler=handler,
            runtime=runtime,
            architecture=architecture,
            layers=layers,
            environment=environment,
            timeout=timeout,
            memory_size=memory_size,
        )

    def grant_dynamodb_access(self, table):
        table.grant_read_write_data(self.function)

    def add_environment_variables(self, variables):
        for key, value in variables.items():
            self.function.add_environment(key, value)

    def grant_execute_api_access(self, api_arn):
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[api_arn],
            )
        )

    def grant_bedrock_access(self):
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:*"],
                resources=["*"],
            )
        )
    
    def grant_ssm_parameter_access(self, parameter_arn: str):
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[parameter_arn],
            )
        )
    
    def grant_secrets_manager_access(self, secret_arn: str):
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[secret_arn]
            )
        )