#!/usr/bin/python

# Copyright (c) 2016-2017, Intel Corporation.
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
import glob
import itertools
import os

DOCUMENTATION = '''
---
module: calculate_pmd_core_mask
short_description: reserve CPU cores from each NUMA node an interface is attached too.
description:
   - This is use for OVS DPDK to calculate with cores to reserve for DPKD and OVS use
   - algorithm:
       - find all the NUMA local cpus for each interface
       - for each NUMA node cpu list:
           - mask one core for OVS thread
           - mask two cores for PMD threads
    - Note: if there are <= 4 core we don't mask CPU cores.
options:
  interfaces: list of interfaces to calculate masks for.
'''


def select_cores(cpu_lists):
    ovs_cores, pmd_cores, unused_cores = select_masked_cores(cpu_lists)
    return {
        "ovs_pmd_cores": sorted(pmd_cores),
        "ovs_cores": sorted(ovs_cores),
        "unused_cores": sorted(unused_cores),
        "ovs_pmd_core_mask": gen_core_mask(pmd_cores),
        "ovs_core_mask": gen_core_mask(ovs_cores),
        "unused_core_mask": gen_core_mask(unused_cores)
    }


def split_cpu_list(cpu_list):
    if cpu_list:
        ranges = cpu_list.split(',')
        bounds = ([int(b) for b in r.split('-')] for r in ranges)
        # include upper bound
        range_objects = (xrange(bound[0], bound[1] + 1 if len(bound) == 2 else bound[0] + 1) for bound
                         in bounds)
        return sorted(itertools.chain.from_iterable(range_objects))
    else:
        return []


def test_split_cpu_list():

    local_cpulist = "0-17,36-53"
    assert split_cpu_list(local_cpulist) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]
    assert split_cpu_list(local_cpulist) == range(0, 18) + range(36, 54)


def test_split_cpu_list_single():

    local_cpulist = "14-27"
    assert split_cpu_list(local_cpulist) == range(14, 28)


def test_split_cpu_list_empty():

    local_cpulist = ""
    assert split_cpu_list(local_cpulist) == []


def select_masked_cores(cpu_lists):
    """
    Select OVS and PMD cores from the avaliable list of cpus.
    We select one CPU for OVS and two CPUs for PMD.
    We select from the end of the CPU list to avoid selecting CPU 0.

    :param cpu_lists: list of CPUs
    :type cpu_lists: iter()
    :return: tuple of ovs_cores and pmd_cores
    :rtype: tuple
    """
    ovs_cores = set()
    pmd_cores = set()
    unused_cores = set()
    for cpu_list in cpu_lists:
        # must make a copy because we pop and mutate
        cpu_list = cpu_list[:]
        # only mask cores if we have more than 4 CPUs
        if len(cpu_list) > 4:
            # take one core from each range for ovs
            # save the first core for unused, in case it is core 0.
            unused_cores.add(cpu_list.pop(0))
            ovs_cores.add(cpu_list.pop(0))
            # take two cores from each range for pmd
            pmd_cores.add(cpu_list.pop(0))
            pmd_cores.add(cpu_list.pop(0))
            unused_cores.update(cpu_list)
    return ovs_cores, pmd_cores, unused_cores


def test_select_masked_cores():
    local_cpulist = "0-17,36-53"
    cpu_ranges = split_cpu_list(local_cpulist)
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([cpu_ranges])
    assert ovs_cores == {1}
    assert pmd_cores == {2, 3}
    assert unused_cores == set(xrange(54)) - set(xrange(18, 36)) - {1, 2, 3}


def test_select_masked_cores_does_not_mutate():
    local_cpulist = "0-17,36-53"
    cpu_ranges = split_cpu_list(local_cpulist)
    orig_cpu_ranges = cpu_ranges[:]
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([cpu_ranges])
    assert ovs_cores == {1}
    assert pmd_cores == {2, 3}
    assert unused_cores == set(xrange(54)) - set(xrange(18, 36)) - {1, 2, 3}
    assert orig_cpu_ranges == cpu_ranges


def test_select_masked_cores_single():
    local_cpulist = "14-27"
    cpu_ranges = split_cpu_list(local_cpulist)
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([cpu_ranges])
    assert ovs_cores == {15}
    assert pmd_cores == {16, 17}
    assert unused_cores == set(range(14, 28)) - {15, 16, 17}


def test_select_masked_cores_no_cpus():
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([])
    assert ovs_cores == set()
    assert pmd_cores == set()
    assert unused_cores == set()


def test_select_masked_cores_four_cpus():
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([range(4)])
    assert ovs_cores == set()
    assert pmd_cores == set()
    assert unused_cores == set()


def test_select_masked_cores_five_cpus():
    ovs_cores, pmd_cores, unused_cores = select_masked_cores([range(5)])
    assert ovs_cores == {1}
    assert pmd_cores == {2, 3}
    assert unused_cores == {0, 4}


def gen_core_mask(core_list):
    # remove trailing L
    mask = hex(sum(2 ** c for c in core_list)).rstrip('L')
    # 0x0 isn't valid, we need an empty string
    if mask == '0x0':
        mask = ''
    return mask


def test_gen_core_mask():
    core_list = {52, 51}
    mask = gen_core_mask(core_list)
    assert mask == "0x18000000000000"
    core_list = {1, 2}
    mask = gen_core_mask(core_list)
    assert mask == "0x6"
    mask = gen_core_mask({})
    assert mask == ""


def get_numa_nodes():

    nodes_sysfs = glob.iglob("/sys/devices/system/node/node*")
    nodes = {}
    for node_sysfs in nodes_sysfs:
        num = os.path.basename(node_sysfs).replace("node", "")
        with open(os.path.join(node_sysfs, "cpulist")) as cpulist_file:
            cpulist = cpulist_file.read().strip()
        nodes[num] = split_cpu_list(cpulist)

    return nodes

# checks on local system
# def test_get_numa_nodes():
#     n = get_numa_nodes()
#     assert n == {'0': [0, 1, 2, 3]}


def main():

    module = AnsibleModule(
        argument_spec={'interfaces': {'required': True, 'type': 'list'}}
    )
    params = module.params

    numa_nodes = get_numa_nodes()
    all_cores = set(itertools.chain.from_iterable(numa_nodes.itervalues()))

    cpu_lists = {}
    for intf in params['interfaces']:
        try:
            if "bond" not in intf:
                with open("/sys/class/net/{}/device/local_cpulist".format(intf)) as cpu_list:
                    cpu_lists[intf] = split_cpu_list(cpu_list.read().strip())
        except EnvironmentError as e:
            if os.path.basename(os.readlink("/sys/class/net/{}/device/driver".format(intf))) == "virtio_net":
                # virtual enviroment, use all cores
                cpu_lists[intf] = ",".join(sorted(all_cores))
            else:
                module.fail_json(msg=str(e))

    interface_cores = set(itertools.chain.from_iterable(cpu_lists.itervalues()))
    ansible_facts = select_cores(cpu_lists.itervalues())
    # all the cores from all the nodes minus the cores from the nodes
    # attached to interfaces
    # this could be the empty set if we can interfaces on all nodes, or only one node
    other_numa_node_cores = all_cores - interface_cores

    ansible_facts.update({
        "interface_numa_cpu_lists": cpu_lists,
        "numa_nodes": numa_nodes,
        "all_cores": sorted(all_cores),
        "other_numa_node_cores": sorted(other_numa_node_cores),
    })

    module.exit_json(changed=True, ansible_facts=ansible_facts)

# use this form to include ansible boilerplate so we can run unittests

#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

if __name__ == '__main__':
    main()
