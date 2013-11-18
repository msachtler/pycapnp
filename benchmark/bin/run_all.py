#!/usr/bin/env python
from __future__ import print_function

from subprocess import Popen, PIPE
import sys
import os
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', "--langs", help="Add languages to test, ie: -l capnproto -l protobuf", action='append', default=['pycapnp', 'pyproto', 'pyproto_cpp'])
    parser.add_argument("-r", "--reuse", help="If this flag is passed, re-use tests will be run", action='store_true',)
    parser.add_argument("-c", "--compression", help="If this flag is passed, compression tests will be run", action='store_true')
    parser.add_argument("-i", "--scale_iters", help="Scaling factor to multiply the default iters by", type=float, default=1.0)

    return parser.parse_args()

def run_one(prefix, name, mode, iters, faster, compression):
    res_type = prefix
    reuse = 'no-reuse'

    if faster:
        reuse = 'reuse'
        res_type += '_reuse'
    if compression != 'none':
        res_type += '_' + compression

    command = ["time", "-p", prefix+"-"+name, mode, reuse, compression, str(iters)]
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    res = p.communicate()[1]

    data = {}

    if p.returncode != 0:
        sys.stderr.write(' '.join(command) + ' failed to run with errors: ' + res + '\n')
        sys.stderr.flush()
    else:
        res = res.strip()

        for line in res.split('\n'):
            vals = line.split()
            data[vals[0]] = float(vals[1])

    data['type'] = res_type
    data['mode'] = mode
    data['name'] = name
    data['iters'] = iters

    return data


def run_each(name, langs, reuse, compression, iters):
    ret = []

    for lang_name in langs:
        ret.append(run_one(lang_name, name, 'object', iters, False, 'none'))
        ret.append(run_one(lang_name, name, 'bytes', iters, False, 'none'))
        if reuse:
            ret.append(run_one(lang_name, name, 'object', iters, True, 'none'))
            ret.append(run_one(lang_name, name, 'bytes', iters, True, 'none'))
            if compression:
                ret.append(run_one(lang_name, name, 'bytes', iters, True, 'packed'))
        if compression:
            ret.append(run_one(lang_name, name, 'bytes', iters, False, 'packed'))

    return ret

def main():
    args = parse_args()

    os.environ['PATH'] += ':.'

    data = []
    data += run_each('carsales', args.langs, args.reuse, args.compression, int(2000 * args.scale_iters))
    data += run_each('catrank', args.langs, args.reuse, args.compression, int(100 * args.scale_iters))
    data += run_each('eval', args.langs, args.reuse, args.compression, int(10000 * args.scale_iters))
    json.dump(data, sys.stdout, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    main()
