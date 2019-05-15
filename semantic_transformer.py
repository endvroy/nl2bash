from bashlint import lint
from bash_parser.bash_ast import BashAST
from bash_parser.normalize_tokens import get_normalize_tokens
from bash_parser import bash_loader
import copy


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
    for arg in ast.args:
        if arg.kind == 'flag':
            if arg.value is not None:
                arg = arg.value
            else:
                continue
        # arg node
        if arg.value in name_subst_map:
            # masked arg
            # the corresponding node should be processed first!
            arg.value = name_subst_map[arg.value].parts
        else:
            # split subtokens by reparsing
            arg.value = reparse_arg(arg.value).parts


def sem_trans_ast(ast):
    if isinstance(ast, BashAST):
        if ast.kind == 'cmd':
            tmp_ast = BashAST(kind='cmd', prog=ast.prog, args=ast.args.copy(),
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
                                     'param_exp',
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

            unmasked = copy.deepcopy(masked_ast)
            # the corresponding node should be processed first
            for k, v in name_subst_map.items():
                name_subst_map[k] = sem_trans_ast(v)
            unmask_ast(unmasked, name_subst_map)
            # add back assign and redir
            unmasked.assign_list = ast.assign_list
            unmasked.redir = ast.redir
            return unmasked
        # recurse
        else:
            for k, v in ast.__dict__.items():
                ast.__dict__[k] = sem_trans_ast(v)
            return ast
    elif isinstance(ast, list):
        # parts
        return [sem_trans_ast(x) for x in ast]
    else:
        # not an AST node
        return ast


if __name__ == '__main__':
    line = input()
    # nast = get_nast(line)
    # ast = nast2ast(nast)
    ast = bash_loader.parse(line)
    # sem_ast = copy.deepcopy(ast)
    sem_ast = sem_trans_ast(ast)
