"""
Deploy Grafana container
"""
import pulumi
import pulumi_command
import pulumi_docker as docker
import yaml
from pulumi import ResourceOptions

from monitoring.utils import get_assets_path, get_image


def create_grafana(network: docker.Network, opts: ResourceOptions):
    """
    Deploy Grafana container
    """
    config = pulumi.Config()
    target_root_dir = config.get("root-dir")
    target_host = config.get("target-host")
    target_user = config.get("target-user")

    grafana_path = get_assets_path() / "grafana"

    # Create grafana-config folder
    grafana_config_dir_resource = pulumi_command.remote.Command(
        "create-grafana-config",
        connection=pulumi_command.remote.ConnectionArgs(
            host=target_host, user=target_user
        ),
        create=f"mkdir -p {target_root_dir}/grafana-config",
    )

    sync_command = (
        f"rsync --rsync-path /bin/rsync -av --delete "
        f"{grafana_path}/ "
        f"{target_user}@{target_host}:{target_root_dir}/grafana-config/"
    )
    with open(
        grafana_path / "provisioning" / "datasources" / "datasources.yml",
        "r",
        encoding="UTF-8",
    ) as f:
        grafana_datasources = yaml.safe_load(f.read())

    pulumi_command.local.Command(
        "grafana-config",
        create=sync_command,
        triggers=[grafana_datasources, grafana_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        "grafana",
        name=get_image("grafana"),
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        "grafana",
        image=image.image_id,
        ports=[
            docker.ContainerPortArgs(internal=3000, external=3000),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f"{target_root_dir}/grafana-config/provisioning",
                container_path="/etc/grafana/provisioning",
            ),
            docker.ContainerVolumeArgs(
                host_path=f"{target_root_dir}/grafana",
                container_path="/var/lib/grafana",
            ),
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["node-exporter"]
            )
        ],
        restart="always",
        start=True,
        opts=opts,
    )
