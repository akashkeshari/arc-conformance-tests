import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes_configuration_utility import get_source_control_configuration_client, create_kubernetes_configuration
from results_utility import save_results, create_results_dir, append_result_output
from arm_rest_utility import fetch_aad_token_credentials


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
test_cases = [TestCase('create-kubernetes-configuration')]

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

client_id = os.getenv('CLIENT_ID')
if not client_id:
    sys.exit('ERROR: variable CLIENT_ID is required.')

client_secret = os.getenv('CLIENT_SECRET')
if not client_secret:
    sys.exit('ERROR: variable CLIENT_SECRET is required.')

cluster_name = os.getenv('CLUSTER_NAME')
if not cluster_name:
    sys.exit('ERROR: variable CLUSTER_NAME is required.')

cluster_type = os.getenv('CLUSTER_TYPE')
if not cluster_type:
    sys.exit('ERROR: variable CLUSTER_TYPE is required.')

cluster_rp = os.getenv('CLUSTER_RP')
if not cluster_rp:
      sys.exit('ERROR: variable CLUSTER_RP is required')

configuration_name = os.getenv('CONFIGURATION_NAME')
if not configuration_name:
    sys.exit('ERROR: variable CONFIGURATION_NAME is required.')

repository_url = os.getenv('REPOSITORY_URL')
if not repository_url:
    sys.exit('ERROR: variable REPOSITORY_URL is required.')

operator_scope = os.getenv('OPERATOR_SCOPE')
if not operator_scope:
    sys.exit('ERROR: variable OPERATOR_SCOPE is required.')

operator_namespace = os.getenv('OPERATOR_NAMESPACE')
if not operator_namespace:
    sys.exit('ERROR: variable OPERATOR_NAMESPACE is required.')

operator_instance_name = os.getenv('OPERATOR_INSTANCE_NAME')
if not operator_instance_name:
    sys.exit('ERROR: variable OPERATOR_INSTANCE_NAME is required.')

operator_type = os.getenv('OPERATOR_TYPE') if os.getenv('OPERATOR_TYPE') else 'flux'
operator_params = os.getenv('OPERATOR_PARAMS') if os.getenv('OPERATOR_PARAMS') else ''  
enable_helm_operator = True if os.getenv('ENABLE_HELM_OPERATOR') else False
helm_operator_version = os.getenv('HELM_OPERATOR_VERSION') if os.getenv('HELM_OPERATOR_VERSION') else '0.6.0'
helm_operator_params = os.getenv('HELM_OPERATOR_PARAMS') if os.getenv('HELM_OPERATOR_PARAMS') else ''

# Fetch aad token credentials from spn
authority_uri = 'https://login.microsoftonline.com/' + tenant_id
credential = fetch_aad_token_credentials(client_id, client_secret, authority_uri, 'https://management.core.windows.net/')
print("Successfully fetched credentials object.")

# Create the source control configuration
kc_client = get_source_control_configuration_client(credential, subscription_id)
put_kc_response = create_kubernetes_configuration(kc_client, resource_group, repository_url, cluster_rp, cluster_type, cluster_name,
                                                  configuration_name, operator_scope, operator_namespace, operator_instance_name,
                                                  operator_type, operator_params, enable_helm_operator, helm_operator_version,
                                                  helm_operator_params)
append_result_output("{}\n".format(put_kc_response), OUT_FILE)
print("Successfully created the kubernetes configuration resource.")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
