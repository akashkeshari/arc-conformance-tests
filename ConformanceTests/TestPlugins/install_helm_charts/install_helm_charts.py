import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes import config
from arm_rest_utility import fetch_aad_token
from helm_utility import get_helm_registry, pull_helm_chart, export_helm_chart, add_helm_repo, install_helm_chart
from results_utility import save_results, create_results_dir, append_result_output


# This directory contains all result files corresponding to sonobuoy test run
RESULTS_DIR = '/tmp/results'

# Name of the tarfile containing all the result files
RESULTS_TAR_FILENAME = 'results.tar.gz'

# This file needs to be updated with the path to results file so that the sonobuoy worker understands that the test plugin container has completed its work.
DONE_FILE = RESULTS_DIR + '/done'

# This file is used to dump any logs from the test run
OUT_FILE = RESULTS_DIR + '/out'

# This file contains test result in xml formal. It will be used by sonobuoy to determine if the test passed/failed 
RESULT_FILE = RESULTS_DIR + '/result.xml'

# Creating the results directory
create_results_dir(RESULTS_DIR)

# The exit code of the test. Defaults to 1
EXIT_CODE = 1

# Creating a test case for the test run
test_cases = [TestCase('install-helm-charts')]

# Saving results when code exits 
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)

# Check environment variables
tenant_id = os.getenv('TENANT_ID')
if not tenant_id:
    sys.exit('ERROR: variable TENANT_ID is required.')

subscription_id = os.getenv('SUBSCRIPTION_ID')
if not subscription_id:
    sys.exit('ERROR: variable SUBSCRIPTION_ID is required.')

resource_group = os.getenv('RESOURCE_GROUP')
if not resource_group:
    sys.exit('ERROR: variable RESOURCE_GROUP is required.')

cluster_name = os.getenv('CLUSTER_NAME')
if not cluster_name:
    sys.exit('ERROR: variable CLUSTER_NAME is required.')

location = os.getenv('LOCATION')
if not location:
    sys.exit('ERROR: variable LOCATION is required.')

client_id = os.getenv('CLIENT_ID')
if not client_id:
    sys.exit('ERROR: variable CLIENT_ID is required.')

client_secret = os.getenv('CLIENT_SECRET')
if not client_secret:
    sys.exit('ERROR: variable CLIENT_SECRET is required.')

# Get aad token
authority_uri = 'https://login.microsoftonline.com/' + tenant_id
token = fetch_aad_token(client_id, client_secret, authority_uri, 'https://management.core.windows.net/')
access_token = token.get('accessToken')

# Fetch helm chart path
release_train = os.getenv('RELEASE_TRAIN') if os.getenv('RELEASE_TRAIN') else 'stable'
helm_registry_path = os.getenv('HELM_REGISTRY_PATH') if os.getenv('HELM_REGISTRY_PATH') else get_helm_registry(access_token, location, release_train)
print("Successfully fetched helm chart path.")

# Pulling helm charts
result = pull_helm_chart(helm_registry_path)
append_result_output("{}\n".format(result), OUT_FILE)
print("Successfully pulled helm charts.")

# Exporting helm charts
helm_export_destination = os.getenv('HELM_EXPORT_DESTINATION') if os.getenv('HELM_EXPORT_DESTINATION') else "."
result = export_helm_chart(helm_registry_path, helm_export_destination)
append_result_output("{}\n".format(result), OUT_FILE)
print("Successfully exported helm charts.")

# Adding a helm repository
if os.getenv('HELM_REPO_NAME') and os.getenv('HELM_REPO_URL'):
    helm_repo_name = os.getenv('HELM_REPO_NAME')
    helm_repo_url = os.getenv('HELM_REPO_URL')
    result = add_helm_repo(helm_repo_name, helm_repo_url)
    append_result_output("{}\n".format(result), OUT_FILE)

# Loading in-cluster kube-config
try:
    config.load_incluster_config()
except Exception as e:
    sys.exit("Error loading the in-cluster config: " + str(e))

# Installing helm charts
helm_chart_path = os.getenv('HELM_CHART_PATH') if os.getenv('HELM_CHART_PATH') else 'azure-arc-k8sagents'
helm_release_name = os.getenv('HELM_RELEASE_NAME') if os.getenv('HELM_RELEASE_NAME') else 'azure-arc'
kubernetes_distribution = os.getenv('KUBERNETES_DISTRIBUTION') if os.getenv('KUBERNETES_DISTRIBUTION') else 'default'

helm_chart_params_dict = {}  # Dictionary to store the helm chart parameters as key value pairs.
if os.getenv('HELM_CHART_PARAMETERS'):  # This environment variable should be provided as comma separated key value pairs. It will append/overwrite the helm chart parameters while installing helm release.
    helm_chart_params_list = os.getenv('HELM_CHART_PARAMETERS').split(',')
    for params in helm_chart_params_list:
        param = params.split('=')
        param_key = param[0].strip()
        param_value = param[1].strip()
        helm_chart_params_dict[param_key] = param_value

result = install_helm_chart(helm_release_name, helm_chart_path, subscription_id, resource_group, cluster_name, location, tenant_id, client_id, client_secret, kubernetes_distribution, **helm_chart_params_dict)
append_result_output("{}\n".format(result), OUT_FILE)
print("Successfully installed helm charts.")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
