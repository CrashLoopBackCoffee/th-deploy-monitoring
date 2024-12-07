"""A Python Pulumi program"""

import pulumi as p
import pulumi_docker

from monitoring.alloy import create_alloy
from monitoring.blackbox_exporter import create_blackbox_exporter
from monitoring.cadvisor import create_cadvisor
from monitoring.config import ComponentConfig
from monitoring.grafana import create_grafana
from monitoring.node_exporter import create_node_exporter
from monitoring.prometheus import create_prometheus
from monitoring.speedtest import create_speedtest_exporter

component_config = ComponentConfig.model_validate(p.Config().get_object('config'))

provider = pulumi_docker.Provider('synology', host='ssh://synology')

opts = p.ResourceOptions(provider=provider)

# Create networks so we don't have to expose all ports on the host
network = pulumi_docker.Network('monitoring', opts=opts)

# Create node-exporter container
create_node_exporter(network, opts)
create_prometheus(component_config, network, opts)
create_grafana(component_config, network, opts)
create_cadvisor(network, opts)
create_blackbox_exporter(component_config, network, opts)
create_speedtest_exporter(network, opts)
create_alloy(component_config, network, opts)
