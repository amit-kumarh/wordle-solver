from collections import Counter, defaultdict
from scipy.stats import entropy
from wordfreq import word_frequency as freq
from tqdm import tqdm
import itertools
import numpy as np
import json
import typer
from typing import List
import pprint
import pathlib
from amitkh_wordle import utils

app = typer.Typer()
PATTERNS = list(itertools.product(range(3), repeat=5))

# TODO: Incorporate word weight scoring. Translate in Spanish

def get_sorted_words():
    '''
    Sorts all words in word list by frequency according to wordfreq module
    '''
    words = utils.get_words()
    raw_freqs = {word: freq(word, 'en') for word in words}
    sorted_words = sorted(raw_freqs, key= lambda x: raw_freqs[x])
    return sorted_words
    
def gen_weights(width=10, cutoff=2500):
    '''
    Calculate probability of each word in the wordlist of being a wordle answer.
    This calculation is done by applying a sigmoid function with the
    cutoff being the 3000 most frequent words.

    Args:
        width (int): the width on which to place the words (in other words, the
                sharpness of the sigmoid transition

        cutoff (int): The midpoint of the function where the probability is 1/2

    Returns:
        weights (dict): dictionary mapping each word to the probability
    '''
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

@app.command()
def gen_pattern_dict(compress: bool=typer.Option(True, help='Compress patterns file from 800MB to 200MB at the expense of read/write time')):
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
    path = pathlib.Path(__file__).parent.resolve()
    words = utils.get_words()
    pattern_dict = defaultdict(lambda: defaultdict(set))
    for word in tqdm(words[:10]):
        for word2 in words:
            pattern = make_pattern(word, word2)
            pattern_dict[word][pattern].add(word2)
    pattern_dict = dict(pattern_dict)
    if compress:
        utils.compress_pickle(path / 'patterns.pbz2', pattern_dict)
    else:
        utils.reg_pickle(path / 'patterns.p', pattern_dict)

def calc_entropies(guesses, rem_words, pattern_dict, weights):
    '''
    Calculate dictionary of entropy in pattern distribution for each possible
    guess given rem_words remaining words with the probability for each word
    being a Wordle answer in weights.

    Args:
        guesses (set): list of all possible guesses
        rem_words (set): list of all remaining answer candidates
        pattern_dict (dict): dictionary connecting words and patterns, created
            by gen_pattern_dict()
        weights (dict): dictionary mapping each word to probability of being an
            answer

    Returns:
        entropies (dict): Maps each potential guess to entropy of it's pattern
            distribution
    '''
    entropies = {}
    for guess in tqdm(guesses):
        # Calculate entropy of distribution for how many possible remaining words will exist from all 243 patterns
        cnt = []
        for pattern in PATTERNS:
            matches = pattern_dict[guess][pattern]
            matches = matches.intersection(rem_words)
            cnt.append(sum(weights[match] for match in matches)/len(rem_words))
        entropies[guess] = entropy(cnt, base=2)
    return entropies

def get_probs(rem_words, weights):
    rem_weight_sum = sum(v for k, v in weights.items() if k in rem_words)
    return {word: weights[word]/rem_weight_sum for word in rem_words}

def entropy_to_score(ent):
    min_score = 2**(-ent) + 2 * (1 - 2**(-ent))
    return min_score + 1.5 * ent / 11.5

def get_expected_scores(rem_words, words, entropies, weights):
    probs = get_probs(rem_words, weights)
    rem_entropy = entropy(list(probs.values()), base=2)

    scores = {}
    for word in words:
        scores[word] = probs.get(word, 0) + (1-probs.get(word, 0)) * (1 + entropy_to_score(rem_entropy - entropies[word]))
    return scores

def optimal_guess(rem_words, words, entropies, weights, num=1):
    scores = get_expected_scores(rem_words, words, entropies, weights) 
    sorted_scores = sorted(list(scores.items()), key=lambda x: x[1])
    return sorted_scores[:num]

