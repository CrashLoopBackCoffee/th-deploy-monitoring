"""
Deploys cadvisor to the target host.
"""
import pulumi_docker as docker
from pulumi import ResourceOptions


def create_cadvisor(network: docker.Network, opts: ResourceOptions()):
    """
    Deploys cadvisor to the target host.
    """
    image = docker.RemoteImage(
        "cadvisor",
        name="gcr.io/cadvisor/cadvisor:v0.47.2",
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        "cadvisor",
        image=image.image_id,
        command=["--disable_metrics=percpu"],
        ports=[
            docker.ContainerPortArgs(internal=8080, external=8081),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=host_path, container_path=container_path, read_only=read_only
            )
            for host_path, container_path, read_only in [
                ("/", "/rootfs", True),
                ("/var/run", "/var/run", False),
                ("/sys", "/sys", True),
                ("/var/lib/docker", "/var/lib/docker", False),
            ]
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["cadvisor"]
            )
        ],
        restart="always",
        start=True,
        opts=opts,
    )
