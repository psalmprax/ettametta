terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
    }
  }
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  
  filter {
    name   = "display_name"
    values = [length(regexall("A1", var.instance_shape)) > 0 ? "^Canonical-Ubuntu-22.04-aarch64-([\\.0-9-]+)$" : "^Canonical-Ubuntu-22.04-([\\.0-9-]+)$"]
    regex  = true
  }
}

resource "oci_core_instance" "this" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  display_name        = var.instance_display_name
  shape               = var.instance_shape
  subnet_id           = var.subnet_id

  dynamic "shape_config" {
    for_each = length(regexall("Flex", var.instance_shape)) > 0 ? [1] : []
    content {
      memory_in_gbs = var.memory_in_gbs
      ocpus         = var.ocpus
    }
  }

  create_vnic_details {
    display_name     = "${var.instance_display_name}-vnic"
    assign_public_ip = true
    hostname_label   = var.hostname_label
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode(<<-EOF
      #!/bin/bash
      apt-get update
      apt-get install -y docker.io docker-compose git
      systemctl enable --now docker
      usermod -aG docker ubuntu
    EOF
    )
  }

  preserve_boot_volume = false

  lifecycle {
    ignore_changes = [
      source_details[0].boot_volume_size_in_gbs
    ]
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}
