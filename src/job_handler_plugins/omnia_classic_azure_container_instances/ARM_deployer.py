from azure.mgmt.resource import ResourceManagementClient


class Deployer:
    def __init__(self, subscription_id, resource_group, credentials):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.credentials = credentials

        self.client = ResourceManagementClient(self.credentials, self.subscription_id)

    def deploy(self, template: dict, deployment_name: str, parameters: dict):
        deployment_properties = {
            "mode": "Incremental",
            "template": template,
            "parameters": {k: {"value": v} for k, v in parameters.items()} if parameters else {},
        }

        deployment_async_operation = self.client.deployments.begin_create_or_update(
            self.resource_group, deployment_name, {"properties": deployment_properties}
        )
        return deployment_async_operation.wait()
