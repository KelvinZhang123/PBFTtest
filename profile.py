# -*- coding: utf-8 -*-
import geni.portal as portal
import geni.rspec.pg as rspec

NUM_REPLICAS = 4

pc = portal.Context()
request = rspec.Request()

lan = request.LAN("lan0")
lan.best_effort = False

for i in range(NUM_REPLICAS):
    node = request.RawPC("replica{}".format(i))
    iface = node.addInterface("if0")
    lan.addInterface(iface)

    setup_cmd = (
        "#!/bin/bash\n"
        "set -e\n"
        "sudo apt-get update\n"
        "sudo apt-get install -y golang-go git\n"
        "cd /local/repository\n"
        "go build -o pbft_server main.go\n"
        "./pbft_server replica{rid} &\n"
    ).format(rid=i)

    node.addService(rspec.Execute(shell="bash", command=setup_cmd))

pc.printRequestRSpec(request)
