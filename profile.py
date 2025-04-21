# -*- coding: utf-8 -*-
import geni.portal as portal
import geni.rspec.pg as rspec

# Number of PBFT replicas (3f+1; here f=1 -> 4 replicas)
NUM_REPLICAS = 4

# Create a portal context and RSpec request
pc = portal.Context()
request = rspec.Request()

# Create a single LAN for all replicas
lan = request.LAN('lan0')
lan.best_effort = False

# Allocate each replica
for i in range(NUM_REPLICAS):
    # Name them replica0, replica1, ...
    node = request.RawPC('replica{}'.format(i))
    iface = node.addInterface('if0')
    lan.addInterface(iface)

    # Bootstrap script
    node.addService(rspec.Execute(
        shell='bash',
        command="""
#!/bin/bash
set -e

# 1) Install Go and Git
sudo apt-get update
sudo apt-get install -y golang-go git

# 2) Build the PBFT server from the auto‑cloned repo
#    CloudLab will clone your GitHub repo into /local/repository
cd /local/repository/simple_pbft
go build -o server ./cmd/server

# 3) Generate the config file for this replica
mkdir -p config
ip=$(hostname -I | awk '{{print $1}}')
cat > config/config.yaml <<EOF
node:
  id: "replica{replica_id}"
  address: "${{ip}}:800{port_tail}"
network:
  port: {port}
EOF

# 4) Launch the server in the background
./server --config config/config.yaml &
""".format(
            replica_id=i,
            port_tail=i + 1,
            port=8000 + i
        )
    ))

# Finally, print the RSpec so CloudLab can allocate the slice
portal.Context().printRequestRSpec(request)
