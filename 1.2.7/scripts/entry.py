#!/usr/bin/env python
# This script processes the command line arguments and then start keepalived. It also checks if the container is running
# in the correct network mode.

########################################################################################################################
# LIBRARY IMPORT                                                                                                       #
########################################################################################################################
# Import required libaries
import sys,os,pwd,grp   # OS Libraries
import argparse         # Parse Arguments
from subprocess import Popen, PIPE, STDOUT
                        # Open up a process
import atexit

# Important required templating libarires
from jinja2 import Environment as TemplateEnvironment, \
                   FileSystemLoader, Template
                        # Import the jinja2 libaries required by this script
from jinja2.exceptions import TemplateNotFound
                        # Import any exceptions that are caught by the Templates section
                        
# Specific to the script
from IPy import IP      # Library to verify if a given IP address is valid
import netifaces
from socket import gethostname as hostname
from threading import Thread
import stat
import urlparse         # Allows you to check the validity of a URL
import requests         # Allows you to perform requests (like curl)
                        
# Varaibles/Consts
scripts_path = '/ka-data/scripts/'

# Define the cleanup function
def cleanup(child):
    # Warning: This function can be registered more than once, code defensively!
    if child is not None: # Make sure the child actually exists
        child.terminate() # Terminate the child cleanly
        for line in iter(child.stdout.readline, ''): # Clear the buffer of any lines remaining
            sys.stdout.write(line)

# User defined exception
class SubprocessTimeoutError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# Functions
def vip_check(vips,check_str,exclude):
    """Check the `check_str` to see if it is valid, and import it into `vips`."""
    check = check_str.split('/')
    if len(check) != 3:
        print "The argument %s provided does not have 3 '/' delimited arguments, terminating" % check_str
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
    try:
        check_ip = IP(check[0])
    except ValueError as e:
        print "The IP %s does not appear to be a valid (returned %s), terminating..." % (check[0], e)
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
        
    #TODO: Check subnet length    
    if check[2] not in netifaces.interfaces():
        print "The iface %s does not appear to be a valid interface on this host, terminating..." % check[2]
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.
    
    vip_obj = { 'addr'    : check_ip.strNormal(0),      # Print string without a mask
                'mask'    : check[1],                   # Prefix length
                'iface'   : check[2],                   # Interface 
                'include' : bool(not exclude),
              }
    vips.append(vip_obj)
    
