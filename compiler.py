import ast
import inspect
import json
import operator as op
import os.path as path

def tab_over(code):
    return '\n'.join(
        ['    ' + line for line in filter(op.truth, code.split('\n'))]
    )


def is_literal(node):
    return any([isinstance(node, t) for t in [ast.Str, ast.Num]]) \
        or (isinstance(node, ast.Name) and (node.id in ['True', 'False']))


def compile_op(op):
    for t, code in {
        ast.Add: '+',
        ast.Sub: '-',
        ast.Gt: '>',
        ast.Lt: '-',
        ast.Eq: '===',
        ast.And: '&&',
        ast.Or: '||',
        ast.Not: '!',
        # TODO!  String interpolation.... JavaScript doesn't support operator
        # overloading
        ast.Mod: '%',
    }.iteritems():
        if isinstance(op, t):
            return code
    if isinstance(op, ast.In):
        raise 'Nope, handle this higher up.'

    print('----OP {}----'.format(op.__class__.__name__))
    print(ast.dump(op))
    return '----OP {}----'.format(op.__class__.__name__)

def wrap_expr(fn):
    def wrapper(node):
        fuck = {'you': ''}
        def add_statement(text):
            fuck['you'] += text
        out = fn(node, add_statement)
        return (out, fuck['you']) \
            if isinstance(out, str) \
            else (out[0], code + fuck['you'])
    return wrapper

@wrap_expr
def compile_expr(node, add_statement):
    def expr(node):
        expr, stmt = compile_expr(node)
        add_statement(stmt)
        return expr

    if isinstance(node, ast.List) or isinstance(node, ast.Tuple):
        return '[{list}]'.format(
            list=', '.join([expr(elt) for elt in node.elts])
        )
    if isinstance(node, ast.Dict):
        if any([not is_literal(key) for key in node.keys]):
            raise 'YOU SUCK!  TODO'
        return '\n'.join([
            '{{',
            '    {defs}',
            '}}'
        ]).format(
            defs=',\n'.join(
                ['{key}: {value}'.format(key=expr(key), value=expr(value))
                    for key, value in zip(node.keys, node.values)]
            )
        )
    if isinstance(node, ast.Name):
        if node.id == 'True':
            return 'true'
        if node.id == 'False':
            return 'false'
        return node.id
    if isinstance(node, ast.Compare):
        def handle_comparator(left, op, right):
            if isinstance(op, ast.In):
                return '\n'.join([
                    '{right}.some(function (_v) {{',
                    '    return _v === {left};',
                    '}})',
                ]).format(
                    left=expr(left),
                    right=expr(right),
                )
            return '{left} {op} {right}'.format(
                left=expr(left),
                op=compile_op(op),
                right=expr(right),
            )
        return ' && '.join([
            handle_comparator(left, op, right)
            for left, op, right in zip(
                [node.left] + node.comparators[:-1],
                node.ops,
                node.comparators,
            )
        ])
    if isinstance(node, ast.Num):
        return '({num})'.format(num=str(node.n))
    if isinstance(node, ast.Str):
        return json.dumps(node.s)
    if isinstance(node, ast.Lambda):
        return '\n'.join([
            'function ({args}) {{',
            '    return {code};',
            '}}',
        ]).format(
            args=', '.join([expr(arg) for arg in node.args.args]),
            code=tab_over(expr(node.body)).lstrip(),
        )
    if isinstance(node, ast.Attribute):
        # TODO: Handle reserved keywords & invalid methods properly
        return '{value}.{attr}'.format(
            value=expr(node.value),
            attr=node.attr,
        )
    if isinstance(node, ast.BoolOp):
        # TODO: Wtf? why is this a list...?  :/
        return '{left} {op} {right}'.format(
            left=expr(node.values[0]),
            op=compile_op(node.op),
            right=expr(node.values[1]),
        )
    if isinstance(node, ast.BinOp):
        # if isinstance(node.op, ast.Add):
        return '\n'.join([
            '{left}.__{op}__({right})',
        ]).format(
            left=expr(node.left),
            op=node.op.__class__.__name__.lower(),
            right=expr(node.right),
        )
        return '{left} {op} {right}'.format(
            left=expr(node.left),
            op=compile_op(node.op),
            right=expr(node.right),
        )
    if isinstance(node, ast.UnaryOp):
        return '{op} {operand}'.format(
            op=compile_op(node.op),
            operand=expr(node.operand),
        )
    if isinstance(node, ast.Call):
        return '{func}({args})'.format(
            func=expr(node.func),
            args=', '.join([expr(arg) for arg in node.args]),
        )
    if isinstance(node, ast.Index):
        return expr(node.value)
    if isinstance(node, ast.IfExp):
        return '({test} ? {body} : {orelse})'.format(
            test=expr(node.test),
            body=expr(node.body),
            orelse=expr(node.orelse),
        )
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            return '\n'.join([
                '(function (list) {{',
                '    var a = {a},',
                '        b = {b};',
                '    return list.slice(a, b < 0 ? list.length - b : b);',
                '}}({list}))',
            ]).format(
                a=expr(node.slice.lower) if node.slice.lower else '0',
                b=expr(node.slice.upper) \
                    if node.slice.upper else 'list.length',
                list=expr(node.value),
            )
        return 'value[slice]'.format(
            value=expr(node.value),
            slice=expr(node.slice),
        )
    if isinstance(node, ast.ListComp):
        def compile_gen(code, gen):
            if isinstance(gen.target, ast.Tuple):
                return '\n'.join([
                    '{iter}.map(function (__temp__) {{',
                    '{args}',
                    '    return {code};',
                    '}})',
                ]).format(
                    iter=expr(gen.iter),
                    args='\n'.join([  # copy-pasta
                        '    %s%s = __temp__[%s];' % (
                            'var ' if isinstance(elt, ast.Name) else '',
                            expr(elt),
                            str(i),
                        )
                        for i, elt in enumerate(gen.target.elts)
                    ]),
                    code=tab_over(code).lstrip(),
                )
            return '\n'.join([
                '{iter}.map(function ({arg}) {{',
                '    return {code};',
                '}})',
            ]).format(
                iter=expr(gen.iter),
                arg=expr(gen.target),
                code=tab_over(code).lstrip(),
            )
        return '{map}{reduce}'.format(  # for scalability
            map=reduce(
                compile_gen,
                node.generators,
                '%s' % expr(node.elt),
            ),
            reduce=''.join(
                ['\n'.join([
                    '.reduce(function (a, b) {',
                    '    return a.concat(b);'
                    '})'
                ]) for _ in range(len(node.generators) - 1)]
            ),
        )
    if isinstance(node, ast.alias):
        return '{asname} = require({name})'.format(
            asname=node.asname or node.name,
            name=json.dumps(node.name),
        )
    if isinstance(node, ast.Slice):
        raise 'NOPE'

    print('----EXPR {}----'.format(node.__class__.__name__))
    print(ast.dump(node))
    return '----EXPR {}----'.format(node.__class__.__name__)

