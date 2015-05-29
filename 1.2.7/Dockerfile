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
#       --restart=on-failure --log-driver=syslog --net=host --privileged=true
#
# The following command line arguments are supported.
# usage: entry [-h] [--router-name [ROUTER_NAME]] [--master]
#              [--auth-pass [AUTH_PASS]] [--vrid [VRID]] [--exclude [EXCLUDE]]
#              [--check-interval [CHECK_INTERVAL]] [--check-rise [CHECK_RISE]]
#              [--check-fall [CHECK_FALL]] [--override-check [OVERRIDE_CHECK] |
#              --enable-check [ENABLE_CHECK]]
#              track_iface priority include [include ...]
# 
# positional arguments:
#   track_iface           The network interface this VRRP will broadcast
#                         multicast traffic over
#   priority              The priority this keepalived instance should run at in
#                         this VRRP.
#   include               The virtual IP(s) and iface(s) you will be using in
#                         the form 203.0.113.0/24/eth0
# 
# optional arguments:
#   -h, --help            show this help message and exit
#   --router-name [ROUTER_NAME], -n [ROUTER_NAME]
#                         The name you want to call this VRRP
#   --master, -m          Set if this keepalived should act as the master for
#                         this VRRP
#   --auth-pass [AUTH_PASS], -p [AUTH_PASS]
#                         This is the password this VRRP should use for
#                         authentication.
#   --vrid [VRID], -v [VRID]
#                         This is the Virtual Router ID this VRRP should use.
#   --exclude [EXCLUDE], -x [EXCLUDE]
#                         Any virtual IP(s) and iface(s) you want to be excluded
#                         in the form 203.0.113.0/24/eth0
#   --check-interval [CHECK_INTERVAL], -i [CHECK_INTERVAL]
#                         The interval the check script should repeat, (default
#                         2)
#   --check-rise [CHECK_RISE], -r [CHECK_RISE]
#                         The amount of sucessful checks required to restore a
#                         fault, (default 2)
#   --check-fall [CHECK_FALL], -f [CHECK_FALL]
#                         The amount of failed checks required to fault,
#                         (default 2)
#   --override-check [OVERRIDE_CHECK], -o [OVERRIDE_CHECK]
#                         This is where you can provide a custom script to this
#                         container to check if this instance should be demoted.
#                         It looks for scripts in the folder /ka-data/scripts/.
#                         The script should not take any arguments.
#   --enable-check [ENABLE_CHECK], -e [ENABLE_CHECK]
#                         This enables the default checking script which will
#                         demote this instance if it cannot get a 200 return
#                         code from the given URL.

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