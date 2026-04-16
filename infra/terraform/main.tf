terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

module "network" {
  source         = "./modules/network"
  compartment_id = var.compartment_id
  allowed_ports  = var.allowed_ports
}

module "compute" {
  source                  = "./modules/compute"
  compartment_id          = var.compartment_id
  subnet_id               = module.network.subnet_id
  ssh_public_key_path     = var.ssh_public_key_path
  image_id                = var.image_id
  boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  instance_display_name   = "ettamettaServer-v2"
}

module "storage" {
  source         = "./modules/storage"
  compartment_id = var.compartment_id
  bucket_name    = var.bucket_name
}
