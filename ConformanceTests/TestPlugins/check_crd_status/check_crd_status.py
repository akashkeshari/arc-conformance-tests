import atexit
import os
import sys

from junit_xml import TestCase
from kubernetes import config, client
from results_utility import save_results, create_results_dir, append_result_output
from kubernetes_crd_utility import watch_crd_instance


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
test_cases = [TestCase('check-crd-instance')]

# Saving results when code exits 
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)

# Loading in-cluster kube-config
try:
    config.load_incluster_config()
except Exception as e:
    sys.exit("Error loading the in-cluster config: " + str(e))

# Check environment variables
crd_group = os.getenv('CRD_GROUP')
if not crd_group:
    sys.exit('ERROR: variable CRD_GROUP is required.')

crd_version = os.getenv('CRD_VERSION')
if not crd_version:
    sys.exit('ERROR: variable CRD_VERSION is required.')

crd_namespace = os.getenv('CRD_NAMESPACE')
if not crd_namespace:
    sys.exit('ERROR: variable CRD_NAMESPACE is required.')

crd_plural = os.getenv('CRD_PLURAL')
if not crd_plural:
    sys.exit('ERROR: variable CRD_PLURAL is required.')

crd_name = os.getenv('CRD_NAME')
if not crd_name:
    sys.exit('ERROR: variable CRD_NAME is required.')


# Setting a list of status fields that will be monitored for presence in the CRD instance events
global status_list
status_list = []
if os.getenv('CRD_STATUS_FIELDS'):  # This environment variable should be provided as comma separated status fields that we want to monitor for the CRD instance
    crd_status_fields_list = os.getenv('CRD_STATUS_FIELDS').split(',')
    for status_fields in crd_status_fields_list:
        status_list.append(status_fields.strip())
append_result_output("Status List: {}\n".format(status_list), OUT_FILE)
print("Generated the status fields list.")


# The callback function to check if the crd event received has been updated with the status fields
def crd_event_callback(event):
    try:
        append_result_output("{}\n".format(event), OUT_FILE)
        status_list = globals()['status_list']
        crd_status = event['raw_object'].get('status')
        if not crd_status:
            return False
        for status_fields in status_list:
            if not crd_status.get(status_fields):
                return False
        return True
    except Exception as e:
        sys.exit("Error occured while processing crd event: " + str(e))
    

# Checking if CRD instance has been updated with status fields
timeout = int(os.getenv('TIMEOUT')) if os.getenv('TIMEOUT') else 300
api_instance = client.CustomObjectsApi()
watch_crd_instance(api_instance, crd_group, crd_version, crd_namespace, crd_plural, crd_name, timeout, crd_event_callback)
print("The status fields have been successfully updated in the CRD instance")

# Exit with success
EXIT_CODE = 0
atexit.unregister(save_results)
atexit.register(save_results, RESULTS_TAR_FILENAME, RESULTS_DIR, RESULT_FILE, DONE_FILE, EXIT_CODE, test_cases)
