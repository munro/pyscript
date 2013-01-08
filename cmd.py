import ast
import compiler
import json
import operator as op
import os.path as path
import prelude
import sys

compiled = {}

def compile(f):
    if f in compiled:
        return
    compiled[f] = True

    d = path.dirname(f)
    try:
        code = ast.parse(open(f).read(), f)
    except Exception:
        return
        print('---- CANT FIND: ' + f + ' -----')

    try:
        [compile(path.join(d, name.name + '.py')) \
            for node in code.body if isinstance(node, ast.Import) \
            for name in node.names]

        print('require.define(' + json.dumps(f) + ', function (require) {')
        print(compiler.tab_over('\n'.join(
            filter(op.truth, [compiler.compile_statement(node) or '' for node in code.body])
        )))
        print('});')
    except Exception:
        print('---- ERROR IN: ' + f + ' ----')


def build(start):
    print prelude.prelude

    compile(start)

    print('require.init({file});'.format(file=json.dumps(start)))

build('./' + (sys.argv[1] if len(sys.argv) == 2 else 'src/main.py'))
