import sys

from azure.mgmt.hybridkubernetes import ConnectedKubernetesClient


# This function returns the python client to interact with resources under the namespace 'Microsoft.Kubernetes'
def get_connected_kubernetes_client(credential, subscription_id):
    return ConnectedKubernetesClient(credential, subscription_id)


# This function returns the python client to interact with the connected cluster resource
def get_connected_cluster_client(credential, subscription_id):
    try:
        return get_connected_kubernetes_client(credential, subscription_id).connected_cluster
    except Exception as e:
        sys.exit("Error occured while creating connected cluster client: " + str(e))


# This function returns a connected cluster object present in a given resource group
def get_connected_cluster(cc_client, resource_group_name, cluster_name):
    try:
        return cc_client.get(resource_group_name, cluster_name)
    except Exception as e:
        sys.exit("Error occured while fetching the connected cluster resource: " + str(e))