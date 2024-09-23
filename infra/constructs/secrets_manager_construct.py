from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class SecretsManagerConstruct(Construct):
    @staticmethod
    def get_secret(scope: Construct, id: str, secret_name: str) -> secretsmanager.ISecret:
        return secretsmanager.Secret.from_secret_name_v2(
            scope,
            id,
            secret_name
        )
    
    def __init__(self, scope: Construct, id: str, secret_name: str, **kwargs) -> None:
        super().__init__(scope, id)

        self.secret = SecretsManagerConstruct.get_secret(
            scope,
            id,
            secret_name
        )