def run_command_with_timeout(cmd, timeout_sec):
    """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.
 
    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""
    proc = Popen(cmd)
    proc_thread = Thread(target=proc.communicate)
    proc_thread.start()
    proc_thread.join(timeout_sec)
    if proc_thread.is_alive():
        # Process still running - kill it and raise timeout error
        try:
            proc.kill()
        except OSError, e:
            # The process finished between the `is_alive()` and `kill()`
            return proc.returncode
        # OK, the process was definitely killed
        raise SubprocessTimeoutError('Process #%d killed after %f seconds' % (proc.pid, timeout_sec))
    # Process completed naturally - return exit code
    return proc.returncode

# Register atexit
atexit.register(cleanup,None)
    
########################################################################################################################
# ARGUMENT PARSER                                                                                                      #
# This is where you put the Argument Parser lines                                                                      #
########################################################################################################################
argparser = argparse.ArgumentParser(description='Run a docker container containing a keepalived Instance')

argparser.add_argument('--router-name','-n',
                       action='store',
                       nargs='?',
                       help='The name you want to call this VRRP',
                       default=hostname())
argparser.add_argument('--master','-m',
                       action='store_true',
                       help='Set if this keepalived should act as the master for this VRRP')
argparser.add_argument('--auth-pass','-p',
                       action='store',
                       nargs='?',
                       help='This is the password this VRRP should use for authentication.')
argparser.add_argument('--vrid','-v',
                       action='store',
                       type=int,
                       nargs='?',
                       help='This is the Virtual Router ID this VRRP should use.')
argparser.add_argument('--exclude','-x',
                       action='append',
                       nargs='?',
                       help='Any virtual IP(s) and iface(s) you want to be excluded in the form 203.0.113.0/24/eth0')
argparser.add_argument('--check-interval','-i',
                       action='store',
                       nargs='?',
                       type=int,
                       default=2,
                       help='The interval the check script should repeat, (default 2)')
argparser.add_argument('--check-rise','-r',
                       action='store',
                       nargs='?',
                       type=int,
                       default=2,
                       help='The amount of sucessful checks required to restore a fault, (default 2)')
argparser.add_argument('--check-fall','-f',
                       action='store',
                       nargs='?',
                       type=int,
                       default=2,
                       help='The amount of failed checks required to fault, (default 2)')
argparser.add_argument('track_iface',
                       action='store',
                       help='The network interface this VRRP will broadcast multicast traffic over')
argparser.add_argument('priority',
                       action='store',
                       type=int,
                       help='The priority this keepalived instance should run at in this VRRP.')
argparser.add_argument('include',
                       action='store',
                       nargs='+',
                       help='The virtual IP(s) and iface(s) you will be using  in the form 203.0.113.0/24/eth0')

argparser_check_script = argparser.add_mutually_exclusive_group()
helptext = 'This is where you can provide a custom script to this container to check if this instance should be' 
helptext += ' demoted. It looks for scripts in the folder %s. The script should not take any arguments.' % scripts_path
argparser_check_script.add_argument('--override-check','-o',
                       action='store',
                       nargs='?',
                       help=helptext)
helptext = 'This enables the default checking script which will demote this instance if it cannot get a 200'
helptext += ' return code from the given URL.'
argparser_check_script.add_argument('--enable-check','-e',
                       action='store',
                       nargs='?',
                       help=helptext)

try:
    args = argparser.parse_args()
except SystemExit:
    pass
    sys.exit(0) # This should be a return 0 to prevent the container from restarting
    
########################################################################################################################
# ARGUMENT VERIRIFCATION                                                                                               #
# This is where you put any logic to verify the arguments, and failure messages                                        #
########################################################################################################################
auth_pass = args.auth_pass
if auth_pass is None:
    print 'WARNING: Using this container without a set auth pass will make this container insecure.'
    auth_pass = '12345678'

vrid  = args.vrid
if vrid is None:
    print 'WARNING: Not setting a vrid could result in a conflict. Please specify a vrid to avoid possible conflicts'
    vrid = 1
    
# Check if the track_iface is a valid iface
if args.track_iface not in netifaces.interfaces():
    print "The iface %s does not appear to be a valid interface on this host, terminating..." % args.track_iface
    sys.exit(0) # This should be a return 0 to prevent the container from restarting.

vips = []
# Check and import the included VIPs
for vip in args.include:
    vip_check(vips,vip,False)
    
# Check and import the excluded VIPs:
if args.exclude is not None:
    for vip in args.exclude:
        vip_check(vips,vip,True)

# Check that they're exclusvely active
check_script_enabled = False
if args.override_check is not None or args.enable_check is not None:
    # At least one is active
    check_script_enabled = True
    # We should check that both are not enabled
    if args.override_check is not None and args.enable_check is not None:
        errormsg = "Both --override-check and --enable-check are enabled. This should never get here as the argparser"
        errormsg += " library should catch this errorcase"
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.        

# Check the override check script
if args.override_check is not None:
    if not os.path.isfile(scripts_path + args.override_check):
        print "The provided file %s for the override_check is not a file, terminating..." % args.override_check
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.        
    # Add execute permissions to the override check script
    try:
        current_mask = stat.S_IMODE(os.stat(scripts_path + args.override_check).st_mode)
        os.chmod(scripts_path + args.override_check, current_mask | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH )
        # Equivelent to chmod +x
    except OSError as e:
        errormsg = "The file %s could not be chmoded" % (scripts_path + args.override_check)
        errormsg += "  (returned %s), terminating..." %  e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting
    # Attempt to execute it
    timeout = 30 # Give it 30 seconds to attempt to check script
    try:
        run_command_with_timeout([scripts_path + args.override_check],timeout)
    except SubprocessTimeoutError as e:
        print "Command %s did not finish in %d seconds, terminating..." % timeout, (scripts_path + args.override_check)
        sys.exit(0) # This should be a return 0 to prevent the container from restarting
   
# Check the default script is working
check_url_parsed = None # Set default
if args.enable_check is not None:
    pass # TODO: After Haproxy container has been written update this script to verify the URL & write the check script

# Setup the check script variables
check_script = { 'enabled'  : check_script_enabled,
                 'path'     : scripts_path + args.override_check if args.override_check is not None else None,
                 'interval' : args.check_interval, # int
                 'rise'     : args.check_rise, # int
                 'fall'     : args.check_fall, # int
                 'url'      : urlparse.urlunparse(check_url_parsed) if check_url_parsed is not None else None,
               }
use_check_script = bool((args.enable_check is not None) or (args.override_check is not None))
########################################################################################################################
# TEMPLATES                                                                                                            #
# This is where you manage any templates                                                                               #
########################################################################################################################
# Configuration Location goes here
template_location = '/ka-templates'

# Create the template list
template_list = {}

# Templates go here
### 00-ls-input.conf ###
template_name = 'keepalived.conf'
template_dict = { 'context' : { # Subsitutions to be performed
                                'router_name'         : args.router_name,
                                'track_iface'         : args.track_iface,
                                'is_master'           : args.master,
                                'auth_pass'           : auth_pass,
                                'virtual_router_id'   : int(vrid),
                                'priority'            : int(args.priority),
                                'check_script'        : check_script, 
                                'virtual_ipaddresses' : vips,
                                'virtual_routes'      : None, # This script currently doesn't handle routes yet
                                                              # This is partially due to being complicated to
                                                              # implement and the current lack of IPv6 support in
                                                              # the version of keepalived this container has been
                                                              # built to use
                              },
                  'path'    : '/etc/keepalived/keepalived.conf',
                  'user'    : 'root',
                  'group'   : 'root',
                  'mode'    : 0644 }
template_list[template_name] = template_dict

# Load in the files from the folder
template_loader = FileSystemLoader(template_location)
template_env = TemplateEnvironment(loader=template_loader,
                                   lstrip_blocks=True,
                                   trim_blocks=True,
                                   keep_trailing_newline=True)

# Load in expected templates
for template_item in template_list:
    # Attempt to load the template
    try:
        template_list[template_item]['template'] = template_env.get_template(template_item)
    except TemplateNotFound as e:
        errormsg = "The template file %s was not found in %s (returned %s)," % (template_item, template_location, e)
        errormsg += " terminating..."
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    # Attempt to open the file for writing
    try:
        template_list[template_item]['file'] = open(template_list[template_item]['path'],'w')
    except IOError as e:
        errormsg = "The file %s could not be opened for writing for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restart
    
    # Stream
    try:
        template_list[template_item]['render'] = template_list[template_item]['template'].\
                                             render(template_list[template_item]['context'])
    
        # Submit to file
        template_list[template_item]['file'].write(template_list[template_item]['render'].encode('utf8'))
        template_list[template_item]['file'].close()
    except:
        e = sys.exc_info()[0]
        print "Unrecognised exception occured, was unable to create template (returned %s), terminating..." % e
        sys.exit(0) # This should be a return 0 to prevent the container from restarting.


    # Change owner and group
    try:
        template_list[template_item]['uid'] = pwd.getpwnam(template_list[template_item]['user']).pw_uid
    except KeyError as e:
        errormsg = "The user %s does not exist for template %s" % template_list[template_item]['user'], template_item
        errormsg += "(returned %s), terminating..." % e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    try:
        template_list[template_item]['gid'] = grp.getgrnam(template_list[template_item]['group']).gr_gid
    except KeyError as e:
        errormsg = "The group %s does not exist for template %s" % template_list[template_item]['group'], template_item
        errormsg += "(returned %s), terminating..." % e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    try:
        os.chown(template_list[template_item]['path'],
                 template_list[template_item]['uid'],
                 template_list[template_item]['gid'])
    except OSError as e:
        errormsg = "The file %s could not be chowned for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

    # Change premisions
    try:
        os.chmod(template_list[template_item]['path'],
                 template_list[template_item]['mode'])
    except OSError as e:
        errormsg = "The file %s could not be chmoded for template" % template_list[template_item]['path']
        errormsg += " %s (returned %s), terminating..." % template_item, e
        print errormsg
        sys.exit(0) # This should be a return 0 to prevent the container from restarting

########################################################################################################################
# SPAWN CHILD                                                                                                          #
########################################################################################################################
# Flush anything on the buffer
sys.stdout.flush()


# Spawn the child
#child_path = ["cat","/etc/keepalived/keepalived.conf"]
child_path = ["/usr/sbin/keepalived","--dont-fork","--log-console"]
child = Popen(child_path, stdout = PIPE, stderr = STDOUT, shell = False)

# Register the atexit terminaton
atexit.register(cleanup, child)

# Reopen stdout as unbuffered. This will mean log messages will appear as soon as they become avaliable.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


# Output any log items to Docker
for line in iter(child.stdout.readline, ''):
    sys.stdout.write(line)

# If the process terminates, read its errorcode and return it
sys.exit(child.returncode)