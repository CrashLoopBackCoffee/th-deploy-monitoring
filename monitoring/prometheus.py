"""
Deploys Prometheus to the target host.
"""
import pulumi
import pulumi_command
import pulumi_docker as docker
import yaml
from pulumi import ResourceOptions

from monitoring.utils import get_assets_path


def create_prometheus(
    network: docker.Network,
    opts: ResourceOptions,
):
    """
    Deploys Prometheus to the target host.
    """
    config = pulumi.Config()

    target_root_dir = config.get("root-dir")
    target_host = config.get("target-host")
    target_user = config.get("target-user")

    prometheus_path = get_assets_path() / "prometheus"

    # Create prometheus-config folder
    prometheus_config_dir_resource = pulumi_command.remote.Command(
        "create-prometheus-config",
        connection=pulumi_command.remote.ConnectionArgs(
            host=target_host, user=target_user
        ),
        create=f"mkdir -p {target_root_dir}/prometheus-config",
    )

    sync_command = (
        f"rsync --rsync-path /bin/rsync -av --delete "
        f"{prometheus_path}/ "
        f"{target_user}@{target_host}:{target_root_dir}/prometheus-config/"
    )
    with open(prometheus_path / "prometheus.yml", "r", encoding="UTF-8") as f:
        prometheus_config = yaml.safe_load(f.read())
    pulumi_command.local.Command(
        "prometheus-config",
        create=sync_command,
        triggers=[prometheus_config, prometheus_config_dir_resource.id],
    )

    image = docker.RemoteImage(
        "prometheus",
        name="quay.io/prometheus/prometheus:v2.37.7",
        keep_locally=True,
        opts=opts,
    )

    docker.Container(
        "prometheus",
        image=image.image_id,
        ports=[
            docker.ContainerPortArgs(internal=9090, external=9090),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                host_path=f"{target_root_dir}/prometheus-config",
                container_path="/etc/prometheus",
                read_only=True,
            ),
            docker.ContainerVolumeArgs(
                host_path=f"{target_root_dir}/prometheus",
                container_path="/prometheus",
            ),
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(
                name=network.name, aliases=["prometheus"]
            ),
        ],
        restart="always",
        start=True,
        opts=opts,
    )
