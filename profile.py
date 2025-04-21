# -*- coding: utf-8 -*-
import geni.portal as portal
import geni.rspec.pg as rspec
import textwrap

NUM_REPLICAS = 4

pc = portal.Context()
request = rspec.Request()

lan = request.LAN('lan0')
lan.best_effort = False

for i in range(NUM_REPLICAS):
    node = request.RawPC('replica{}'.format(i))
    iface = node.addInterface('if0')
    lan.addInterface(iface)

    bash_script = textwrap.dedent("""\
        #!/bin/bash
        set -e

        # 1) Install Go and Git
        sudo apt-get update
        sudo apt-get install -y golang-go git

        # 2) Build the PBFT server from the auto‑cloned repo
        cd /local/repository/simple_pbft
        go build -o server ./cmd/server

        # 3) Generate the per‑node config
        mkdir -p config
        ip=$(hostname -I | awk '{{print $1}}')
        cat > config/config.yaml <<EOF
        node:
          id: "replica{rid}"
          address: "${{ip}}:800{tail}"
        network:
          port: {port}
        EOF

        # 4) Launch the replica
        ./server --config config/config.yaml &
        """.format(
            rid=i,
            tail=i + 1,
            port=8000 + i
        ))

    node.addService(rspec.Execute(shell='bash', command=bash_script))

portal.Context().printRequestRSpec(request)
