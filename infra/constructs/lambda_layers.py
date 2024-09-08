from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3_assets as s3_assets,
    BundlingOptions,
    DockerImage,
    RemovalPolicy,
)
from constructs import Construct

class LambdaLayers(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name: str,
        architecture: _lambda.Architecture,
        python_runtime: _lambda.Runtime,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.runtime = python_runtime
        self.architecture = architecture

        # Define layers
        self.ai_hub_be = self._create_layer(
            f"{stack_name}-ai-hub-be-layer",
            "./assets/layers/ai-hub-be",
            "AI Hub backend layer with messaging and model utilities"
        )

        self.dependencies = self._create_layer_from_requirements(
            f"{stack_name}-dependencies-layer",
            "./assets/layers/ai-hub-be/python",
            "Lambda layer including Langchain, boto3, and other dependencies"
        )

    def _create_layer(
        self,
        layer_name: str,
        asset_path: str,
        description: str
    ) -> _lambda.LayerVersion:
        return _lambda.LayerVersion(
            self,
            layer_name,
            compatible_runtimes=[self.runtime],
            compatible_architectures=[self.architecture],
            code=_lambda.Code.from_asset(asset_path),
            description=description,
            layer_version_name=layer_name,
        )

    def _create_layer_from_requirements(
        self,
        layer_name: str,
        asset_path: str,
        description: str
    ) -> _lambda.LayerVersion:
        bundling_options = BundlingOptions(
            image=self.runtime.bundling_image,  # Use the bundling_image directly
            command=[
                "bash", "-c",
                "pip install -r requirements.txt -t /asset-output/python && cp -au . /asset-output/python/"
            ],
        )

        layer_asset = s3_assets.Asset(
            self,
            f"{layer_name}-asset",
            path=asset_path,
            bundling=bundling_options
        )

        return _lambda.LayerVersion(
            self,
            layer_name,
            compatible_runtimes=[self.runtime],
            compatible_architectures=[self.architecture],
            code=_lambda.Code.from_bucket(layer_asset.bucket, layer_asset.s3_object_key),
            description=description,
            layer_version_name=layer_name,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def get_all_layers(self) -> list[_lambda.ILayerVersion]:
        return [self.ai_hub_be, self.dependencies]