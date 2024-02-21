"""
Deploys the speedtest-exporter
"""

import pulumi_docker
from pulumi import ResourceOptions

from monitoring.utils import get_image


def create_speedtest_exporter(network: pulumi_docker.Network, opts: ResourceOptions):
    """
    Deploys the speedtest-exporter
    """
    speedtest_exporter_image = pulumi_docker.RemoteImage(
        "speedtest-exporter",
        name=get_image("speedtest-exporter"),
        keep_locally=True,
        opts=opts,
    )
    pulumi_docker.Container(
        "speedtest-exporter",
        image=speedtest_exporter_image.image_id,
        ports=[
            pulumi_docker.ContainerPortArgs(internal=9469, external=9469),
        ],
        networks_advanced=[
            pulumi_docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["speedtest-exporter"]
            )
        ],
        restart="always",
        start=True,
        opts=opts,
    )
