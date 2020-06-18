import sys

from kubernetes import watch


# Returns a list of kubernetes pod objects in a given namespace. Object description at: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1PodList.md
def get_pod_list(api_instance, namespace):
    try:
        api_response = api_instance.list_namespaced_pod(namespace)
    except Exception as e:
        sys.exit("Error occurred when retrieving pod information: " + str(e))
    return api_response


# Checks the status of all the pods present in the given pod list.
def check_pod_status(api_instance, pod_list):
    # Creating a pod dictionary from the pod list received above with key as pod name and iniial value as 0
    pod_dict = {}
    for pod in pod_list.items:
        pod_dict[pod.metadata.name] = 0
    # Starting the watch on pods
    w = watch.Watch()
    try:
        for event in w.stream(api_instance.list_namespaced_pod, namespace='azure-arc', timeout_seconds=360):
            pod_status = event['raw_object'].get('status')
            pod_name = event['object'].metadata.name
            if pod_status.get('containerStatuses'):
                for container in pod_status.get('containerStatuses'):
                    if container.get('restartCount') > 0:
                        sys.exit("The pod {} was restarted. Please see the pod logs for more info.".format(container.get('name')))
                    if not container.get('state').get('running'):
                        pod_dict[pod_name] = 0
                        break
                    else:
                        pod_dict[pod_name] = 1
            if all(ele == 1 for ele in list(pod_dict.values())):
                return
    except Exception as e:
        sys.exit("Error occurred when checking pod status: " + str(e))
    sys.exit("The pods were unable to start before timeout. Please see the pod logs for more info.")
