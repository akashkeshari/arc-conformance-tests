import sys
import time

from kubernetes import watch


# Returns a kubernetes pod object in given namespace. Object description at: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodList.md
def get_pod(api_instance, namespace, pod_name):
    try:
        return api_instance.read_namespaced_pod(pod_name, namespace)
    except Exception as e:
        sys.exit("Error occured when retrieving pod information: " + str(e))


# Returns a list of kubernetes pod objects in a given namespace. Object description at: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodList.md
def get_pod_list(api_instance, namespace):
    try:
        return api_instance.list_namespaced_pod(namespace)
    except Exception as e:
        sys.exit("Error occurred when retrieving pod information: " + str(e))


# Function that watches events corresponding to pods in the given namespace and passes the events to a callback function
def watch_pod_status(api_instance, namespace, timeout, callback=None):
    if not callback:
        return
    try:
        w = watch.Watch()
        for event in w.stream(api_instance.list_namespaced_pod, namespace, timeout_seconds=timeout):
            if callback(event):
                return
    except Exception as e:
        sys.exit("Error occurred when checking pod status: " + str(e))
    sys.exit("The pods were unable to start before timeout. Please see the pod logs for more info.")


# Function that watches events corresponding to pod logs and passes them to a callback function
def watch_pod_logs(api_instance, namespace, pod_name, container_name, timeout_seconds, callback=None):
    if not callback:
        return
    try:
        w = watch.Watch()
        timeout = time.time() + timeout_seconds
        for event in w.stream(api_instance.read_namespaced_pod_log, pod_name, namespace, container=container_name):
            if callback(event):
                return
            if time.time() > timeout:
                sys.exit("Timed Out. Could not find the required pod log.")
    except Exception as e:
        sys.exit("Error occurred when checking pod logs: " + str(e))
