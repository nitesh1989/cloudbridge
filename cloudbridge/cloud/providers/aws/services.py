"""
Services implemented by the AWS provider.
"""
import string

from boto.ec2.blockdevicemapping import BlockDeviceMapping
from boto.ec2.blockdevicemapping import BlockDeviceType
from boto.exception import EC2ResponseError
import requests

from cloudbridge.cloud.base.resources import BaseLaunchConfig
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBlockStoreService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseInstanceTypesService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseObjectStoreService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseSecurityGroupService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.resources \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
# from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import Volume

from .resources import AWSBucket
from .resources import AWSInstance
from .resources import AWSInstanceType
from .resources import AWSKeyPair
from .resources import AWSMachineImage
from .resources import AWSNetwork
from .resources import AWSRegion
from .resources import AWSSecurityGroup
from .resources import AWSSnapshot
from .resources import AWSSubnet
from .resources import AWSVolume


class AWSSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(AWSSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AWSKeyPairService(provider)
        self._security_groups = AWSSecurityGroupService(provider)

    @property
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        :rtype: ``object`` of :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        return self._key_pairs

    @property
    def security_groups(self):
        """
        Provides access to security groups for this provider.

        :rtype: ``object`` of :class:`.SecurityGroupService`
        :return: a SecurityGroupService object
        """
        return self._security_groups


class AWSKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(AWSKeyPairService, self).__init__(provider)

    def get(self, key_pair_id):
        """
        Returns a KeyPair given its ID.
        """
        try:
            kps = self.provider.ec2_conn.get_all_key_pairs(
                keynames=[key_pair_id])
            return AWSKeyPair(self.provider, kps[0])
        except EC2ResponseError:
            return None

    def list(self, limit=None, marker=None):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = [AWSKeyPair(self.provider, kp)
                     for kp in self.provider.ec2_conn.get_all_key_pairs()]
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        """
        Searches for a key pair by a given list of attributes.
        """
        try:
            key_pairs = [
                AWSKeyPair(self.provider, kp) for kp in
                self.provider.ec2_conn.get_all_key_pairs(keynames=[name])]
        except EC2ResponseError:
            key_pairs = []
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    def create(self, name):
        """
        Create a new key pair or return an existing one by the same name.

        :type name: str
        :param name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A key pair instance or ``None`` if one was not be created.
        """
        kp = self.get(name)
        if kp:
            return kp
        kp = self.provider.ec2_conn.create_key_pair(name)
        return AWSKeyPair(self.provider, kp)


class AWSSecurityGroupService(BaseSecurityGroupService):

    def __init__(self, provider):
        super(AWSSecurityGroupService, self).__init__(provider)

    def get(self, sg_id):
        """
        Returns a SecurityGroup given its id.
        """
        try:
            sgs = self.provider.ec2_conn.get_all_security_groups(
                group_ids=[sg_id])
            return AWSSecurityGroup(self.provider, sgs[0]) if sgs else None
        except EC2ResponseError:
            return None

    def list(self, limit=None, marker=None):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        sgs = [AWSSecurityGroup(self.provider, sg)
               for sg in self.provider.ec2_conn.get_all_security_groups()]

        return ClientPagedResultList(self.provider, sgs,
                                     limit=limit, marker=marker)

    def create(self, name, description):
        """
        Create a new SecurityGroup.

        :type name: str
        :param name: The name of the new security group.

        :type description: str
        :param description: The description of the new security group.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return:  A SecurityGroup instance or ``None`` if one was not created.
        """
        sg = self.provider.ec2_conn.create_security_group(name, description)
        if sg:
            return AWSSecurityGroup(self.provider, sg)
        return None

    def find(self, name, limit=None, marker=None):
        """
        Get all security groups associated with your account.
        """
        try:
            security_groups = self.provider.ec2_conn.get_all_security_groups(
                groupnames=[name])
        except EC2ResponseError:
            security_groups = []
        return [AWSSecurityGroup(self.provider, sg) for sg in security_groups]

    def delete(self, group_id):
        """
        Delete an existing SecurityGroup.

        :type group_id: str
        :param group_id: The security group ID to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the security group does not exist, ``False``
                  otherwise. Note that this implies that the group may not have
                  been deleted by this method but instead has not existed in
                  the first place.
        """
        try:
            for sg in self.provider.ec2_conn.get_all_security_groups(
                    group_ids=[group_id]):
                try:
                    sg.delete()
                except EC2ResponseError:
                    return False
        except EC2ResponseError:
            pass
        return True


class AWSBlockStoreService(BaseBlockStoreService):

    def __init__(self, provider):
        super(AWSBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AWSVolumeService(self.provider)
        self._snapshot_svc = AWSSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class AWSVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AWSVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        vols = self.provider.ec2_conn.get_all_volumes(volume_ids=[volume_id])
        return AWSVolume(self.provider, vols[0]) if vols else None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filtr = {'tag:Name': name}
        aws_vols = self.provider.ec2_conn.get_all_volumes(filters=filtr)
        cb_vols = [AWSVolume(self.provider, vol) for vol in aws_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all volumes.
        """
        aws_vols = self.provider.ec2_conn.get_all_volumes()
        cb_vols = [AWSVolume(self.provider, vol) for vol in aws_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def create(self, name, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.
        """
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, AWSSnapshot) and snapshot else snapshot

        ec2_vol = self.provider.ec2_conn.create_volume(
            size,
            zone_id,
            snapshot=snapshot_id)
        cb_vol = AWSVolume(self.provider, ec2_vol)
        cb_vol.name = name
        if description:
            cb_vol.description = description
        return cb_vol


class AWSSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(AWSSnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        try:
            snaps = self.provider.ec2_conn.get_all_snapshots(
                snapshot_ids=[snapshot_id])
        except EC2ResponseError as ec2e:
            if ec2e.code == 'InvalidSnapshot.NotFound':
                return None
            raise ec2e
        return AWSSnapshot(self.provider, snaps[0]) if snaps else None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a snapshot by a given list of attributes.
        """
        filtr = {'tag-value': name}
        snaps = [AWSSnapshot(self.provider, snap) for snap in
                 self.provider.ec2_conn.get_all_snapshots(filters=filtr)]
        return ClientPagedResultList(self.provider, snaps,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all snapshots.
        """
        snaps = [AWSSnapshot(self.provider, snap)
                 for snap in self.provider.ec2_conn.get_all_snapshots(
                 owner='self')]
        return ClientPagedResultList(self.provider, snaps,
                                     limit=limit, marker=marker)

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_id = volume.id if isinstance(volume, AWSVolume) else volume

        ec2_snap = self.provider.ec2_conn.create_snapshot(
            volume_id,
            description=description)
        cb_snap = AWSSnapshot(self.provider, ec2_snap)
        cb_snap.name = name
        if description:
            cb_snap.description = description
        return cb_snap


class AWSObjectStoreService(BaseObjectStoreService):

    def __init__(self, provider):
        super(AWSObjectStoreService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        bucket = self.provider.s3_conn.lookup(bucket_id)
        if bucket:
            return AWSBucket(self.provider, bucket)
        else:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a bucket by a given list of attributes.
        """
        buckets = [AWSBucket(self.provider, bucket)
                   for bucket in self.provider.s3_conn.get_all_buckets()
                   if name in bucket.name]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        buckets = [AWSBucket(self.provider, bucket)
                   for bucket in self.provider.s3_conn.get_all_buckets()]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        bucket = self.provider.s3_conn.create_bucket(
            name,
            location=location if location else '')
        return AWSBucket(self.provider, bucket)


class AWSImageService(BaseImageService):

    def __init__(self, provider):
        super(AWSImageService, self).__init__(provider)

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            image = self.provider.ec2_conn.get_image(image_id)
            if image:
                return AWSMachineImage(self.provider, image)
        except EC2ResponseError:
            pass

        return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for an image by a given list of attributes
        """
        filters = {'name': name}
        images = [AWSMachineImage(self.provider, image) for image in
                  self.provider.ec2_conn.get_all_images(filters=filters)]
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        images = [AWSMachineImage(self.provider, image)
                  for image in self.provider.ec2_conn.get_all_images()]
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class AWSComputeService(BaseComputeService):

    def __init__(self, provider):
        super(AWSComputeService, self).__init__(provider)
        self._instance_type_svc = AWSInstanceTypesService(self.provider)
        self._instance_svc = AWSInstanceService(self.provider)
        self._region_svc = AWSRegionService(self.provider)
        self._images_svc = AWSImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def instance_types(self):
        return self._instance_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class AWSInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(AWSInstanceService, self).__init__(provider)

    def create(self, name, image, instance_type, zone=None,
               key_pair=None, security_groups=None, user_data=None,
               launch_config=None,
               **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.id if isinstance(image, MachineImage) else image
        instance_size = instance_type.id if \
            isinstance(instance_type, InstanceType) else instance_type
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        key_pair_name = key_pair.name if isinstance(
            key_pair,
            KeyPair) else key_pair
        if security_groups:
            if isinstance(security_groups, list) and \
                    isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None
        if launch_config:
            bdm = self._process_block_device_mappings(launch_config, zone_id)
            net_id = self._get_net_id(launch_config)
        else:
            bdm = net_id = None

        reservation = self.provider.ec2_conn.run_instances(
            image_id=image_id, instance_type=instance_size,
            min_count=1, max_count=1, placement=zone_id,
            key_name=key_pair_name, security_groups=security_groups_list,
            user_data=user_data, block_device_map=bdm, subnet_id=net_id)
        if reservation:
            instance = AWSInstance(self.provider, reservation.instances[0])
            instance.name = name
        return instance

    def _process_block_device_mappings(self, launch_config, zone=None):
        """
        Processes block device mapping information
        and returns a Boto BlockDeviceMapping object. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        bdm = BlockDeviceMapping()
        # Assign letters from f onwards
        # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html
        next_letter = iter(list(string.ascii_lowercase[6:]))
        # assign ephemeral devices from 0 onwards
        ephemeral_counter = 0
        for device in launch_config.block_devices:
            bd_type = BlockDeviceType()

            if device.is_volume:
                if device.is_root:
                    bdm['/dev/sda1'] = bd_type
                else:
                    bdm['sd' + next(next_letter)] = bd_type

                if isinstance(device.source, Snapshot):
                    bd_type.snapshot_id = device.source.id
                elif isinstance(device.source, Volume):
                    bd_type.volume_id = device.source.id
                elif isinstance(device.source, MachineImage):
                    # Not supported
                    pass
                else:
                    # source is None, but destination is volume, therefore
                    # create a blank volume. If the Zone is None, this
                    # could fail since the volume and instance may be created
                    # in two different zones.
                    if not zone:
                        raise InvalidConfigurationException(
                            "A zone must be specified when launching with a"
                            " new blank volume block device mapping.")
                    new_vol = self.provider.block_store.volumes.create(
                        '',
                        device.size,
                        zone)
                    bd_type.volume_id = new_vol.id
                bd_type.delete_on_terminate = device.delete_on_terminate
                if device.size:
                    bd_type.size = device.size
            else:  # device is ephemeral
                bd_type.ephemeral_name = 'ephemeral%s' % ephemeral_counter

        return bdm

    def _get_net_id(self, launch_config):
        return (launch_config.network_interfaces[0]
                if len(launch_config.network_interfaces) > 0
                else None)

    def create_launch_config(self):
        return BaseLaunchConfig(self.provider)

    def get(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.
        """
        reservation = self.provider.ec2_conn.get_all_reservations(
            instance_ids=[instance_id])
        if reservation:
            return AWSInstance(self.provider, reservation[0].instances[0])
        else:
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.Instance`
        :return: an Instance object
        """
        filtr = {'tag:Name': name}
        reservations = self.provider.ec2_conn.get_all_reservations(
            filters=filtr,
            max_results=limit,
            next_token=marker)
        instances = [AWSInstance(self.provider, inst)
                     for res in reservations
                     for inst in res.instances]
        return ServerPagedResultList(reservations.is_truncated,
                                     reservations.next_token,
                                     False, data=instances)

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        reservations = self.provider.ec2_conn.get_all_reservations(
            max_results=limit,
            next_token=marker)
        instances = [AWSInstance(self.provider, inst)
                     for res in reservations
                     for inst in res.instances]
        return ServerPagedResultList(reservations.is_truncated,
                                     reservations.next_token,
                                     False, data=instances)

AWS_INSTANCE_DATA_DEFAULT_URL = "https://swift.rc.nectar.org.au:8888/v1/" \
                                "AUTH_377/cloud-bridge/aws/instance_data.json"


class AWSInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(AWSInstanceTypesService, self).__init__(provider)

    @property
    def instance_data(self):
        """
        TODO: Needs a caching function with timeout
        """
        r = requests.get(self.provider.config.get(
            "aws_instance_info_url", AWS_INSTANCE_DATA_DEFAULT_URL))
        return r.json()

    def list(self, limit=None, marker=None):
        inst_types = [AWSInstanceType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class AWSRegionService(BaseRegionService):

    def __init__(self, provider):
        super(AWSRegionService, self).__init__(provider)

    def get(self, region_id):
        region = self.provider.ec2_conn.get_all_regions(
            region_names=[region_id])
        if region:
            return AWSRegion(self.provider, region[0])
        else:
            return None

    def list(self, limit=None, marker=None):
        regions = [AWSRegion(self.provider, region)
                   for region in self.provider.ec2_conn.get_all_regions()]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self):
        return self.get(self._provider.region_name)


class AWSNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(AWSNetworkService, self).__init__(provider)
        self._subnet_svc = AWSSubnetService(self.provider)

    def get(self, network_id):
        network = self.provider.vpc_conn.get_all_vpcs(vpc_ids=[network_id])
        if network:
            return AWSNetwork(self.provider, network[0])
        return None

    def list(self, limit=None, marker=None):
        networks = [AWSNetwork(self.provider, network)
                    for network in self.provider.vpc_conn.get_all_vpcs()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def create(self, name=None):
        # AWS requried CIDR block to be specified when creating a network
        # so set a default one and use the largest possible netmask.
        default_cidr = '10.0.0.0/16'
        network = self.provider.vpc_conn.create_vpc(cidr_block=default_cidr)
        cb_network = AWSNetwork(self.provider, network)
        if name:
            cb_network.name = name
        return cb_network

    @property
    def subnets(self):
        return self._subnet_svc


class AWSSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AWSSubnetService, self).__init__(provider)

    def get(self, subnet_id):
        subnets = self.provider.vpc_conn.get_all_subnets([subnet_id])
        if subnets:
            return AWSSubnet(self.provider, subnets[0])
        return None

    def list(self, network=None):
        fltr = None
        if network:
            network_id = (network.id if isinstance(network, AWSNetwork) else
                          network)
            fltr = {'vpc-id': network_id}
        subnets = self.provider.vpc_conn.get_all_subnets(filters=fltr)
        return [AWSSubnet(self.provider, subnet) for subnet in subnets]

    def create(self, network, cidr_block, name=None):
        network_id = network.id if isinstance(network, AWSNetwork) else network
        subnet = self.provider.vpc_conn.create_subnet(network_id, cidr_block)
        cb_subnet = AWSSubnet(self.provider, subnet)
        if name:
            cb_subnet.name = name
        return cb_subnet

    def delete(self, subnet):
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        return self.provider.vpc_conn.delete_subnet(subnet_id=subnet_id)
