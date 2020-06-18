import atexit
import os

from kubernetes import config, client
from kubernetes_pod_utility import get_pod_list, check_pod_status
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

# Loading in-cluster kube-config
config.load_incluster_config()

# Getting list of all pods in the azure-arc namespace
namespace = os.getenv('POD_NAMESPACE') if os.getenv('POD_NAMESPACE') else 'azure-arc'
api_instance = client.CoreV1Api()
pod_list = get_pod_list(api_instance, namespace)
append_result_output("{}\n".format(pod_list), OUT_FILE)
print("Successfully fetched pod list.")

# Checking status of all pods
check_pod_status(api_instance, pod_list)
print("Successfully checked pod status.")
