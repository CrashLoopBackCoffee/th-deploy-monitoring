"""
Deploys Prometheus to the target host.
"""

import urllib.request

import pulumi as p
import pulumi_cloudflare as cloudflare
import pulumi_command
import pulumi_docker as docker
import yaml

from monitoring.cloudflare import create_cloudflare_cname
from monitoring.config import ComponentConfig
from monitoring.utils import get_assets_path, get_image


def create_prometheus(
    component_config: ComponentConfig,
    network: docker.Network,
    cloudflare_provider: cloudflare.Provider,
    opts: p.ResourceOptions,
):
    """
    Deploys Prometheus to the target host.
    """
    target_root_dir = component_config.target.root_dir
    target_host = component_config.target.host
    target_user = component_config.target.user

    prometheus_path = get_assets_path() / 'prometheus'

    # Create prometheus DNS record
    dns_record = create_cloudflare_cname(
        'prometheus', component_config.cloudflare.zone, cloudflare_provider
    )

    # Create prometheus-config folder
    prometheus_config_dir_resource = pulumi_command.remote.Command(
        'create-prometheus-config',
        connection=pulumi_command.remote.ConnectionArgs(host=target_host, user=target_user),
        create=f'mkdir -p {target_root_dir}/prometheus-config',
    )

    sync_command = (
        f'rsync --rsync-path /bin/rsync -av --delete '
        f'{prometheus_path}/ '
        f'{target_user}@{target_host}:{target_root_dir}/prometheus-config/'
    )
    with open(prometheus_path / 'prometheus.yml', 'r', encoding='UTF-8') as f:
        prometheus_config = yaml.safe_load(f.read())
    pulumi_command.local.Command(
        'prometheus-config',
        create=sync_command,
        triggers=[prometheus_config, prometheus_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        'prometheus',
        name=get_image('prometheus'),
        keep_locally=True,
        opts=opts,
    )

    container = docker.Container(
        'prometheus',
        image=image.image_id,
        command=[
            '--web.enable-lifecycle',
            '--config.file=/etc/prometheus/prometheus.yml',
            '--storage.tsdb.retention.time=720d',
        ],
        ports=[
            docker.ContainerPortArgs(internal=9090, external=9090),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f'{target_root_dir}/prometheus-config',
                container_path='/etc/prometheus',
                read_only=True,
            ),
            docker.ContainerVolumeArgs(
                host_path=f'{target_root_dir}/prometheus',
                container_path='/prometheus',
            ),
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=network.name, aliases=['prometheus']),
        ],
        restart='always',
        start=True,
        opts=opts,
    )

    # Reload prometheus config after pushing config and runnnig the container
    def reload_prometheus(args):
        if p.runtime.is_dry_run():
            return

        hostname = args[0]
        print('Reloading prometheus config for {hostname}')
        req = urllib.request.Request(f'https://{hostname}/-/reload', method='POST')
        with urllib.request.urlopen(req):
            pass

    p.Output.all(dns_record.hostname, prometheus_config_dir_resource.id, container.id).apply(
        reload_prometheus
    )
