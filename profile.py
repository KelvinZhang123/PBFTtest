# -*- coding: utf-8 -*-
import geni.portal as portal
import geni.rspec.pg as rspec

NUM_REPLICAS = 4

pc = portal.Context()
request = rspec.Request()

lan = request.LAN('lan0')
lan.best_effort = False

for i in range(NUM_REPLICAS):
    node = request.RawPC('replica{}'.format(i))
    iface = node.addInterface('if0')
    lan.addInterface(iface)

    node.addService(rspec.Execute(
        shell='bash',
        command="""
#!/bin/bash
set -e

# Install prerequisites
sudo apt-get update
sudo apt-get install -y golang-go git

# Clone and build simple_pbft from your GitHub
git clone https://github.com/yourusername/simple_pbft.git
cd simple_pbft
go build -o server ./cmd/server

# Generate config file
mkdir -p config
ip=$(hostname -I | awk '{{print $1}}')    # Double {{ }} here
cat > config/config.yaml <<EOF
node:
  id: "replica{replica_id}"
  address: "${{ip}}:800{port_tail}"
network:
  port: {port}
EOF

# Run the PBFT server
./server --config config/config.yaml &
""".format(
            replica_id=i,
            port_tail=i + 1,
            port=8000 + i
        )
    ))

portal.Context().printRequestRSpec(request)
