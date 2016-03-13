"""
Provider implementation based on google-api-python-client library
for GCE.
"""


from cloudbridge.cloud.base import BaseCloudProvider
import json
import os
import time

from googleapiclient import discovery
import httplib2
from oauth2client.client import SignedJwtAssertionCredentials

from .services import GCESecurityService
# from .services import GCEComputeService


class GCECloudProvider(BaseCloudProvider):

    PROVIDER_ID = 'gce'

    def __init__(self, config):
        super(GCECloudProvider, self).__init__(config)

        # Initialize cloud connection fields
        self.client_email = self._get_config_value(
            'gce_client_email', os.environ.get('GCE_CLIENT_EMAIL'))
        self.private_key = self._get_config_value(
            'gce_private_key', os.environ.get('GCE_PRIVATE_KEY'))
        self.project_name = self._get_config_value(
            'gce_project_name', os.environ.get('GCE_PROJECT_NAME'))
        self.credentials_file = self._get_config_value(
            'gce_service_creds_file', os.environ.get('GCE_SERVICE_CREDS_FILE'))
        self.default_zone = self._get_config_value(
            'gce_default_zone', os.environ.get('GCE_DEFAULT_ZONE'))

        # service connections, lazily initialized
        self._gce_compute = None

        # Initialize provider services
        self._security = GCESecurityService(self)
        # self._compute = GCEComputeService(self)

    @property
    def compute(self):
        # return self._compute
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def network(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def security(self):
        return self._security

    @property
    def block_store(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def object_store(self):
        raise NotImplementedError(
            "GCECloudProvider does not implement this service")

    @property
    def gce_compute(self):
        if not self._gce_compute:
            self._gce_compute = self._connect_gce_compute()
        return self._gce_compute

    def _connect_gce_compute(self):
        if self.credentials_file:
            with open(self.credentials_file) as f:
                data = json.load(f)
                credentials = SignedJwtAssertionCredentials(
                    data['client_email'], data['private_key'],
                    'https://www.googleapis.com/auth/compute')
        else:
            credentials = SignedJwtAssertionCredentials(
                self.client_email, self.private_key,
                'https://www.googleapis.com/auth/compute')
        http = httplib2.Http()
        http = credentials.authorize(http)
        return discovery.build('compute', 'v1', http=http)

    def wait_for_global_operation(self, operation):
        while True:
            result = self.gce_compute.globalOperations().get(
                project=self.project_name,
                operation=operation['name']).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(0.5)
