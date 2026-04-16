resource "oci_core_security_list" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "${var.vcn_display_name}-SL"

  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
    destination_type = "CIDR_BLOCK"
  }

  # SSH
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Web/API Ports
  dynamic "ingress_security_rules" {
    for_each = var.allowed_ports
    content {
      protocol    = "6"
      source      = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"
      tcp_options {
        min = ingress_security_rules.value
        max = ingress_security_rules.value
      }
    }
  }
}
