#!/usr/bin/env python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import re
import sys


def get_sector_size(output):
    line = (line for line in output if line.startswith("Sector size")).next()
    match = re.search(r': \d+ bytes / (\d+) bytes', line)
    
    return int(match.group(1))


def get_partition_offset(output, fs_type):
    in_partitions = False
    type_key = None
    for line in output:
        if not in_partitions:
            in_partitions = line.strip().startswith('Device')
            type_key = 5 if "Blocks" in line else 6 # Bleh. Depends which version of fdisk is used
        else:
            parts = re.split(r'\s+', line, maxsplit=type_key)
            if parts[type_key].lower().startswith(fs_type.lower()):
                return int(parts[1])

    raise Exception("Not found partition: {}".format("\n".join(output)))


def fdisk(image, fs_type):
    output = subprocess.check_output(["fdisk", "-l", image]).splitlines()
    output = [line for line in output if line]

    sector_size = get_sector_size(output)
    partition_offset = get_partition_offset(output, fs_type)
    
    return {
        "sector_size": sector_size,
        "offset_sectors": partition_offset,
        "offset_bytes": partition_offset * sector_size,
    }
    

def main():
    module = AnsibleModule(argument_spec=dict(
        image=dict(required=True),
        fs_type=dict(required=True)
    ))
    output = fdisk(module.params['image'], module.params['fs_type'])

    module.exit_json(changed=True, **output)


if __name__ == "__main__":
    main()
