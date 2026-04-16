output "bucket_name" {
  value = oci_objectstorage_bucket.this.name
}

output "bucket_id" {
  value = oci_objectstorage_bucket.this.bucket_id
}
