variable "compartment_id" {
  type = string
}

variable "vcn_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "vcn_display_name" {
  type    = string
  default = "ViralForgeVCN"
}

variable "vcn_dns_label" {
  type    = string
  default = "vfvcn"
}

variable "subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "subnet_display_name" {
  type    = string
  default = "ViralForgeSubnet"
}

variable "subnet_dns_label" {
  type    = string
  default = "vfsubnet"
}

variable "allowed_ports" {
  type    = list(number)
  default = [80, 443, 8000, 3000, 8080, 8081]
}
