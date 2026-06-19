# Consul Configuration for ettametta

datacenter = "dc1"
data_dir = "/consul/data"
log_level = "INFO"
node_name = "consul-server-1"

# Server mode
server = true
bootstrap_expect = 1

# UI
ui_config {
  enabled = true
}

# Networking
bind_addr = "0.0.0.0"
client_addr = "0.0.0.0"
advertise_addr = "{{ GetInterfaceIP \"eth0\" }}"

# Ports
ports {
  http = 8500
  https = 8501
  grpc = 8502
  dns = 8600
}

# DNS
recursors = ["8.8.8.8", "8.8.4.4"]

# Health checks
checks = [
  {
    id = "consul-alive",
    name = "Consul Server Alive",
    http = "http://localhost:8500/v1/status/leader",
    interval = "10s",
    timeout = "3s"
  }
]

# ACL
acl {
  enabled = false
  default_policy = "allow"
  enable_token_persistence = true
}

# Encryption
encrypt = ""

# Performance
performance {
  raft_multiplier = 1
}

# Connect (service mesh)
connect {
  enabled = true
}
