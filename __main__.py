"""A Python Pulumi program"""


import pulumi
import pulumi_docker

from monitoring.node_exporter import create_node_exporter

provider = pulumi_docker.Provider("synology", host="ssh://synology")

opts = pulumi.ResourceOptions(provider=provider)

# Create networks so we don't have to expose all ports on the host
network_frontend = pulumi_docker.Network("monitoring-frontend", opts=opts)
network_backend = pulumi_docker.Network("monitoring-backend", opts=opts)

# Create node-exporter container
create_node_exporter(network_backend, opts)
