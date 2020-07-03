import os
import requests
import subprocess
import sys


# Function to fetch the helm chart path.
def get_helm_registry(token, location, release_train):
    get_chart_location_url = "https://{}.dp.kubernetesconfiguration.azure.com/azure-arc-k8sagents/GetLatestHelmPackagePath?api-version=2019-11-01-preview".format(location)
    query_parameters = {}
    query_parameters['releaseTrain'] = release_train
    header_parameters = {}
    header_parameters['Authorization'] = "Bearer {}".format(str(token))
    try:
        response = requests.post(get_chart_location_url, params=query_parameters, headers=header_parameters)
    except Exception as e:
        sys.exit("Error while fetching helm chart registry path: " + str(e))
    if response.status_code == 200:
        return response.json().get('repositoryPath')
    sys.exit("Error while fetching helm chart registry path: {}".format(str(response.json())))


# Function to pull helm charts
def pull_helm_chart(registry_path):
    os.environ['HELM_EXPERIMENTAL_OCI'] = '1'
    cmd_helm_chart_pull = ["helm", "chart", "pull", registry_path]
    response_helm_chart_pull = subprocess.Popen(cmd_helm_chart_pull, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_chart_pull, error_helm_chart_pull = response_helm_chart_pull.communicate()
    if response_helm_chart_pull.returncode != 0:
        sys.exit("Unable to pull helm chart from the registry '{}': ".format(registry_path) + error_helm_chart_pull.decode("ascii"))
    return output_helm_chart_pull.decode("ascii")


# Function to export helm charts
def export_helm_chart(registry_path, destination):
    cmd_helm_chart_export = ["helm", "chart", "export", registry_path, "--destination", destination]
    response_helm_chart_export = subprocess.Popen(cmd_helm_chart_export, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_chart_export, error_helm_chart_export = response_helm_chart_export.communicate()
    if response_helm_chart_export.returncode != 0:
        sys.exit("Unable to export helm chart from the registry '{}': ".format(registry_path) + error_helm_chart_export.decode("ascii"))
    return output_helm_chart_export.decode("ascii")


# Function to add a helm repository
def add_helm_repo(repo_name, repo_url):
    cmd_helm_repo = ["helm", "repo", "add", repo_name, repo_url]
    response_helm_repo = subprocess.Popen(cmd_helm_repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_repo, error_helm_repo = response_helm_repo.communicate()
    if response_helm_repo.returncode != 0:
        sys.exit("Unable to add repository {} to helm: ".format(repo_url) + error_helm_repo.decode("ascii"))
    return output_helm_repo.decode("ascii")


# Function to install helm charts
def install_helm_chart(helm_release_name, helm_chart_path, subscription_id, resource_group_name, cluster_name, location, tenant_id, client_id, client_secret, kubernetes_distro, **kwargs):
    cmd_helm_install = ["helm", "install", helm_release_name, helm_chart_path,
                        "--set", "global.subscriptionId={}".format(subscription_id),
                        "--set", "global.resourceGroupName={}".format(resource_group_name),
                        "--set", "global.resourceName={}".format(cluster_name),
                        "--set", "global.location={}".format(location),
                        "--set", "global.tenantId={}".format(tenant_id),
                        "--set", "global.clientId={}".format(client_id),
                        "--set", "global.clientSecret={}".format(client_secret),
                        "--set", "global.kubernetesDistro={}".format(kubernetes_distro)]
    for key, value in kwargs.items():
        cmd_helm_install.extend(["--set", "{}={}".format(key, value)])
    response_helm_install = subprocess.Popen(cmd_helm_install, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_install, error_helm_install = response_helm_install.communicate()
    if response_helm_install.returncode != 0:
        sys.exit("Unable to install helm release: " + error_helm_install.decode("ascii"))
    return output_helm_install.decode("ascii")
