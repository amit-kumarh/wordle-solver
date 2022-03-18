from collections import Counter, defaultdict
from scipy.stats import entropy
from wordfreq import word_frequency as freq
import itertools
from tqdm import tqdm
import utils
import numpy as np
import json

PATTERNS = list(itertools.product(range(3), repeat=5))
use_tares = False

# TODO: Incorporate word weights and scoring. Make the CLI. Translate in Spanish
def get_sorted_words():
    with open('words.txt', 'r') as f:
        words = list(i.strip() for i in f.readlines())
    
    raw_freqs = {word: freq(word, 'en') for word in words}
    sorted_words = sorted(raw_freqs, key= lambda x: raw_freqs[x])
    return sorted_words
    
def gen_weights(width=10, cutoff=3000):
    sigmoid = lambda x: 1/(1 + np.exp(-x))
    sorted_words = get_sorted_words()
    num_words = len(sorted_words)

    center = cutoff/num_words
    xs = np.linspace(center - width/2, center + width/2, num_words)
    
    weights = {word: sigmoid(rank) for word, rank in zip(sorted_words, xs)}
    return weights

def make_pattern(guess, ans):
    ''' 
    Given a guess and an answer, calculate the wordle pattern generated from
    that guess, where:

    Green = 2
    Yellow = 1
    Grey = 0

    Args:
        guess, ans (str): the guess and answer to generate the pattern,
            respectively

    Returns:
        pattern (tuple): Tuple representing the wordle pattern according to the
            rules above
    '''
    pattern = []
    counts = Counter(ans) # Account for repeated letters
    for i, char in enumerate(guess):
        if char == ans[i]:
            pattern.append(2)
            counts[char] -= 1
        elif char in set(ans) and counts[char] > 0:
            pattern.append(1)
            counts[char] -= 1
        else:
            pattern.append(0)
    return tuple(pattern)

def gen_pattern_dict(words):
    '''
    Generate dictionary where each word in possible answers is a key, and each
    value is another dictionary. The inner dictionary's keys are all of the
    possible Wordle patterns that can result from guessing that word, and it's
    values are a set containing all of the words that match the guess word and
    the resultant pattern.

    Args:
        words (list): list of strings of all possible guesses

    Returns:
        pattern_dict (dict): Dictionary mapping all patterns and words to
            remaining candidates
    '''
    pattern_dict = defaultdict(lambda: defaultdict(set))
    for word in tqdm(words):
        for word2 in words:
            pattern = make_pattern(word, word2)
            pattern_dict[word][pattern].add(word2)
    return dict(pattern_dict)

def calc_entropies(guesses, rem_words, pattern_dict, weights):
    entropies = {}
    for guess in guesses:
        # Calculate entropy of distribution for how many possible remaining words will exist from all 243 patterns
        cnt = []
        for pattern in PATTERNS:
            matches = pattern_dict[guess][pattern]
            cnt.append(sum(weights[match] for match in matches.intersection(rem_words)))
        entropies[guess] = entropy(cnt)
    return entropies

def play_game(ans, words, pattern_dict, weights):
    words = set(words)
    rem_words = words.copy()
    init = 1

    # Save time for bulk calculations since the first guess will always be the same
    if use_tares:
        guess = 'tares'
        pattern = make_pattern(guess, ans)
        rem_words = rem_words.intersection(pattern_dict[guess][pattern])
        init = 2

    for i in range(init, 10):
        if len(rem_words) == 1:
            # Game is won
            guess = rem_words.pop()
        else:
            # Guess whatever word has the maximum entropy of its distribution
            entropies = calc_entropies(words, rem_words, pattern_dict, weights)
            guess = max(entropies.items(), key=lambda x: x[1])[0]

        # Reduce the remaining words to those that match the new pattern 
        pattern = make_pattern(guess, ans)
        rem_words = rem_words.intersection(pattern_dict[guess][pattern])
        
        # Some console output
        if not use_tares:
            print(f'Guess #{i}: {guess}\nGiven info {pattern}\nExp. Entropy: {round(entropies[guess], 3)}')
            if len(rem_words) < 100:
                print(rem_words)

        if guess == ans:
            # Game is won
            print(f'Guessed {ans} in {i} guesses')
            break

    return i

def test_all_answers(of_name, gen=False):
    # Loading text files
    with open('words.txt', 'r') as f:
        words = list(i.strip() for i in f.readlines())
    with open('solutions.txt', 'r') as sol:
        solutions = list(i.strip() for i in sol.readlines())

    # Generating or loading pattern_dict
    if gen:
        pattern_dict = wordle.gen_pattern_dict(words)
        utils.compress_pickle('patterns.pbz2', pattern_dict)
    else:
        print('Loading pattern dictionary (may take up to two minutes)...')
        pattern_dict = utils.decompress_pickle('patterns.pbz2')

    # Playing all 2315 possible games
    stats = {}
    for sol in tqdm(solutions):
        stats[sol] = wordle.play_game(sol, words, pattern_dict)

    # Writing output to JSON
    with open(of_name, 'w') as of:
        json.dump(stats, of)

REMAP_COLORS = {0: "⬛", 1: "🟨", 2: "🟩"}
def emojify(pattern):
    emoji = ''
    for char in pattern:
        emoji += REMAP_COLORS[char]
    return emoji

        
    
