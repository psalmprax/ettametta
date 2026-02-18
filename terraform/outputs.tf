output "viral_forge_ip" {
  value = module.compute.public_ip
}

output "bucket_name" {
  value = module.storage.bucket_name
}

output "available_ads" {
  value = module.compute.availability_domains
}
