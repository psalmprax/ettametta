terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
    }
  }
}

resource "oci_core_vcn" "this" {
  cidr_block      = var.vcn_cidr
  compartment_id  = var.compartment_id
  display_name    = var.vcn_display_name
  dns_label       = var.vcn_dns_label
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  display_name   = "${var.vcn_display_name}-IG"
  vcn_id         = oci_core_vcn.this.id
}

resource "oci_core_route_table" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "${var.vcn_display_name}-RT"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_subnet" "this" {
  cidr_block        = var.subnet_cidr
  display_name      = var.subnet_display_name
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.this.id
  route_table_id    = oci_core_route_table.this.id
  security_list_ids = [oci_core_security_list.this.id]
  dns_label         = var.subnet_dns_label
}
