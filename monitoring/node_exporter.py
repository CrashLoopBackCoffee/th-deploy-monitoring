"""
Deploys the node-exporter
"""

import pulumi_docker
from pulumi import ResourceOptions

from monitoring.utils import get_image


def create_node_exporter(network: pulumi_docker.Network, opts: ResourceOptions):
    """
    Deploys the node-exporter
    """
    node_exporter_image = pulumi_docker.RemoteImage(
        "node-exporter",
        name=get_image("node-exporter"),
        keep_locally=True,
        opts=opts,
    )
    pulumi_docker.Container(
        "node-exporter",
        image=node_exporter_image.image_id,
        ports=[
            pulumi_docker.ContainerPortArgs(internal=9100, external=9100),
        ],
        volumes=[
            pulumi_docker.ContainerVolumeArgs(
                host_path=host_path, container_path=container_path, read_only=True
            )
            for host_path, container_path in [
                ("/", "/host"),
                ("/proc", "/host/proc"),
                ("/sys", "/host/sys"),
                ("/", "/rootfs"),
            ]
        ],
        command=[
            "--path.procfs=/host/proc",
            "--path.rootfs=/host",
            "--path.sysfs=/host/sys",
            "--collector.filesystem.ignored-mount-points",
            "^/(sys|proc|dev|host|etc|rootfs/var/lib/docker/containers|"
            "rootfs/var/lib/docker/overlay2|rootfs/run/docker/netns|"
            "rootfs/var/lib/docker/aufs)($$|/)",
        ],
        networks_advanced=[
            pulumi_docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["node-exporter"]
            )
        ],
        restart="always",
        start=True,
        opts=opts,
    )
