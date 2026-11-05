"""Fixed-width signed/unsigned programmer arithmetic, bases 2/8/10/16."""
from __future__ import annotations


def _width(width):
    width = int(width)
    if width not in (8, 16, 32, 64):
        raise ValueError('Word size must be 8, 16, 32 or 64')
    return width


def parse_int(text, base=10):
    if base not in (2, 8, 10, 16):
        raise ValueError('Input base must be 2, 8, 10 or 16')
    if len(str(text)) > 100:
        raise ValueError('Integer input is too long')
    return int(str(text).replace('_', '').strip(), base)


def represent(value: int, width: int = 32):
    width = _width(width)
    u = int(value) & ((1 << width) - 1)
    s = u if u < 1 << (width-1) else u-(1 << width)
    return {'Signed decimal': s, 'Unsigned decimal': u,
            'Binary': '0b'+format(u, f'0{width}b'),
            'Octal': '0o'+format(u, f'0{(width+2)//3}o'),
            'Hexadecimal': '0x'+format(u, f'0{width//4}X')}


def bitwise(a, b, op, width=32):
    width = _width(width)
    mask = (1 << width) - 1
    ua, ub = a & mask, b & mask
    if op == 'AND': result = ua & ub
    elif op == 'OR': result = ua | ub
    elif op == 'XOR': result = ua ^ ub
    elif op == 'NAND': result = ~(ua & ub)
    elif op == 'NOR': result = ~(ua | ub)
    elif op == 'NOT A': result = ~ua
    else: raise ValueError('Operator: AND, OR, XOR, NAND, NOR, NOT A')
    return represent(result, width)


def shift(a, positions, direction, width=32):
    width = _width(width)
    mask = (1 << width)-1
    if not 0 <= positions <= 1024:
        raise ValueError('Shift count 0..1024')
    ua = a & mask
    if direction == 'LEFT': result = (ua << positions) & mask
    elif direction == 'RIGHT': result = ua >> positions
    elif direction == 'ARITH RIGHT':
        signed = represent(a, width)['Signed decimal']
        result = signed >> positions
    else: raise ValueError('Direction: LEFT, RIGHT, ARITH RIGHT')
    return represent(result, width)


def rotate(a, positions, direction, width=32):
    width = _width(width)
    if positions < 0 or positions > 1024:
        raise ValueError('Rotate count 0..1024')
    n = positions % width
    mask = (1<<width)-1
    ua = a & mask
    if direction == 'LEFT': result = ((ua<<n) | (ua>>(width-n))) & mask
    elif direction == 'RIGHT': result = ((ua>>n) | (ua<<(width-n))) & mask
    else: raise ValueError('Direction: LEFT or RIGHT')
    return represent(result, width)


def prog_convert(v):
    base = int(v['base'])
    return represent(parse_int(v['value'], base), int(v['width']))


def prog_logic(v):
    base = int(v['base'])
    return bitwise(parse_int(v['a'], base), parse_int(v['b'], base),
                   v['op'].strip().upper(), int(v['width']))


def prog_shift(v):
    return shift(parse_int(v['a'], int(v['base'])), int(v['count']),
                 v['direction'].strip().upper(), int(v['width']))


def prog_rotate(v):
    return rotate(parse_int(v['a'], int(v['base'])), int(v['count']),
                  v['direction'].strip().upper(), int(v['width']))


def prog_count(v):
    w = _width(int(v['width']))
    u = parse_int(v['a'], int(v['base'])) & ((1<<w)-1)
    return {'Set bits': u.bit_count(), 'Zero bits': w-u.bit_count(),
            'Representation': represent(u,w)}
