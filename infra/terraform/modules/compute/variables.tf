variable "compartment_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "instance_display_name" {
  type    = string
  default = "ettamettaServer"
}

variable "instance_shape" {
  type    = string
  default = "VM.Standard.A1.Flex"
}

variable "ocpus" {
  type    = number
  default = 4
}

variable "memory_in_gbs" {
  type    = number
  default = 24
}

variable "hostname_label" {
  type    = string
  default = "ettametta"
}

variable "ssh_public_key_path" {
  type    = string
}

variable "image_id" {
  type = string
}

variable "boot_volume_size_in_gbs" {
  type    = number
  default = 50
}
