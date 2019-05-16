from bashlint import lint
from bash_parser.bash_ast import BashAST
from bash_parser.normalize_tokens import get_normalize_tokens
from bash_parser import bash_loader
from bashlint.bash import argument_types
import copy


def reparse_arg(lexeme):
    input_stream = bash_loader.InputStream(lexeme)
    lexer = bash_loader.PanicBashLexer(input_stream)
    stream = bash_loader.CommonTokenStream(lexer)
    parser = bash_loader.BashParser(stream)
    parser._errHandler = bash_loader.BailErrorStrategy()
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
    if nast.kind == 'argument':
        # leaf node
        ast = BashAST(kind=nast.arg_type, parts=nast.value)
    elif nast.kind == 'utility':
        ast = nast2ast(BashAST(kind='root', children=[nast]))
    else:
        # flag
        ast = BashAST(kind=nast.kind, name=nast.value)
        if nast.children:
            # assert len(nast.children) == 1
            value = [nast_arg2ast(nast.children[0])]
        else:
            value = None
        ast.value = value
    return ast


def unmask_ast(ast, name_subst_map):
    nodes = []
    for arg in ast.args:
        if arg.kind == 'flag':
            if arg.value is not None:
                nodes.extend([x for x in arg.value if x.kind in argument_types])
        elif arg.kind in argument_types:
            # arg node
            nodes.append(arg)

    for arg in nodes:
        if arg.parts in name_subst_map:
            # masked arg
            # the corresponding node should be processed first!
            arg.parts = name_subst_map[arg.parts].parts
        else:
            # split subtokens by reparsing
            arg.parts = reparse_arg(arg.parts).parts


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
            if not tmp_line:
                # only assignments
                return ast
            # get semantic info and transform the nast back to ast
            nast = lint.normalize_ast(tmp_line)
            if not nast:
                # semantic parsing not available
                return ast
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


# todo: export semantic ast
# todo: transform to DRNN Node class
# todo: create sketch
# todo: export tokens for seq2seq
# todo: create sketch for seq2seq

if __name__ == '__main__':
    line = input()
    # nast = get_nast(line)
    # ast = nast2ast(nast)
    ast = bash_loader.parse(line)
    # sem_ast = copy.deepcopy(ast)
    sem_ast = sem_trans_ast(ast)
