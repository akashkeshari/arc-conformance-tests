import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes import config, client
from results_utility import save_results, create_results_dir
from kubernetes_secret_utility import watch_kubernetes_secret


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
test_cases = [TestCase('check-kubernetes-secret')]

# Saving results when code exits 
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)

# Loading in-cluster kube-config
try:
    config.load_incluster_config()
except Exception as e:
    sys.exit("Error loading the in-cluster config: " + str(e))

# Check environment variables
secret_namespace = os.getenv('SECRET_NAMESPACE')
if not secret_namespace:
    sys.exit('ERROR: variable SECRET_NAMESPACE is required.')

secret_name = os.getenv('SECRET_NAME')
if not secret_name:
    sys.exit('ERROR: variable SECRET_NAME is required.')

# The callback function to check if the secret event received has secret data
def secret_event_callback(event):
    try:
        secret_data = event['raw_object'].get('data')
        if not secret_data:
            return False   
        return True
    except Exception as e:
        sys.exit("Error occured while processing secret event: " + str(e))

# Checking if the kubernetes secret has secret data
timeout = int(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') else 300
api_instance = client.CoreV1Api()
watch_kubernetes_secret(api_instance, secret_namespace, secret_name, timeout, secret_event_callback)
print("The secret data was retrieved successfully.")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
