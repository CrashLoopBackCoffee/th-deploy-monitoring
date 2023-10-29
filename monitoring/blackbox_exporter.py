"""
Deploys Blackbox Exporter to the target host.
"""

import pulumi
import pulumi_command
import pulumi_docker as docker
import yaml
from pulumi import ResourceOptions

from monitoring.utils import get_assets_path, get_image

# docker run --rm \
#   -p 9115/tcp \
#   --name blackbox_exporter \
#   -v $(pwd):/config \
#   quay.io/prometheus/blackbox-exporter:latest --config.file=/config/blackbox.yml


def create_blackbox_exporter(network: docker.Network, opts: ResourceOptions):
    """
    Deploys Blackbox Exporter to the target host.
    """

    config = pulumi.Config()

    target_root_dir = config.get("root-dir")
    target_host = config.get("target-host")
    target_user = config.get("target-user")

    prometheus_path = get_assets_path() / "blackbox-exporter"

    # Create prometheus-config folder
    prometheus_config_dir_resource = pulumi_command.remote.Command(
        "create-blackbox-config",
        connection=pulumi_command.remote.ConnectionArgs(
            host=target_host, user=target_user
        ),
        create=f"mkdir -p {target_root_dir}/blackbox-exporter-config",
    )

    sync_command = (
        f"rsync --rsync-path /bin/rsync -av --delete "
        f"{prometheus_path}/ "
        f"{target_user}@{target_host}:{target_root_dir}/blackbox-exporter-config/"
    )
    with open(prometheus_path / "blackbox.yml", "r", encoding="UTF-8") as f:
        blackbox_config = yaml.safe_load(f.read())

    pulumi_command.local.Command(
        "blackbox-config",
        create=sync_command,
        triggers=[blackbox_config, prometheus_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        "blackbox-exporter",
        name=get_image("blackbox-exporter"),
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        "blackbox-exporter",
        image=image.image_id,
        ports=[
            docker.ContainerPortArgs(
                internal=9115,
                external=9115,
            )
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f"{target_root_dir}/blackbox-exporter-config",
                container_path="/config",
                read_only=True,
            )
        ],
        command=[
            "--config.file=/config/blackbox.yml",
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["blackbox-exporter"]
            ),
        ],
        restart="always",
        start=True,
        opts=opts,
    )
