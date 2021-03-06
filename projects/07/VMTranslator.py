#!/usr/bin/env python3

import sys
from pathlib import Path


def main():
    in_files, out_file = get_files()
    with open(out_file, 'w') as f_out:
        for f in in_files:
            with open(f, 'r') as f_in:
                for line in f_in:
                    f_out.write(translate(line, f.stem))


def get_files():
    p = Path(sys.argv[1])
    vm_files = list(p.glob('*.vm')) if p.is_dir() else [p]
    base_dir = p if p.is_dir() else p.parent
    asm_file = base_dir / vm_files[0].name.replace('vm', 'asm')
    return vm_files, asm_file


def translate(line, f):
    command, *args = line.split('//')[0].strip().split(' ')
    cmds = []
    if command in math_ops:
        cmds += translate_math(command)
    elif command in comp_ops:
        cmds += translate_comp(command)
    elif command in mem_ops:
        cmds += translate_mem(f, command, *args)
    return '\n'.join(cmds) + ('\n' if len(cmds) > 0 else '')


def translate_math(command):
    cmds = []
    n = math_ops[command]['n_args']
    cmds += ['@SP', 'A=M-1'] if n == 1 else ['@SP', 'AM=M-1', 'D=M', 'A=A-1']
    cmds += [math_ops[command]['asm_op']]
    return cmds


def translate_comp(command):
    cmds = []
    comp_count = next(comp_counter)
    cmds += ['@SP', 'AM=M-1', 'D=M']
    cmds += ['@SP', 'A=M-1']
    cmds += ['D=M-D']
    cmds += [f'@COMP_JUMP.{comp_count}']
    cmds += [comp_ops[command]]
    cmds += ['@SP', 'A=M-1', 'M=0']
    cmds += [f'@CONTINUE_JUMP.{comp_count}']
    cmds += ['0;JMP']
    cmds += [f'(COMP_JUMP.{comp_count})']
    cmds += ['@SP', 'A=M-1', 'M=-1']
    cmds += [f'(CONTINUE_JUMP.{comp_count})']
    return cmds


def translate_mem(f, command, segment, index):
    cmds = []
    seg_addr = segment_address_lookups[segment](index, f)
    if command == 'push':
        cmds += seg_addr
        cmds += ['D=A'] if segment == 'constant' else ['D=M']
        cmds += ['@SP', 'M=M+1', 'A=M-1', 'M=D']
    else:
        if len(seg_addr) > 1:
            cmds += seg_addr
            cmds += ['D=A']
            cmds += ['@R13', 'M=D']
            cmds += ['@SP', 'AM=M-1', 'D=M']
            cmds += ['@R13', 'A=M', 'M=D']
        else:
            cmds += ['@SP', 'AM=M-1', 'D=M']
            cmds += seg_addr
            cmds += ['M=D']
    return cmds


def comp_incrementer():
    i = 0
    while True:
        yield i
        i += 1


math_ops = {
    'add': {'asm_op': 'M=M+D', 'n_args': 2},
    'sub': {'asm_op': 'M=M-D', 'n_args': 2},
    'neg': {'asm_op':  'M=-M', 'n_args': 1},
    'and': {'asm_op': 'M=M&D', 'n_args': 2},
    'or':  {'asm_op': 'M=M|D', 'n_args': 2},
    'not': {'asm_op':  'M=!M', 'n_args': 1},
}

comp_ops = {'eq': 'D;JEQ', 'lt': 'D;JLT', 'gt': 'D;JGT'}

mem_ops = ['push', 'pop']

segment_address_lookups = {
    'local':    lambda i, f: f'@LCL D=M @{i} A=D+A'.split(),
    'argument': lambda i, f: f'@ARG D=M @{i} A=D+A'.split(),
    'this':     lambda i, f: f'@THIS D=M @{i} A=D+A'.split(),
    'that':     lambda i, f: f'@THAT D=M @{i} A=D+A'.split(),
    'pointer':  lambda i, f: [f'@R{3 + int(i)}'],
    'temp':     lambda i, f: [f'@R{5 + int(i)}'],
    'static':   lambda i, f: [f'@{f}.{i}'],
    'constant': lambda i, f: [f'@{i}'],
}

comp_counter = comp_incrementer()

if __name__ == '__main__':
    main()
