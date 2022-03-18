import bz2
import pickle

def compress_pickle(name, data):
    with bz2.BZ2File(name, 'w') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def decompress_pickle(name):
    data = bz2.BZ2File(name, 'rb')
    data = pickle.load(data)
    return data
