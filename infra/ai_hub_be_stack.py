import yaml
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    RemovalPolicy,
)
from constructs import Construct
from infra.constructs.lambda_layers import LambdaLayers

class AiHubBeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load configuration
        with open("config.yml", "r") as config_file:
            config = yaml.safe_load(config_file)

        # Set architecture
        architecture = _lambda.Architecture.X86_64
        if config["lambda"]["architecture"].upper() == "ARM_64":
            architecture = _lambda.Architecture.ARM_64

        # Set Python runtime
        python_runtime = _lambda.Runtime.PYTHON_3_9
        if config["lambda"]["python_runtime"] == "PYTHON_3_10":
            python_runtime = _lambda.Runtime.PYTHON_3_10
        elif config["lambda"]["python_runtime"] == "PYTHON_3_11":
            python_runtime = _lambda.Runtime.PYTHON_3_11
        elif config["lambda"]["python_runtime"] == "PYTHON_3_12":
            python_runtime = _lambda.Runtime.PYTHON_3_12
        else:
            raise ValueError(f"Unsupported Python runtime: {config['lambda']['python_runtime']}")

        ## **************** Lambda Layers ****************
        self.layers = LambdaLayers(
            self,
            f"{construct_id}-layers",
            stack_name=construct_id,
            architecture=architecture,
            python_runtime=python_runtime,
        )
