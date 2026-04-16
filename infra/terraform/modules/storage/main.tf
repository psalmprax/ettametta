terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
    }
  }
}

resource "oci_objectstorage_bucket" "this" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.this.namespace
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  
  versioning = "Enabled"
}

data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_id
}
