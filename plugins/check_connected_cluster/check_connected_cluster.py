import atexit
import os
import sys
import time

from azure.mgmt.hybridkubernetes import ConnectedKubernetesClient
from arm_rest_utility import fetch_aad_token_credentials
from connected_cluster_utility import get_connected_cluster_client, get_connected_cluster
from results_utility import save_results, create_results_dir, append_result_output


# This directory contains all result files corresponding to sonobuoy test run
RESULTS_DIR = '/tmp/results'

RESULTS_TAR_FILENAME = 'results.tar.gz'

# This directory needs to be updated with the path to results file so that the sonobuoy worker understands that the test plugin container has completed its work.
DONE_FILE = RESULTS_DIR + '/done'

# This directory is used to dump any logs from the test run
OUT_FILE = RESULTS_DIR + '/out'

# Creating the results directory
create_results_dir(RESULTS_DIR)

# Saving results when code exits 
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, DONE_FILE)

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

client_id = os.getenv('CLIENT_ID')
if not client_id:
    sys.exit('ERROR: variable CLIENT_ID is required.')

client_secret = os.getenv('CLIENT_SECRET')
if not client_secret:
    sys.exit('ERROR: variable CLIENT_SECRET is required.')

# Fetch aad token credentials from spn
authority_uri = 'https://login.microsoftonline.com/' + tenant_id
credential = fetch_aad_token_credentials(client_id, client_secret, authority_uri, 'https://management.core.windows.net/')
print("Successfully fetched credentials object.")

# Check provisioning state of the connected cluster resource
cc_client = get_connected_cluster_client(credential, subscription_id)
timeout = time.time() + 300
provisioning_state = None
while True:
    provisioning_state = get_connected_cluster(cc_client, resource_group, cluster_name).provisioning_state
    append_result_output("Provisioning State: {}\n".format(provisioning_state), OUT_FILE)
    if provisioning_state == 'Succeeded':
        break
    if (provisioning_state == 'Failed' or provisioning_state == 'Cancelled'):
        sys.exit("ERROR: The connected cluster creation finished with terminal provisioning state {}. ".format(provisioning_state))
    if time.time() > timeout:
        sys.exit("ERROR: Timeout. The connected cluster is in non terminal provisioning state.")
    time.sleep(10)
print("The connected cluster resource was created successfully.")
