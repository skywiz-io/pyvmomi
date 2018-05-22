#!/usr/bin/env python


from __future__ import print_function

import sys
sys.path.insert(0, "/home/danco/workspace/pyvmomi")

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

import argparse
import atexit
import getpass
import ssl
import json

folder = "Dan"

def GetArgs():
   """
   Supports the command-line arguments listed below.
   """
   parser = argparse.ArgumentParser(
       description='Process args for retrieving all the Virtual Machines')
   parser.add_argument('-s', '--host', required=True, action='store',
                       help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store',
                       help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store',
                       help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store',
                       help='Password to use when connecting to host')
#   parser.add_argument('-f', '--folder', required=True, action='store',
#                       help='Target folder to display') 
   args = parser.parse_args()
   return args


out = {}
out['group'] = { 'hosts' : [], 'vars' : {'ansible_ssh_user': 'vagrant','ansible_ssh_private_key_file':'~/.vagrant.d/insecure_private_key','example_variable': 'value'}}


hostvars = {}
 

def PrintVmInfo(folder, depth=1):
   """
   Print information for a particular virtual machine or recurse into a folder
   or vApp with depth protection
   """


 
   vmList = folder.childEntity
   for item in vmList:
      if not hasattr(item,'childEntity'):
             summary = item.summary

             if summary.guest != None:
                 ip = summary.guest.ipAddress
                 if ip != None and ip != "":
                     vmName = summary.guest.ipAddress
                     out['group']['hosts'].append(vmName)
                 else:
                     vmName = "N/A"

             hostvars[vmName] = {}
             varObj = {}
             varObj['name'] = summary.config.name
             varObj['path'] = summary.config.vmPathName
             varObj['guestFullName'] = summary.config.guestFullName
             annotation = summary.config.annotation
             if annotation != None and annotation != "":
                varObj['annotation'] = summary.config.annotation

             varObj['state'] = summary.runtime.powerState
             if summary.guest != None:
                 ip = summary.guest.ipAddress
                 if ip != None and ip != "":
                     varObj['ip'] = summary.guest.ipAddress
   
             hostvars[vmName] = varObj
      else:
             PrintVmInfo(item)
   
  

def SearchFolder(currFolder, targetFolder):
   if currFolder.name == targetFolder:
        PrintVmInfo(currFolder)
        return 0
   children = currFolder.childEntity
   for child in children:
       if hasattr(child, 'childEntity'):
          SearchFolder(child, targetFolder)


def main():
   """
   Simple command-line program for listing the virtual machines on a system.
   """

   args = GetArgs()
   if args.password:
      password = args.password
   else:
      password = getpass.getpass(prompt='Enter password for host %s and '
                                        'user %s: ' % (args.host,args.user))

   context = None
   if hasattr(ssl, '_create_unverified_context'):
      context = ssl._create_unverified_context()
   si = SmartConnect(host=args.host,
                     user=args.user,
                     pwd=password,
                     port=int(args.port),
                     sslContext=context)
   if not si:
       print("Could not connect to the specified host using specified "
             "username and password")
       return -1

   atexit.register(Disconnect, si)

   content = si.RetrieveContent()
   for child in content.rootFolder.childEntity:
      if hasattr(child, 'vmFolder'):
         datacenter = child
         vmFolder = datacenter.vmFolder
         itemList = vmFolder.childEntity
         for item in itemList:
               if hasattr(item, 'childEntity'):
                   SearchFolder(item,folder)


   out['_meta'] = { 'hostvars' : hostvars }

   print(json.dumps(out,sort_keys=True, indent=4))
   print("")
   return 0

# Start program
if __name__ == "__main__":
   main()
