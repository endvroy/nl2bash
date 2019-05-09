from bashlint import lint
from bash_parser.bash_ast import BashAST
from bash_parser.normalize_tokens import get_normalize_tokens
from bash_parser import bash_loader


def get_nast(line):
    return lint.normalize_ast(line)


def nast2ast(nast):
    # nast node types: root, utility, flag, argument
    if not nast.children:
        # leaf node
        if nast.kind == 'argument':
            return BashAST(kind=nast.arg_type, value=nast.value)
        else:
            return BashAST(kind=nast.kind, value=nast.value)
    else:
        children = [nast2ast(n) for n in nast.children]
        return BashAST(kind=nast.kind, value=nast.value, children=children)


def sem_trans_ast(ast):
    if ast.kind == 'cmd':
        tmp_ast = BashAST(kind='cmd', prog=ast.prog, args=ast.args,
                          assign_list=[], redir=[])
        # mask the args
        # todo: gather info from children in case of substitution
        name_subst_map = {}
        subst_template = '__SUBST_{}__'
        for i, arg in enumerate(tmp_ast.args):
            # only mask arg containing subst
            for part in arg.parts:
                if part.kind in ['cst',
                                 'lpst',
                                 'rpst',
                                 'arith_subst',
                                 'param_exp_hash',
                                 'param_exp_repl',
                                 'dquote_str']:
                    mask = subst_template.format(i)
                    name_subst_map[mask] = arg
                    tmp_ast.args[i] = BashAST(kind='arg', parts=[BashAST(kind='MASK', value=mask)])
                    break
        tmp_tokens = get_normalize_tokens(tmp_ast)
        tmp_line = ''.join(tmp_tokens)

        # get semantic info and transform the nast back to ast
        nast = lint.normalize_ast(tmp_line)
        masked_ast = nast2ast(nast)
        assert masked_ast.kind == 'root' and len(masked_ast.children) == 1
        util_node = masked_ast.children[0]

        for child in util_node.children:
            pass

        return util_node


if __name__ == '__main__':
    line = input()
    # nast = get_nast(line)
    # ast = transform_nast(nast)
    ast = bash_loader.parse(line)
    sem_nast = sem_trans_ast(ast.last_cmd)
