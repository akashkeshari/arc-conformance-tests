import adal
import sys

from msrestazure.azure_active_directory import AADTokenCredentials


# Function to fetch aad token from spn id and password
def fetch_aad_token(client_id, client_secret, authority_uri, resource_uri):
    """
    Authenticate using service principal w/ key.
    """
    try:
        context = adal.AuthenticationContext(authority_uri, api_version=None)
        return context.acquire_token_with_client_credentials(resource_uri, client_id, client_secret)
    except Exception as e:
        sys.exit("Error occured while fetching aad token: " + str(e))


def fetch_aad_token_credentials(client_id, client_secret, authority_uri, resource_uri):
    mgmt_token = fetch_aad_token(client_id, client_secret, authority_uri, resource_uri)
    try:
        return AADTokenCredentials(mgmt_token, client_id)
    except Exception as e:
        sys.exit("Error occured while fetching credentials: " + str(e))
