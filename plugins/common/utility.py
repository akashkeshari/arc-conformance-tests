import adal
import os
import requests
import shutil, subprocess, sys
import tarfile

from msrestazure.azure_active_directory import AADTokenCredentials
from pathlib import Path


# Function to create the test result directory 
def create_results_dir(results_dir):
    Path(results_dir).mkdir(parents=True, exist_ok=True)

# Function to save all the results after test plugin exits 
def save_results(tar_filename, results_dir, done_file):
    print('Saving Results ...')
    make_tarfile(tar_filename, results_dir)
    with open(done_file, "w+") as f:
        f.write(results_dir + '/' + tar_filename)

# Function to create a tarball of all the results. This is a required standard for sonobuoy 
def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname="")
    shutil.move(output_filename, source_dir)

# Function to append logs from the test run into results file
def append_result_output(message, result_file_path):
    with open(result_file_path, "a") as result_file:
        result_file.write(message)

# Function to fetch aad token from spn id and password
def fetch_aad_token(client_id, client_secret, authority_uri, resource_uri):
    """
    Authenticate using service principal w/ key.
    """
    context = adal.AuthenticationContext(authority_uri, api_version=None)
    return context.acquire_token_with_client_credentials(resource_uri, client_id, client_secret)

# Function to fetch the helm chart path.
def get_helm_registry(token, location, release_train):
    get_chart_location_url = "https://{}.dp.kubernetesconfiguration.azure.com/{}/GetLatestHelmPackagePath?api-version=2019-11-01-preview".format(location, 'azure-arc-k8sagents')
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
def export_helm_chart(registry_path):
    cmd_helm_chart_export = ["helm", "chart", "export", registry_path, "--destination", "."]
    response_helm_chart_export = subprocess.Popen(cmd_helm_chart_export, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_chart_export, error_helm_chart_export = response_helm_chart_export.communicate()
    if response_helm_chart_export.returncode != 0:
        sys.exit("Unable to export helm chart from the registry '{}': ".format(registry_path) + error_helm_chart_export.decode("ascii"))
    return output_helm_chart_export.decode("ascii")

# Function to install helm charts
def install_helm_chart(subscription_id, resource_group_name, cluster_name, location, tenant_id, client_id, client_secret):
    cmd_helm_install = ["helm", "install", "azure-arc", "azure-arc-k8sagents",
                        "--set", "global.subscriptionId={}".format(subscription_id),
                        "--set", "global.resourceGroupName={}".format(resource_group_name),
                        "--set", "global.resourceName={}".format(cluster_name),
                        "--set", "global.location={}".format(location),
                        "--set", "global.tenantId={}".format(tenant_id),
                        "--set", "global.clientId={}".format(client_id),
                        "--set", "global.clientSecret={}".format(client_secret)]
    response_helm_install = subprocess.Popen(cmd_helm_install, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_helm_install, error_helm_install = response_helm_install.communicate()
    if response_helm_install.returncode != 0:
        sys.exit("Unable to install helm release: " + error_helm_install.decode("ascii"))
    return output_helm_install.decode("ascii")
