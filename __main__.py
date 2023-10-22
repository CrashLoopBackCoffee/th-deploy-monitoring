"""A Python Pulumi program"""

import pulumi
import pulumi_docker
from pulumi_docker import ContainerVolumeArgs

provider = pulumi_docker.Provider("synology", host="ssh://synology")

opts = pulumi.ResourceOptions(provider=provider)
# shared_volume = pulumi_docker.Volume('test', opts=opts)

# Create node-exporter container
node_exporter_image = pulumi_docker.RemoteImage(
    "node-exporter",
    name="quay.io/prometheus/node-exporter:latest",
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
        ContainerVolumeArgs(host_path="/", container_path="/host", read_only=True),
        ContainerVolumeArgs(
            host_path="/proc", container_path="/host/proc", read_only=True
        ),
        ContainerVolumeArgs(
            host_path="/sys", container_path="/host/sys", read_only=True
        ),
        ContainerVolumeArgs(host_path="/", container_path="/rootfs", read_only=True),
    ],
    command=[
        "--path.procfs=/host/proc",
        "--path.rootfs=/host",
        "--path.sysfs=/host/sys",
        "--collector.filesystem.ignored-mount-points",
        "^/(sys|proc|dev|host|etc|rootfs/var/lib/docker/containers|rootfs/var/lib/docker/overlay2|rootfs/run/docker/netns|rootfs/var/lib/docker/aufs)($$|/)",
    ],
    restart="always",
    start=True,
    opts=opts,
)
