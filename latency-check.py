#!/usr/local/bin/python3

"""
This script uses the Nornir framework to 

collect discovery information from 
Cisco network devices and save the output to file. Devices and parameters are 
provided by the SimpleInventory plugin for Nornir using YAML files. 
"""

import sys
from getpass import getpass
from datetime import datetime
from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.tasks import text, files
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import napalm_ping
from pprint import pprint as pp

# print formatting function
def c_print(printme):
    # Print centered text with newline before and after
    print(f"\n" + printme.center(80, " ") + "\n")


# Nornir kickoff
def kickoff():
    # print banner
    print()
    print("~" * 80)

    c_print(f"This script will test latency from various Cisco devices")

    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c_print(f"Timestamp: {time_stamp}")

    if len(sys.argv) < 2:
        site = ""

    else:
        site = sys.argv[1] + "_"

    # initialize The Norn
    nr = InitNornir(
        inventory={
            "plugin": "nornir.plugins.inventory.simple.SimpleInventory",
            "options": {
                "host_file": f"inventory/{site}hosts.yaml",
                "group_file": f"inventory/{site}groups.yaml",
                "defaults_file": "inventory/defaults.yaml",
            },
        }
    )

    # filter The Norn
    # nr = nr.filter(platform="ios")

    c_print(f"Destination: {nr.inventory.defaults.data['dest']}")

    devices = ""
    for dev in nr.inventory.hosts.keys():
        if devices != "":
            devices += ", "

        devices += f"{dev}"

    c_print(f"Devices: {devices}")

    c_print("Checking inventory for credentials")
    # check for existing credentials in inventory

    if nr.inventory.defaults.username == None or nr.inventory.defaults.password == None:
        c_print("Please enter device credentials:")

    if nr.inventory.defaults.username == None:
        nr.inventory.defaults.username = input("Username: ")

    if nr.inventory.defaults.password == None:
        nr.inventory.defaults.password = getpass()
        print()

    print("~" * 80)

    return nr


# Nornir task for latency check
def check_latency(task):
    """
    This function uses the NAPALM ping module to test latency to a specified destination
    """
    c_print(f"**** {task.host}: BEGIN TESTING ****")

    output = task.run(task=napalm_ping, dest=task.host["dest"], size=1500, count=100)

    if "success" in output.result.keys():
        c_print(f"**** {task.host}: TESTING SUCCESS ****")
        task.host['output'] = output.result['success']
    else:
        c_print(f"**** {task.host}: TESTING ERROR ****")
        print(output.result)


def report_latency(task):

    loss = task.host['output']["packet_loss"]
    sent = task.host['output']["probes_sent"]
    rtt_avg = task.host['output']["rtt_avg"]

    loss_pct = loss / sent

    c_print(f"**** {task.host}: RESULTS ****")

    c_print(f"**** {loss_pct}% of {sent} pings failed ****")

    c_print(f"**** Average latency: {rtt_avg} ms ****")

    print("~" * 80)


def main():
    # kickoff The Norn
    nr = kickoff()
    # run The Norn
    nr.run(task=check_latency)
    print("~" * 80)
    nr.run(task=report_latency, num_workers=1)
    c_print(f"Failed hosts: {nr.data.failed_hosts}")
    print("~" * 80)


if __name__ == "__main__":
    main()