def play_game(ans, words, pattern_dict, weights, savetime=True):
    words = set(words)
    rem_words = words.copy()
    init = 1

    # Save time for bulk calculations since the first guess will always be the same
    if savetime:
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
            guess = optimal_guess(rem_words, words, entropies, weights, 1)[0][0]

        # Reduce the remaining words to those that match the new pattern 
        pattern = make_pattern(guess, ans)
        rem_words = rem_words.intersection(pattern_dict[guess][pattern])
        
        # Some console output
        if not savetime:
            typer.echo(f'Guess #{i}: {guess}')
            typer.echo(f'Given info {pattern}')
            typer.echo(f'Exp. Entropy: {round(entropies[guess], 3)}')
            if len(rem_words) < 100:
                typer.echo(rem_words)

        if guess == ans:

            # Game is won
            typer.echo(f'Guessed {ans} in {i} guesses')
            break

    return i

@app.command()
def test_all(of_name: str=typer.Argument('stats.json', help='Where to save results')):
    '''
    Run solver on all 2315 original wordle answers, writes JSON file with num
    of guesses for each word

    Args:
        of_name (str): where to write test results
    '''
    # Loading files
    words = utils.get_words()

    solutions = pkgutil.get_data(__name__, 'solutions.txt').decode('ascii').split('\n')
    pattern_dict = utils.get_pattern_dict()
    weights = gen_weights()

    # Playing all 2315 possible games
    stats = {}
    for sol in tqdm(solutions):
        stats[sol] = wordle.play_game(sol, words, pattern_dict, weights)

    # Writing output to JSON
    with open(of_name, 'w') as of:
        json.dump(stats, of)

@app.command()
def play_words(answers: List[str]):
    '''
    Simlulate a list of Wordle words
    '''
    typer.echo('Loading wordlist...')
    words = utils.get_words()
    typer.echo('Loading pattern dictionary (may take up to two minutes)...')
    pattern_dict = utils.get_pattern_dict()
    typer.echo('Generating frequency weights...')
    weights = gen_weights()
    for ans in answers:
        play_game(ans, words, pattern_dict, weights, False)

@app.command()
def play():
    typer.echo('Loading wordlist...')
    words = utils.get_words()
    typer.echo('Loading pattern dictionary (may take up to two minutes)...')
    pattern_dict = utils.get_pattern_dict()
    typer.echo('Generating frequency weights...')
    weights = gen_weights()

    words = set(words)
    rem_words = words.copy()

    for i in range(1, 11):
        entropies = calc_entropies(words, rem_words, pattern_dict, weights)
        probs = get_probs(rem_words, weights)
        best_guesses = optimal_guess(rem_words, words, entropies, weights, 10)
        display_guesses = [(w[0], round(best_guesses[i][1], 3), round(entropies[w[0]], 3), round(probs.get(w[0], 0), 3)) for i, w in enumerate(best_guesses)]
        display_guesses.insert(0, ('Word', 'Expected Score', 'Entropy', 'Probability of being correct'))
        if len(rem_words) > 1:
            typer.echo(f'{len(rem_words)} words are remaining. Top guesses are:')
            typer.echo(pprint.pformat(display_guesses))
        guess = ''
        while guess not in words:
            guess = typer.prompt('Guess:\n>')

        # Reduce the remaining words to those that match the new pattern 
        pattern = ''
        while (len(pattern)) != 5 or (not pattern.isnumeric()):
            pattern = typer.prompt('What was your pattern? (Green=2, Yellow=1, Grey=0)\n>')
        pattern = tuple(int(i) for i in pattern)
        rem_words = rem_words.intersection(pattern_dict[guess][pattern])
        
        if pattern == (2, 2, 2, 2, 2):
            typer.echo(f'Congratulations! You won in {i} guesses')
            raise typer.Exit()

        if len(rem_words) < 20:
            typer.echo('Remaining words are:')
            typer.echo(pprint.pformat([(word, round(weights[word], 4)) for word in rem_words]))

    raise typer.Exit()



if __name__ == '__main__':
    app()
