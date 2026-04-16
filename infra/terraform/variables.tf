variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" {
  default = "us-ashburn-1"
}
variable "compartment_id" {}
variable "ssh_public_key_path" {
  description = "Path to your Public SSH Key"
  default     = "~/.ssh/id_rsa.pub"
}

variable "image_id" {
  description = "OCID for Ubuntu 22.04 ARM image (check for your region)"
}

variable "boot_volume_size_in_gbs" {
  description = "Size of the boot volume in GB (OCI Free Tier max is 200GB total)"
  default     = 200
}

variable "allowed_ports" {
  type    = list(number)
  default = [22, 80, 443, 3000, 3001, 5000, 8000, 8080, 8085, 8443]
}

variable "bucket_name" {
  description = "Name for the Object Storage bucket"
  default     = "viral-forge-assets"
}
