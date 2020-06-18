import sys


def get_custom_object(api_instance, group, version, namespace, plural, crd_name):
    try:
        return api_instance.get_namespaced_custom_object(group, version, namespace, plural, crd_name)
    except Exception as e:
        sys.exit("Error occurred when retrieving crd information: " + str(e))