def wrap_statement(fn):
    def wrapper(node):
        fuck = {'you': ''}

        def add_statement(text):
            fuck['you'] += text
        out = fn(node, add_statement)
        return (fuck['you'] and fuck['you'] + '\n') + out
    return wrapper

@wrap_statement
def compile_statement(node, add_statement):
    # expr = compile_expr
    def expr(node):
        expr, stmt = compile_expr(node)
        add_statement(stmt)
        return expr

    def sub_statement(body):
        return tab_over('\n'.join(
            [compile_statement(sub_node) for sub_node in body]
        ))

    if isinstance(node, ast.FunctionDef):
        return 'var {name} = {code};'.format(
            name=node.name,
            code=reduce(
                lambda code, dec: '{dec}({code})'.format(
                    dec=expr(dec),
                    code=code,
                ),
                node.decorator_list,
                '\n'.join([
                    'function ({args}) {{',
                    '{code}',
                    '}}',
                ]).format(
                    args=', '.join([arg.id for arg in node.args.args]),
                    code=sub_statement(node.body),
                ),
            ),
        )
    if isinstance(node, ast.Return):
        return 'return ' + expr(node.value) + ';'
    if isinstance(node, ast.Expr):
        return expr(node.value) + ';'
    if isinstance(node, ast.Pass):
        return ''
    if isinstance(node, ast.Import):
        return '\n'.join(
            ['var ' + expr(name) + ';' for name in node.names]
        )
    if isinstance(node, ast.Assign):
        # TODO: HANDLE SCOPING CORRECTLY
        if len(node.targets) > 1:
            raise 'wtf?  when does this happen?'

        if isinstance(node.targets[0], ast.Tuple):
            return 'var __temp__ = %s;\n' % expr(node.value) + '\n'.join([
                '%s%s = __temp__[%s];' % (
                    'var ' if isinstance(elt, ast.Name) else '',
                    expr(elt),
                    str(i),
                )
                for i, elt in enumerate(node.targets[0].elts)
            ])
        return (
            'var ' + expr(node.targets[0]) + ' = ' +
            expr(node.value) + ';'
        )
    if isinstance(node, ast.Print):
        return 'console.log(%s);' % ', '.join(
            [expr(arg) for arg in node.values]
        )
    if isinstance(node, ast.ClassDef):
        # decorator_list????
        js = 'function %s(???) {\n' % (node.name)
        js += sub_statement(node.body) + '\n'
        js += '}\n'
        js += '\n'.join(
            [node.name + '.prototype = Object.create(' + expr(base) + \
                ');' for base in node.bases]
        )
        return js
    if isinstance(node, ast.Raise):
        return 'throw %s;' % expr(node.type)

    def compile_if(node):
        js = '\n'.join(
            ['if ({test}) {{'.format(test=expr(node.test))] +
            [sub_statement(node.body)] +
            ['}']
        )
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            js += ' else ' + compile_if(node.orelse[0])
        elif len(node.orelse):
            js += ' else {\n' + sub_statement(node.orelse) + '\n}'
        return js
    if isinstance(node, ast.If):
        return compile_if(node)
    if isinstance(node, ast.AugAssign):
        return expr(node.target) + ' ' + compile_op(node.op) + '= ' + \
            expr(node.value)

    print('----STMT %s----' % node.__class__.__name__)
    print(ast.dump(node))

    return '----STMT %s----' % node.__class__.__name__

