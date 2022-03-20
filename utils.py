import bz2
import pickle
import os.path

def compress_pickle(name, data):
    with bz2.BZ2File(name, 'w') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def decompress_pickle(name):
    data = bz2.BZ2File(name, 'rb')
    data = pickle.load(data)
    return data

def reg_pickle(name, data):
    with open(name, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def get_pickle(name):
    with open(name, 'rb') as f:
        data = pickle.load(f)
    return data
        
def get_words():
    with open('words.txt', 'r') as f:
        words = list(i.strip() for i in f.readlines())
    return words

def get_pattern_dict():
    if os.path.exists('patterns.pbz2'):
        typer.echo('Loading compressed pattern dictionary (may take up to two minutes)...')
        pattern_dict = decompress_pickle('patterns.pbz2')
    elif os.path.exists('patterns.p'):
        pattern_dict = get_pickle('patterns.p')
    else:
        raise FileNotFoundError(f'Pattern dictionary not found. If you haven\'t, you can generate a pattern dicitonary by running wordle gen_pattern_dict.')
    return pattern_dict
