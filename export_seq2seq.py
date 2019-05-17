from bash_parser.normalize_tokens import get_normalize_tokens
import json
import pickle

IN_TMPL = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash/{}.cm.filtered.ast.pkl'
OUT_TMPL = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash/{}.cm.filtered.tokens'

READBACK_TMPL = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash/{}.cm.filtered.readback'

if __name__ == '__main__':
    for dataset in ['train', 'dev', 'test']:
        IN_PATH = IN_TMPL.format(dataset)
        OUT_PATH = OUT_TMPL.format(dataset)
        READBACK_PATH = READBACK_TMPL.format(dataset)

        with open(IN_PATH, 'rb') as in_f:
            trees = pickle.load(in_f)
        all_tokens = []
        for tree in trees:
            # try:
            tokens = get_normalize_tokens(tree)
            # except:
            #     tokens = []
            all_tokens.append(tokens)

        with open(OUT_PATH, 'w') as out_f:
            for tokens in all_tokens:
                out_f.write(json.dumps(tokens))
                out_f.write('\n')

        with open(READBACK_PATH, 'w') as rb_f:
            for tokens in all_tokens:
                rb_f.write(''.join(tokens))
                rb_f.write('\n')
