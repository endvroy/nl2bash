from semantic_transformer import bash_loader, sem_trans_ast
import pickle

in_tmpl = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash/{}.cm.filtered'
out_tmpl = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash/{}.cm.filtered.ast.pkl'


class ParseError(Exception):
    pass


def main():
    for dataset in ['train', 'dev', 'test']:
        in_path = in_tmpl.format(dataset)
        out_path = out_tmpl.format(dataset)
        with open(in_path) as in_f:
            lines = in_f.readlines()
        l = []
        for i, line in enumerate(lines):
            try:
                ast = bash_loader.parse(line)
            except:
                print('error in {} line {}'.format(dataset, i))
                sem_ast = None
            else:
                sem_ast = sem_trans_ast(ast)
            l.append(sem_ast)
        with open(out_path, 'wb') as out_f:
            pickle.dump(l, out_f)


if __name__ == '__main__':
    main()
