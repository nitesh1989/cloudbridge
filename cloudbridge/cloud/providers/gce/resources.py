"""
DataTypes used by this provider
"""
from cloudbridge.cloud.base.resources import BaseKeyPair


class GCEKeyPair(BaseKeyPair):

    def __init__(self, provider, kp_id, kp_name, kp_material=None):
        super(GCEKeyPair, self).__init__(provider, None)
        self._kp_id = kp_id
        self._kp_name = kp_name
        self._kp_material = kp_material

    @property
    def id(self):
        return self._kp_id

    @property
    def name(self):
        # use e-mail as keyname if possible, or ID if not
        return self._kp_name or self.id

    def delete(self):
        svc = self._provider.security.key_pairs

        def _delete_key(gce_kp_generator):
            kp_list = []
            for gce_kp in gce_kp_generator:
                if svc.gce_kp_to_id(gce_kp) == self.id:
                    continue
                else:
                    kp_list.append(gce_kp)
            return kp_list

        svc.gce_metadata_save_op(_delete_key)

    @property
    def material(self):
        return self._kp_material

    @material.setter
    def material(self, value):
        self._kp_material = value


from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.base.resources import BaseMachineImage


class GCEMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        super(GCEMachineImage, self).__init__(provider)
        if isinstance(image, GCEMachineImage):
            self._gce_image = image._gce_image
        else:
            self._gce_image = image

    # TODO: Properties missing in GCE -- Ask Enis/Nuwan
    # 1. id
    # 2. description
    # 3. delete: Should this be deleting the image?
    #    Shouldn't this be in GCEImageServices?

    @property
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._gce_image.name

    @property
    def delete(self):
        """
        Delete this self
        """
        self._gce_image.delete(project=self.provider.project_name,
                               image=self._gce_image.name)
        return
