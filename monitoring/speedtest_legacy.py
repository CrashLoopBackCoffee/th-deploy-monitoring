"""
Deploys the speedtest-exporter
"""

import pulumi as p
import pulumi_docker

from monitoring.config import ComponentConfig


def create_speedtest_exporter(
    component_config: ComponentConfig, network: pulumi_docker.Network, opts: p.ResourceOptions
):
    """
    Deploys the speedtest-exporter
    """
    assert component_config.speedtest_exporter
    speedtest_exporter_image = pulumi_docker.RemoteImage(
        'speedtest-exporter',
        name=f'ghcr.io/billimek/prometheus-speedtest-exporter:{component_config.speedtest_exporter.version}',
        keep_locally=True,
        opts=opts,
    )
    pulumi_docker.Container(
        'speedtest-exporter',
        image=speedtest_exporter_image.image_id,
        name='speedtest-exporter',
        ports=[
            pulumi_docker.ContainerPortArgs(internal=9469, external=9469),
        ],
        networks_advanced=[
            pulumi_docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=['speedtest-exporter']
            )
        ],
        restart='always',
        start=True,
        opts=opts,
    )
