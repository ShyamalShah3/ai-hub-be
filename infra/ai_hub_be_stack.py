import yaml
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct
from infra.constructs.lambda_layers import LambdaLayers
from infra.constructs.api_construct import ApiConstruct

class AiHubBeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Load configuration files
        with open("config.yml", "r") as config_file:
            config = yaml.safe_load(config_file)

        with open("api_keys.yml", "r") as api_key_file:
            api_key_config = yaml.safe_load(api_key_file)

        # Set architecture
        architecture = _lambda.Architecture.X86_64
        if config["lambda"]["architecture"].upper() == "ARM_64":
            architecture = _lambda.Architecture.ARM_64

        # Set Python runtime
        python_runtime_str = config["lambda"]["python_runtime"]
        if python_runtime_str == "PYTHON_3_9":
            python_runtime = _lambda.Runtime.PYTHON_3_9
        elif python_runtime_str == "PYTHON_3_10":
            python_runtime = _lambda.Runtime.PYTHON_3_10
        elif python_runtime_str == "PYTHON_3_11":
            python_runtime = _lambda.Runtime.PYTHON_3_11
        elif python_runtime_str == "PYTHON_3_12":
            python_runtime = _lambda.Runtime.PYTHON_3_12
        else:
            raise ValueError(f"Unsupported Python runtime: {python_runtime_str}")

        # Get values from config
        openai_secret_name = api_key_config["openai"]["secret_name"]
        openai_secret_arn = api_key_config["openai"]["secret_arn"]
        max_tokens = str(config["model"]["max_tokens"])
        temperature = str(config["model"]["temperature"])

        ## **************** Lambda Layers ****************
        self.layers = LambdaLayers(
            self,
            f"{construct_id}-layers",
            stack_name=construct_id,
            architecture=architecture,
            python_runtime=python_runtime,
        )

        ## **************** API Construct ****************
        self.api_construct = ApiConstruct(
            self,
            "ApiConstruct",
            stack_name=construct_id,
            layers=self.layers.get_all_layers(),
            architecture=architecture,
            runtime=python_runtime,
            openai_secret_name=openai_secret_name,
            openai_secret_arn=openai_secret_arn,
            max_tokens=max_tokens,
            temperature=temperature
        )