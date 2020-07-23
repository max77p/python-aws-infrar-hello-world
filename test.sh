#!/bin/bash
# sed -i '' '3 s/^/#/' nginx.conf
sed -i '' 's/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 128;/g' nginx.conf
sed -i    's/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 128;/g' /etc/nginx/nginx.conf