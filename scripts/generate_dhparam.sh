#!/bin/bash
# Generate DH parameters for nginx (this takes a while)
openssl dhparam -out nginx/dhparam.pem 2048
