import aws_cdk as core
import aws_cdk.assertions as assertions

from infra.ai_hub_be_stack import AiHubBeStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ai_hub_be/ai_hub_be_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AiHubBeStack(app, "ai-hub-be")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
