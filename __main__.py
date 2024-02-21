"""A Python Pulumi program"""

import pulumi
import pulumi_docker

from monitoring.blackbox_exporter import create_blackbox_exporter
from monitoring.cadvisor import create_cadvisor
from monitoring.grafana import create_grafana
from monitoring.node_exporter import create_node_exporter
from monitoring.prometheus import create_prometheus
from monitoring.speedtest import create_speedtest_exporter

provider = pulumi_docker.Provider("synology", host="ssh://synology")

opts = pulumi.ResourceOptions(provider=provider)

# Create networks so we don't have to expose all ports on the host
network = pulumi_docker.Network("monitoring", opts=opts)

# Create node-exporter container
create_node_exporter(network, opts)
create_prometheus(network, opts)
create_grafana(network, opts)
create_cadvisor(network, opts)
create_blackbox_exporter(network, opts)
create_speedtest_exporter(network, opts)
