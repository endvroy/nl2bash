from bashlint import lint
from bash_parser.bash_ast import BashAST
from bash_parser.normalize_tokens import get_normalize_tokens


def get_nast(line):
    return lint.normalize_ast(line)


def transform_nast(nast):
    # nast node types: root, utility, flag, argument
    if not nast.children:
        # leaf node
        return BashAST(kind=nast.kind, value=nast.value)
    else:
        children = [transform_nast(n) for n in nast.children]
        return BashAST(kind=nast.kind, value=nast.value, children=children)


def sem_trans_ast(ast):
    if ast.kind == 'cmd':
        tmp_ast = BashAST(kind='cmd', prog=ast.prog, args=ast.args)
        # mask the args
        # todo: gather info from children in case of substitution
        name_subst_map = {}
        subst_template = '__SUBST_{}__'
        i = 0
        for arg in tmp_ast.args:
            for part in arg.parts:
                # todo: only mask subst?
                mask = subst_template.format(i)
                name_subst_map[mask] = part
                part[i] = mask
                i += 1
        tmp_tokens = get_normalize_tokens(tmp_ast)
        tmp_line = ''.join(tmp_tokens)
        nast = lint.normalize_ast(tmp_line)
        masked_ast = transform_nast(nast)
        for child in masked_ast.children:
            if child.kind == 'argument':
                pass
                # todo: fill in


if __name__ == '__main__':
    line = input()
    nast = get_nast(line)
    ast = transform_nast(nast)
