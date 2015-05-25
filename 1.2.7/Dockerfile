# Keepalived Dockerfile
# Solnet Solutions
# Version: 1.2.7 (1:1.2.7-1ubuntu1)

# Pull base image (Ubuntu 14.04)
FROM ubuntu:14.04

# Build Instructions
# When building use the following flags:
#       --tag="keepalived:1.2.7

# Run Instructions:
# When running use the following flags:
#       --restart=on-failure --log-driver=syslog --net=host --privleged=true
# The following command line arguments are supported.
# == Output of --help here ==

# NOTICE: You may need to enable multicast through the filewall to allow keepalived to work:
# iptables -I INPUT -d 224.0.0.0/8 -j ACCEPT
# iptables -I INPUT -p vrrp -j ACCEPT

# Information
MAINTAINER Taylor Bertie <taylor.bertie@solnet.co.nz>
LABEL Description="This image is used to stand up a keepalived daemon that will keep a VIP active between multiple \
nodes. This container must run in privleged mode with host networking in order to operate. Provide VIPs via \
'203.0.113.0/24/eth0'" Version="1.2.7"

# Patch notes:
# Version 1.2.7
#       - First working version of keepalived
#       - Current version does not handle routes

# Set the keepalived version to be pinned
ENV KA_PKG_VRS 1:1.2.7-1ubuntu1

# Install any required packages
RUN \
    apt-get update && \
    apt-get install python python-jinja2 python-ipy python-netifaces python-requests keepalived=$KA_PKG_VRS -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Prepare various directories in /ka-data/
RUN \
    mkdir -p /ka-data/ && \
    mkdir -p /ka-data/scripts && \
    mkdir -p /ka-templates
    
# Mount the configuration files, entry script and templates
# Templates
ADD templates/keepalived.conf /ka-templates/keepalived.conf

# Configuration Files
ADD scripts/check_haproxy.py /usr/local/bin/check_haproxy
RUN chmod +x /usr/local/bin/check_haproxy

# Entry Script
ADD scripts/entry.py /usr/local/bin/entry
RUN chmod +x /usr/local/bin/entry

# Define working directory
WORKDIR /ka-data

# Define the default command as an entrypoint
ENTRYPOINT ["/usr/local/bin/entry"]

# Expose ports
# None (as it is using host interfaces it will not need any ports exposed)