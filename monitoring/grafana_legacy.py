"""
Deploy Grafana container
"""

import pulumi as p
import pulumi_cloudflare as cloudflare
import pulumi_command
import pulumi_docker as docker
import yaml

from monitoring.cloudflare import create_cloudflare_cname
from monitoring.config import ComponentConfig
from monitoring.utils import get_assets_path


def create_grafana(
    component_config: ComponentConfig,
    network: docker.Network,
    cloudflare_provider: cloudflare.Provider,
    opts: p.ResourceOptions,
):
    """
    Deploy Grafana container
    """
    assert component_config.target
    assert component_config.cloudflare
    assert component_config.grafana
    target_root_dir = component_config.target.root_dir
    target_host = component_config.target.host
    target_user = component_config.target.user

    grafana_path = get_assets_path() / 'grafana'

    # Create alloy DNS record
    create_cloudflare_cname('grafana', component_config.cloudflare.zone, cloudflare_provider)

    # Create grafana-config folder
    grafana_config_dir_resource = pulumi_command.remote.Command(
        'create-grafana-config',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/grafana-config',
    )

    sync_command = (
        f'rsync --rsync-path /bin/rsync -av --delete '
        f'{grafana_path}/ '
        f'{target_user}@{target_host}:{target_root_dir}/grafana-config/'
    )
    with open(
        grafana_path / 'provisioning' / 'datasources' / 'datasources.yml',
        'r',
        encoding='UTF-8',
    ) as f:
        grafana_datasources = yaml.safe_load(f.read())

    pulumi_command.local.Command(
        'grafana-config',
        create=sync_command,
        triggers=[grafana_datasources, grafana_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        'grafana',
        name=f'grafana/grafana:{component_config.grafana.version}',
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        'grafana',
        image=image.image_id,
        name='grafana',
        ports=[
            docker.ContainerPortArgs(internal=3000, external=3000),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f'{target_root_dir}/grafana-config/provisioning',
                container_path='/etc/grafana/provisioning',
            ),
            docker.ContainerVolumeArgs(
                host_path=f'{target_root_dir}/grafana',
                container_path='/var/lib/grafana',
            ),
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=network.name, aliases=['grafana'])
        ],
        restart='always',
        start=True,
        opts=opts,
    )
