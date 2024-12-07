"""
Deploys Prometheus to the target host.
"""

import urllib.request

import pulumi
import pulumi_command
import pulumi_docker as docker
import yaml
from pulumi import ResourceOptions

from monitoring.utils import get_assets_path, get_image


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
    prometheus_host = config.get("prometheus-host")

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
        name=get_image("prometheus"),
        keep_locally=True,
        opts=opts,
    )

    container = docker.Container(
        "prometheus",
        image=image.image_id,
        command=[
            "--web.enable-lifecycle",
            "--config.file=/etc/prometheus/prometheus.yml",
            "--storage.tsdb.retention.time=720d",
        ],
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

    # Reload prometheus config after pushing config and runnnig the container
    def reload_prometheus(_):
        if pulumi.runtime.is_dry_run():
            return

        print("Reloading prometheus config")
        req = urllib.request.Request(
            f"https://{prometheus_host}/-/reload", method="POST"
        )
        with urllib.request.urlopen(req):
            pass

    pulumi.Output.all(prometheus_config_dir_resource.id, container.id).apply(
        reload_prometheus
    )
