"""A Python Pulumi program"""


import pulumi
import pulumi_docker

from monitoring.node_exporter import create_node_exporter
from monitoring.prometheus import create_prometheus

provider = pulumi_docker.Provider("synology", host="ssh://synology")

opts = pulumi.ResourceOptions(provider=provider)

# Create networks so we don't have to expose all ports on the host
network = pulumi_docker.Network("monitoring", opts=opts)

# Create node-exporter container
create_node_exporter(network, opts)
create_prometheus(network, opts)
