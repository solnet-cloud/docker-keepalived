# docker-keepalived

    Please note the following for this build:
    
    - I will be providing a script that provides the --enable-check functionality but due to time constraints this has not been implemented just yet. Please do not use the --enable-check flag until this has been fixed.
    
Keepalived is a routing software designed to provide simple and robust facilities for loadbalancing and high-availability to Linux system and Linux based infrastructures. This container providers a mechanism to provide a highly avaliable IP address via the VRRP protocol. VRRP is a fundamental brick for router failover.

More details on the Keepalived can be found at the project's website at http://keepalived.org/

This Docker build builds on top of a Ubuntu image to provide a working Keepalived instance that can be paired with multiple similar containers to distribute a VIP.

Under the most basic usage you will provide an interface for multicast, a priority, and at least one address that is included in the VRRP broadcasts. This container must run with the host networking and in privileged mode. It is also recommend you redirect logs to syslog (requires Docker 1.6) and use restart on-failure.

    docker run -d --restart=on-failure --log-driver=syslog --net=host --privileged=true solnetcloud/keepalived:latest --master eth0 100 203.0.113.0/24/eth0
    
It is important to have a basic understanding of the VRRP protocol, and the difference between master and slave nodes as well as the priority. You will likely not execute two instances with the same priority and master/slave state.

It is also strongly recommened you explictly state the VRID using the --vrid tag, as well as a custom auth pass using --auth-pass.

NOTICE: You may need to enable multicast through the filewall to allow keepalived to work:
    iptables -I INPUT -d 224.0.0.0/8 -j ACCEPT
    iptables -I INPUT -p vrrp -j ACCEPT

    usage: entry [-h] [--router-name [ROUTER_NAME]] [--master]
                 [--auth-pass [AUTH_PASS]] [--vrid [VRID]] [--exclude [EXCLUDE]]
                 [--check-interval [CHECK_INTERVAL]] [--check-rise [CHECK_RISE]]
                 [--check-fall [CHECK_FALL]] [--override-check [OVERRIDE_CHECK] |
                 --enable-check [ENABLE_CHECK]]
                 track_iface priority include [include ...]
    
    positional arguments:
      track_iface           The network interface this VRRP will broadcast
                            multicast traffic over
      priority              The priority this keepalived instance should run at in
                            this VRRP.
      include               The virtual IP(s) and iface(s) you will be using in
                            the form 203.0.113.0/24/eth0
    
    optional arguments:
      -h, --help            show this help message and exit
      --router-name [ROUTER_NAME], -n [ROUTER_NAME]
                            The name you want to call this VRRP
      --master, -m          Set if this keepalived should act as the master for
                            this VRRP
      --auth-pass [AUTH_PASS], -p [AUTH_PASS]
                            This is the password this VRRP should use for
                            authentication.
      --vrid [VRID], -v [VRID]
                            This is the Virtual Router ID this VRRP should use.
      --exclude [EXCLUDE], -x [EXCLUDE]
                            Any virtual IP(s) and iface(s) you want to be excluded
                            in the form 203.0.113.0/24/eth0
      --check-interval [CHECK_INTERVAL], -i [CHECK_INTERVAL]
                            The interval the check script should repeat, (default
                            2)
      --check-rise [CHECK_RISE], -r [CHECK_RISE]
                            The amount of sucessful checks required to restore a
                            fault, (default 2)
      --check-fall [CHECK_FALL], -f [CHECK_FALL]
                            The amount of failed checks required to fault,
                            (default 2)
      --override-check [OVERRIDE_CHECK], -o [OVERRIDE_CHECK]
                            This is where you can provide a custom script to this
                            container to check if this instance should be demoted.
                            It looks for scripts in the folder /ka-data/scripts/.
                            The script should not take any arguments.
      --enable-check [ENABLE_CHECK], -e [ENABLE_CHECK]
                            This enables the default checking script which will
                            demote this instance if it cannot get a 200 return
                            code from the given URL.