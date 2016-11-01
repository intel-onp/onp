
Intel ONP
============================================

Experimental repository for Intel ONP.

Intel ONP scripts provide a simplified mechanism for installing and configuring OpenStack on Intel Architecture using Kolla.

Preparing Kolla bare-metal nodes using Ansible
============================================

Ansible is a configuration management utility.  It runs on a system separate from the Kolla nodes to configure networking, drivers and handle system reboots.

Instructions in this readme have been tested with Ansible version 2.1.0.0.

1. Install Ansible 2.1.0.0 on a deployment system (VM or physical) separate from ones to be used for Kolla deployment.

2. Have multiple systems with fresh installations of chosen OS standing by.

3. On the deployment system, create a file in the Ansible directory called ``inventory.ini``.  This file holds information regarding which system(s) are control and which are compute.
   Group vars are used to specify login credentials.  Alternatively, a pre-shared ssh key can be used.  See examples below.

    Inventory hostnames MUST MATCH EXACTLY what is provided by DHCP or DNS.  Ansible does not support case-insentive hostnames.  RabbitMQ does not support full path hostnames.

        [control]
        # Only use 'ansible_host' here to set IP if DNS is not configured
        # The hostname must match the hostname in the ``node_info`` section in onps_config.yml (details in subsequent section of this readme)
        # This hostname will be set on the node
        control-1.example.com  ansible_host=1.2.3.a

        [compute]
        compute-1.example.com  ansible_host=1.2.3.c
        # Optionally, per node passwords are supported
        compute-2.example.com  ansible_host=1.2.3.d ansible_ssh_pass=something_different

        [network]
        # Optionally, when external network mode is desired
        network-1.example.com ansible_host=1.2.3.e

        [control:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

        [compute:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

        # Or, use the global group 'all' (or -k to provide a password on the command line)
        [all:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

    Only one method of supplying login credentials should be chosen.
    See also http://docs.ansible.com/ansible/intro_inventory.html
    A skeleton of the inventory file can be found in ansible/examples directory.

4. Use Ansible to probe systems and gather facts about network topology for Kolla systems.

        ansible -i inventory.ini -m setup all  > all_system_facts.txt

    Examine all_system_facts.txt to get all current network topology details.
    e.g.


        "ansible_interfaces": [
            "ens785f0",
            "lo",
            "ens785f2",
            "ens785f3",
            "ens513f1",
            "ens513f0",
            "mgmt",
            "virtual-1",
            "inter",
            "virbr0-nic",
            "virbr0"
        ],
        "ansible_ens513f1": {
            "active": false,
            "device": "ens513f1",
            "macaddress": "00:1e:67:e2:6f:25",
            "module": "ixgbe",
            "mtu": 1500,
            "promisc": false,
            "type": "ether"
        },
        "ansible_ens785f0": {
            "active": false,
            "device": "ens785f0",
            "macaddress": "68:05:ca:37:dc:68",
            "module": "i40e",
            "mtu": 1500,
            "promisc": false,
            "type": "ether"
        },

5. Copy the examples/onps_config.yml file to ansible directory and edit it.
    - Define ovs_type, tenant_network_type and use_odl.  Other configuration options can be left at default values.
      Info regarding available options are outlined as comments in onps_config.yml.
    - Using info in all_system_facts.txt, set interface names for mgmt (management), inter (internet), public and tenant networks.
    - Define static IPs for interfaces that need them (tunnel_ip and mgmt ip_address typically) in ``node_info`` section.
      Since we configure all nodes in parallel, every node has to know the full topology and IP address of every other node.
    - Optionally, speed up pip by using a local pip cache mirror.

        pip_mirror_url: http://local-pip-mirror.example.com:4040/root/pypi/+simple/


6. Set ANSIBLE_LOG_BASE environment variable to a desired log path and run the multinode.yml playbook.

         export ANSIBLE_LOG_BASE=/tmp/logs/$(date +%Y%m%d%H%M%S)
         export ANSIBLE_LOG_PATH=$(ANSIBLE_LOG_BASE)/multinode.log
         ansible-playbook -i inventory.ini multinode.yml


7. Logs from the playbook run will be copied from system to the log path specified (ANSIBLE_LOG_BASE).




