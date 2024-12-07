"""
Deploys Blackbox Exporter to the target host.
"""

import pulumi as p
import pulumi_command
import pulumi_docker as docker
import yaml

from monitoring.config import ComponentConfig
from monitoring.utils import get_assets_path, get_image


def create_blackbox_exporter(
    component_config: ComponentConfig, network: docker.Network, opts: p.ResourceOptions
):
    """
    Deploys Blackbox Exporter to the target host.
    """

    target_root_dir = component_config.target.root_dir
    target_host = component_config.target.host
    target_user = component_config.target.user

    prometheus_path = get_assets_path() / 'blackbox-exporter'

    # Create prometheus-config folder
    prometheus_config_dir_resource = pulumi_command.remote.Command(
        'create-blackbox-config',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/blackbox-exporter-config',
    )

    sync_command = (
        f'rsync --rsync-path /bin/rsync -av --delete '
        f'{prometheus_path}/ '
        f'{target_user}@{target_host}:{target_root_dir}/blackbox-exporter-config/'
    )
    with open(prometheus_path / 'blackbox.yml', 'r', encoding='UTF-8') as f:
        blackbox_config = yaml.safe_load(f.read())

    pulumi_command.local.Command(
        'blackbox-config',
        create=sync_command,
        triggers=[blackbox_config, prometheus_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        'blackbox-exporter',
        name=get_image('blackbox-exporter'),
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        'blackbox-exporter',
        image=image.image_id,
        ports=[
            docker.ContainerPortArgs(
                internal=9115,
                external=9115,
            )
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f'{target_root_dir}/blackbox-exporter-config',
                container_path='/config',
                read_only=True,
            )
        ],
        command=[
            '--config.file=/config/blackbox.yml',
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=network.name, aliases=['blackbox-exporter']),
        ],
        restart='always',
        start=True,
        opts=opts,
    )
