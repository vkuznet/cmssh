#!/usr/bin/env python
#-*- coding: ISO-8859-1 -*-
#pylint: disable-msg=E1101,C0103,R0902

# system modules
import os
import sys
import stat
import time
import thread
import traceback
from   types import GeneratorType

# ipython modules
import IPython
from   IPython import release

# cmssh modules
import cmssh
from   cmssh.iprint import PrintManager, print_error, print_warning, print_info
from   cmssh.debug import DebugManager
from   cmssh.cms_cmds import dbs_instance, Magic, cms_find, cms_du
from   cmssh.cms_cmds import cms_ls, cms_cp, verbose, cms_dqueue
from   cmssh.cms_cmds import cms_rm, cms_rmdir, cms_mkdir, cms_root, cms_xrdcp
from   cmssh.cms_cmds import cms_install, cms_releases, cms_info
from   cmssh.cms_cmds import cmsrel, cmsrun, cms_help, cms_arch, cms_vomsinit
from   cmssh.cms_cmds import cms_help_msg, results, cms_apt, cms_das, cms_das_json

class ShellName(object):
    def __init__(self):
        """Hold information about the shell"""
        self.prompt   = "cms-sh"
        self.name     = 'cmsHelp'
        self.dict     = {}
        self.funcList = []

def unregister():
    """Unregister shell"""
    ID.prompt         = "cms-sh"
    ID.name           = "cms-sh"
    ID.dict[ID.name]  = []
    ID.funcList       = []

def register(prompt, name, funcList=[]):
    """Register shell"""
    set_prompt(prompt)
    ID.prompt = prompt
    ID.name   = name
    funcList.sort()
    ID.dict[name] = funcList
    if  funcList:
        print_info("Available commands within %s sub-shell:" % prompt)
    if  funcList:
        if  not funcList.count('_exit'):
            funcList.append('_exit')
        for func in funcList:
            print_info("%s %s" % (" "*10, func))
            if  not ID.funcList.count(func):
                ID.funcList.append(func)
    else:
        ID.funcList = funcList

def set_prompt(in1):
    """Define shell prompt"""
    ip = get_ipython()
    prompt = '%s|\#> ' % in1
    ip.prompt_manager.width = len(prompt)-1
    ip.prompt_manager.in_template = prompt


#
# load managers
#
try:
    DEBUG    = DebugManager()
    ID       = ShellName()
except:
    traceback.print_exc()

# list of cms-sh magic functions
cmsMagicList = [ \
    # generic commands, we use Magic class and its execute function
    ('cvs', Magic('cvs').execute),
    ('svn', Magic('svn').execute),
    ('git', Magic('git').execute),
    ('echo', Magic('echo').execute),
    ('grep', Magic('grep').execute),
    ('tail', Magic('tail').execute),
    ('tar', Magic('tar').execute),
    ('zip', Magic('zip').execute),
    ('chmod', Magic('chmod').execute),
    ('vim', Magic('vim').execute),
    ('python', Magic('python').execute),
    ('env', Magic('env').execute),
    ('pip', Magic('pip').execute),
    # CMS commands
    ('crab', Magic('crab').execute),
    ('cmsenv', Magic('eval `scramv1 runtime -sh`').execute),
    ('scram', Magic('scramv1').execute),
    # grid middleware commands
#    ('gridinit', Magic('grid-proxy-init').execute),
#    ('gridinfo', Magic('grid-proxy-info').execute),
#    ('vomsinit', Magic('voms-proxy-init').execute),
    ('vomsinit', cms_vomsinit),
    ('vomsinfo', Magic('voms-proxy-info').execute),
    # specific commands whose execution depends on conditions
    ('das', cms_das),
    ('das_json', cms_das_json),
    ('apt', cms_apt),
    ('xrdcp', cms_xrdcp),
    ('root', cms_root),
    ('find', cms_find),
    ('du', cms_du),
    ('ls', cms_ls),
    ('info', cms_info),
    ('rm', cms_rm),
    ('mkdir', cms_mkdir),
    ('rmdir', cms_rmdir),
    ('cp', cms_cp),
    ('dqueue', cms_dqueue),
    ('verbose', verbose),
    ('install', cms_install),
    ('releases', cms_releases),
    ('dbs_instance', dbs_instance),
    ('cmsrel', cmsrel),
    ('cmsRun', cmsrun),
    ('cmsrun', cmsrun),
    ('cmshelp', cms_help),
    ('arch', cms_arch),
]

def check_0400(kfile):
    "Check 0400 permission of given file"
    mode = os.stat(kfile).st_mode
    cond = bool(mode & stat.S_IRUSR) and not bool(mode & stat.S_IWUSR) \
            and not bool(mode & stat.S_IXUSR) \
            and not bool(mode & stat.S_IRWXO) \
            and not bool(mode & stat.S_IRWXG)
    return cond

def check_0600(kfile):
    "Check 0600 permission of given file"
    mode = os.stat(kfile).st_mode
    cond = bool(mode & stat.S_IRUSR) and not bool(mode & stat.S_IXUSR) \
            and not bool(mode & stat.S_IRWXO) \
            and not bool(mode & stat.S_IRWXG)
    return cond

def test_key_cert():
    """Test user key/cert file and their permissions"""
    kfile = os.path.join(os.environ['HOME'], '.globus/userkey.pem')
    cfile = os.path.join(os.environ['HOME'], '.globus/usercert.pem')
    if  os.path.isfile(kfile):
        if  not (check_0600(kfile) or check_0400(kfile)):
            msg = "File %s has weak permission settings, try" % kfile
            print_warning(msg)
            print "chmod 0400 %s" % kfile
    else:
        print_error("File %s does not exists, grid/cp commands will not work" % kfile)
    if  os.path.isfile(cfile):
        if  not (check_0600(cfile) or check_0400(cfile)):
            msg = "File %s has weak permission settings, try" % cfile
            print_warning(msg)
            print "chmod 0600 %s" % cfile
    else:
        msg = "File %s does not exists, grid/cp commands will not work" % cfile
        print_error(msg)

#
# Main function
#
def main(ipython):
    """Define custom extentions"""

    # global IP API
    ip = ipython

    # load cms modules and expose them to the shell
    for m in cmsMagicList:
        magic_name = 'magic_%s' % m[0]
        setattr(ip, magic_name, m[1])

    # import required modules for the shell
    ip.ex("from cmssh.cms_cmds import results, cms_vomsinit")
    ip.ex("from cmssh.auth_utils import PEMMGR, read_pem")
    ip.ex("read_pem()")
    ip.ex("cms_vomsinit()")

    # Set cmssh prompt
    prompt = 'cms-sh'
#    ip.displayhook.prompt1.p_template = \
#        '\C_LightBlue[\C_LightCyan%s\C_LightBlue]|\#> ' % prompt
    ip.prompt_manager.in_template = '%s|\#> ' % prompt
    
    # define dbsh banner
    pyver  = sys.version.split('\n')[0]
    ipyver = release.version
    ver    = "%s.%s" % (cmssh.__version__, cmssh.__revision__)
    msg    = "Welcome to cmssh:\n[python %s, ipython %s]\n%s\n" \
            % (pyver, ipyver ,os.uname()[3])
    msg   += cms_help_msg()
    print msg

    # check existance and permission of key/cert 
    test_key_cert()

def load_ipython_extension(ipython):
    """Load custom extensions"""
    # The ``ipython`` argument is the currently active
    # :class:`InteractiveShell` instance that can be used in any way.
    # This allows you do to things like register new magics, plugins or
    # aliases.
    main(ipython)
