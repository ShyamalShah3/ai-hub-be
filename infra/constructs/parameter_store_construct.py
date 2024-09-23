from aws_cdk import (
    aws_ssm as ssm,
)
from aws_cdk.aws_ssm import (
    ParameterType,
    IStringParameter
)
from constructs import Construct

class ParameterStoreConstruct(Construct):

    @staticmethod
    def get_string_ssm_parameter(scope: Construct, id: str, parameter_name: str) -> IStringParameter:
        return ssm.StringParameter.from_string_parameter_name(
            scope,
            id,
            parameter_name
        )

    def __init__(self, scope: Construct, id: str, parameter_name: str, parameter_value: str=None, parameter_description: str=None, parameter_type: ParameterType=None, **kwargs) -> None:
        super().__init__(scope, id)

        if parameter_value:
            self.parameter = ssm.StringParameter(
                self,
                id,
                parameter_name=parameter_name,
                string_value=parameter_value,
                description=parameter_description,
                type=parameter_type
            )
        else:
            self.parameter = ParameterStoreConstruct.get_string_ssm_parameter(
                scope,
                id,
                parameter_name
            )
