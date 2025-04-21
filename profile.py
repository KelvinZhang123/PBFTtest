import geni.portal as portal
import geni.rspec.pg as rspec

# ----------------------------------------------------------------------------
# CloudLab Profile for deploying bigpicturelabs/simple_pbft replicas
# ----------------------------------------------------------------------------

# Number of PBFT replicas (3f+1; here f=1 -> 4 replicas for basic BFT)
NUM_REPLICAS = 4

# 1. Initialize GENI portal context and RSpec
pc = portal.Context()
request = rspec.Request()

# 2. Create a LAN for inter-node communication
lan = request.LAN('lan0')
lan.best_effort = False

# 3. Allocate replicas
for i in range(NUM_REPLICAS):
    node = request.RawPC(f'replica{i}')
    iface = node.addInterface('if0')
    lan.addInterface(iface)

    # 4. Bootstrap each node: install Go, clone repo, build, configure, and run server
    node.addService(rspec.Execute(
        shell='bash',
        command=f"""
          #!/bin/bash
          # Install prerequisites
          sudo apt-get update && \
          sudo apt-get install -y golang-go git && \

          # Clone and build simple_pbft
          git clone https://github.com/bigpicturelabs/simple_pbft.git && \
          cd simple_pbft && \
          go build -o server ./cmd/server && \

          # Generate config file
          mkdir -p config && \
          ip=$(hostname -I | awk '{{print $1}}') && \
          cat > config/config.yaml <<EOF
node:
  id: "replica{i}"
  address: "${{ip}}:800{i+1}"
network:
  port: {8000 + i}
EOF

          # Run the PBFT server
          ./server --config config/config.yaml &
        """
    ))

# 5. Output the RSpec
portal.Context().printRequestRSpec(request)
