#!/usr/bin/env python
# Copyright (c) 2015-2017, Intel Corporation.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

DOCUMENTATION = '''
---
module: generate_network_mappings
short_description: generate all OVS_BRIDGE_MAPPING type local.conf settings
description:
    - generate the following mappings based on tenant networks
        - ovs_bridge_mapping
        - physical_network
        - vlan_interface
        - ovs_physical_bridge
        - m2_vlan_ranges
        - odl_provider_mappings
        - odl_provider_mappings_ovs_vlan
options:
  tenant_networks: dict of all the tenant_networks
  mappings: optional subset of mappings to create
'''

def do_ovs_bridge_mapping(seq):
    return ",".join(
        ("physnet{0}:br-{1}".format(i, intf) for i, intf in enumerate(sorted(seq), 1)))


def do_physical_network(seq):
    return ','.join("physnet{}".format(i) for i, __ in enumerate(seq, 1))


def do_vlan_interface(seq):
    return ",".join(sorted(seq))


def do_ovs_physical_bridge(seq):
    return ",".join(("br-{}".format(s) for s in sorted(seq)))


def do_m2_vlan_ranges(seq):
    return ",".join(
        ("physnet{0}:{1}".format(i, vlan_range) for i, vlan_range in enumerate(sorted(seq), 1)))


def do_odl_provider_mappings(seq):
    return ",".join(
        ("physnet{0}:br-{1}".format(i, intf) for i, intf in enumerate(sorted(seq), 1)))


def do_odl_provider_mappings_ovs_vlan(seq):
    return ",".join(
        ("physnet{0}:{1}".format(i, intf) for i, intf in enumerate(sorted(seq), 1)))


MAPPINGS = {
    'ovs_bridge_mapping': do_ovs_bridge_mapping,
    'physical_network': do_physical_network,
    'vlan_interface': do_vlan_interface,
    'ovs_physical_bridge': do_ovs_physical_bridge,
    'm2_vlan_ranges': do_m2_vlan_ranges,
    'odl_provider_mappings': do_odl_provider_mappings,
    'odl_provider_mappings_ovs_vlan': do_odl_provider_mappings_ovs_vlan,
}

PORT_ATTRIBUTE = {
    'ovs_bridge_mapping': 'interface',
    'physical_network': 'interface',
    'vlan_interface': 'interface',
    'ovs_physical_bridge': 'interface',
    'm2_vlan_ranges': 'vlan_ranges',
    'odl_provider_mappings': 'interface',
    'odl_provider_mappings_ovs_vlan': 'interface',
}


def main():
    module = AnsibleModule(
        argument_spec={'tenant_networks': {'required': True, 'type': 'dict'},
                       'mappings': {'required': False,
                                    'default': MAPPINGS.keys(),
                                    'type': 'list'}}
    )
    ansible_facts = {}
    for mapping in module.params['mappings']:
        args = (port[PORT_ATTRIBUTE[mapping]] for port in
                module.params['tenant_networks'].itervalues())
        ansible_facts[mapping] = MAPPINGS[mapping](args)

    module.exit_json(changed=True, ansible_facts=ansible_facts)


# <<INCLUDE_ANSIBLE_MODULE_COMMON>>
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()
