#!/usr/bin/env python3.12
import os
import aws_cdk as cdk
from infra.ai_hub_be_stack import AiHubBeStack

app = cdk.App()
AiHubBeStack(app, "AiHubBeStack",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

app.synth()