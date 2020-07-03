import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes import config, client
from kubernetes_pod_utility import get_pod_list, watch_pod_status
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
test_cases = [TestCase('check-arc-agent-pods')]

# Saving results when code exits 
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)

# Loading in-cluster kube-config
try:
    config.load_incluster_config()
except Exception as e:
    sys.exit("Error loading the in-cluster config: " + str(e))

# Check environment variables
pod_namespace = os.getenv('POD_NAMESPACE')
if not pod_namespace:
    sys.exit('ERROR: variable POD_NAMESPACE is required.')

# Setting a dictionary of pods that will be monitored in the provided namespace
global pod_dict
pod_dict = {}
if os.getenv('POD_LIST'):  # This environment variable should be provided as comma separated pod names that we want to monitor in the given namespace
    pod_list = os.getenv('POD_LIST').split(',')
    for pod in pod_list:
        pod_dict[pod.strip()] = 0
append_result_output("Pod dict: {}\n".format(pod_dict), OUT_FILE)
print("Generated the metadata fields dictionary.")

# The callback function to check if the pod is in running state
def pod_event_callback(event):
    try:
        append_result_output("{}\n".format(event), OUT_FILE)
        pod_dict = globals()['pod_dict']
        pod_status = event['raw_object'].get('status')
        pod_name = event['object'].metadata.name
        if pod_status.get('containerStatuses'):
            for container in pod_status.get('containerStatuses'):
                if container.get('restartCount') > 0:
                    sys.exit("The pod {} was restarted. Please see the pod logs for more info.".format(container.get('name')))
                if not container.get('state').get('running'):
                    pod_dict[pod_name] = 0
                    return False
                else:
                    pod_dict[pod_name] = 1
        if all(ele == 1 for ele in list(pod_dict.values())):
            return True
        return False
    except Exception as e:
        sys.exit("Error occured while processing the pod event: " + str(e))

# Checking status of all pods
if pod_dict:
    timeout = int(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') else 300
    api_instance = client.CoreV1Api()
    watch_pod_status(api_instance, pod_namespace, timeout, pod_event_callback)
print("Successfully checked pod status.")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
