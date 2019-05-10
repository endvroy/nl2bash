from bashlint import lint
from bash_parser.bash_ast import BashAST
from bash_parser.normalize_tokens import get_normalize_tokens
from bash_parser import bash_loader


def reparse_arg(lexeme):
    input_stream = bash_loader.InputStream(lexeme)
    lexer = bash_loader.BashLexer(input_stream)
    stream = bash_loader.CommonTokenStream(lexer)
    parser = bash_loader.BashParser(stream)
    tree = parser.arg()
    visitor = bash_loader.BashASTVisitor()
    ast = visitor.visit(tree)
    return ast


def get_nast(line):
    return lint.normalize_ast(line)


def nast2ast(nast):
    # nast node types: root, utility, flag, argument
    assert nast.kind == 'root' and len(nast.children) == 1
    util_node = nast.children[0]
    prog = BashAST(kind='prog', parts=[BashAST(kind='VARNAME', value=util_node.value)])
    args = [nast_arg2ast(c) for c in util_node.children]
    ast = BashAST(kind='cmd', prog=prog, args=args,
                  assign_list=[], redir=[])
    return ast


def nast_arg2ast(nast):
    # leaf node
    if nast.kind == 'argument':
        ast = BashAST(kind=nast.arg_type, value=nast.value)
    else:
        # flag
        ast = BashAST(kind=nast.kind, name=nast.value)
        if nast.children:
            assert len(nast.children) == 1
            value = nast_arg2ast(nast.children[0])
        else:
            value = None
        ast.value = value
    return ast


def unmask_ast(ast, name_subst_map):
    if not hasattr(ast, 'children'):
        # leaf node
        # todo: split subtoken (or reparse)
        if ast.value in name_subst_map:
            # masked
            # todo: reparse arg
            ast.value = name_subst_map[ast.value]
        else:
            return ast
    else:
        # todo: transform back to normal form? (maybe should be done in nast2ast)
        return BashAST(kind=ast.kind,
                       value=ast.value,
                       children=[unmask_ast(c, name_subst_map)
                                 for c in ast.children])


def sem_trans_ast(ast):
    # todo: find the base case
    if ast.kind == 'cmd':
        tmp_ast = BashAST(kind='cmd', prog=ast.prog, args=ast.args,
                          assign_list=[], redir=[])
        # mask the args containing substitution
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

        unmasked = unmask_ast(util_node, name_subst_map)
        # todo: continue working on subparts if necessary (maybe via recurse?)
        # todo: add back assign and redir
        return unmasked
    else:
        # todo: recurse
        pass


if __name__ == '__main__':
    line = input()
    nast = get_nast(line)
    ast = nast2ast(nast)
    # ast = bash_loader.parse(line)
    # sem_nast = sem_trans_ast(ast.last_cmd)
