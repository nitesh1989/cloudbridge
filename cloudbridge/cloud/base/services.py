"""
Base implementation for services available through a provider
"""
from cloudbridge.cloud.interfaces.services import BlockStoreService
from cloudbridge.cloud.interfaces.services import CloudService
from cloudbridge.cloud.interfaces.services import ComputeService
from cloudbridge.cloud.interfaces.services import ImageService
from cloudbridge.cloud.interfaces.services import InstanceService
from cloudbridge.cloud.interfaces.services import InstanceTypesService
from cloudbridge.cloud.interfaces.services import KeyPairService
from cloudbridge.cloud.interfaces.services import ObjectStoreService
from cloudbridge.cloud.interfaces.services import RegionService
from cloudbridge.cloud.interfaces.services import SecurityGroupService
from cloudbridge.cloud.interfaces.services import SecurityService
from cloudbridge.cloud.interfaces.services import SnapshotService
from cloudbridge.cloud.interfaces.services import VolumeService
from .resources import BasePageableObjectMixin


class BaseCloudService(CloudService):

    def __init__(self, provider):
        self._provider = provider

    @property
    def provider(self):
        return self._provider


class BaseComputeService(ComputeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseComputeService, self).__init__(provider)


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)


class BaseBlockStoreService(BlockStoreService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBlockStoreService, self).__init__(provider)


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)


class BaseObjectStoreService(
        BasePageableObjectMixin, ObjectStoreService, BaseCloudService):

    def __init__(self, provider):
        super(BaseObjectStoreService, self).__init__(provider)


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseCloudService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)

    def delete(self, keypair_id):
        """
        Delete an existing key pair.

        :type keypair_id: str
        :param keypair_id: The id of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist. Note that this implies
                  that the key may not have been deleted by this method but
                  instead has not existed in the first place.
        """
        kp = self.get(keypair_id)
        if kp:
            kp.delete()
        return True


class BaseSecurityGroupService(
        BasePageableObjectMixin, SecurityGroupService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityGroupService, self).__init__(provider)


class BaseInstanceTypesService(
        BasePageableObjectMixin, InstanceTypesService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceTypesService, self).__init__(provider)

    def find(self, **kwargs):
        name = kwargs.get('name')
        if name:
            return [itype for itype in self.list() if itype.name == name]
        else:
            raise TypeError(
                "Invalid parameters for search. Supported attributes: {name}")


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)
