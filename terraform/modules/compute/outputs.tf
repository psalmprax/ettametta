output "public_ip" {
  value = oci_core_instance.this.public_ip
}

output "availability_domains" {
  value = data.oci_identity_availability_domains.ads.availability_domains
}

output "instance_id" {
  value = oci_core_instance.this.id
}
