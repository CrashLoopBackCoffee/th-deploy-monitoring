"""A Python Pulumi program"""

import pulumi
import pulumi_docker
from pulumi_docker import ContainerVolumeArgs

provider = pulumi_docker.Provider("synology", host="ssh://synology")

opts = pulumi.ResourceOptions(provider=provider)

# Create networks so we don't have to expose all ports on the host
network_frontend = pulumi_docker.Network("monitoring-frontend", opts=opts)
network_backend = pulumi_docker.Network("monitoring-backend", opts=opts)

# Create node-exporter container
node_exporter_image = pulumi_docker.RemoteImage(
    "node-exporter",
    name="quay.io/prometheus/node-exporter:v1.6.1",
    keep_locally=True,
    opts=opts,
)
node_exporter = pulumi_docker.Container(
    "node-exporter",
    image=node_exporter_image.name,
    ports=[
        pulumi_docker.ContainerPortArgs(internal=9100, external=9100),
    ],
    volumes=[
        ContainerVolumeArgs(
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
        "rootfs/var/lib/docker/overlay2|rootfs/run/docker/netns|rootfs/var/lib/docker/aufs)($$|/)",
    ],
    networks_advanced=[
        pulumi_docker.ContainerNetworksAdvancedArgs(
            name=network_backend.name, aliases=["node-exporter"]
        )
    ],
    restart="always",
    start=True,
    opts=opts,
)
