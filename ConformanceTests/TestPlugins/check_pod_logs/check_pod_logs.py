import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes import config, client
from kubernetes_pod_utility import watch_pod_logs
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
test_cases = [TestCase('check-arc-agent-pod-log')]

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

pod_name = os.getenv('POD_NAME')
if not pod_name:
    sys.exit('ERROR: variable POD_NAME is required.')

container_name = os.getenv('CONTAINER_NAME')
if not container_name:
    sys.exit('ERROR: variable CONTAINER_NAME is required.')

# Setting a dictionary of logs that will be monitored for presence inside the given pod
global log_dict
log_dict = {}
if os.getenv('LOG_LIST'):  # This environment variable should be provided as comma separated logs that we want to find in the pod logs
    log_list = os.getenv('LOG_LIST').split(',')
    for log in log_list:
        log_dict[log.strip()] = 0
append_result_output("Logs Dict: {}\n".format(log_dict), OUT_FILE)
print("Generated the pod log dictionary.")

# The callback function to examine the pod log
def pod_log_event_callback(event):
    try:
        append_result_output("{}\n".format(event), OUT_FILE)
        log_dict = globals()['log_dict']
        for log in log_dict:
            if log in event:
                log_dict[log] = 1
        if all(ele == 1 for ele in list(log_dict.values())):
            return True
        return False
    except Exception as e:
        sys.exit("Error occured while processing pod log event: " + str(e))

# Checking the pod logs
timeout = int(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') else 300
api_instance = client.CoreV1Api()
watch_pod_logs(api_instance, pod_namespace, pod_name, container_name, timeout, pod_log_event_callback)
print("Successfully checked pod logs.")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
