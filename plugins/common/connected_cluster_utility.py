import sys

from azure.mgmt.hybridkubernetes import ConnectedKubernetesClient


def get_connected_kubernetes_client(credential, subscription_id):
    return ConnectedKubernetesClient(credential, subscription_id)


def get_connected_cluster_client(credential, subscription_id):
    try:
        return get_connected_kubernetes_client(credential, subscription_id).connected_cluster
    except Exception as e:
        sys.exit("Error occured while creating connected cluster client: " + str(e))


def get_connected_cluster(cc_client, resource_group_name, cluster_name):
    try:
        return cc_client.get(resource_group_name, cluster_name)
    except Exception as e:
        sys.exit("Error occured while fetching the connected cluster resource: " + str(e))