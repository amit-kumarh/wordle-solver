## Entropy based Wordle solver

CLI built with Typer. Based on [this](https://www.youtube.com/watch?v=v68zYyaEmEA) video from 3 Blue 1 Brown



## Installation
```
pip install amitkh-wordle
```
## Quick Start
1. The solver needs to generate a pattern dictionary containing all of the word and pattern combinations in order to run. To do this, run `wordle gen-pattern-dict`. This process will take around 10-15 minutes.
    1. By default the dictionary will be compressed using bz2 to about 200 MB. You can also specify the `--no-compress` option which will save the pickle without compression and will result in quicker load times, but take about 800 MB of storage .
2. To run the solver in interactive mode, run `wordle play`. This will be followed by roughly 2 minutes of setup time while the program loads in the pattern dictionary and calculates the initial guess.
3. After this, you will be presented with some information and prompted for a guess. The program will present you the top 10 guesses (though you can guess any word you would like), along with (from left to right) the expected score should you play that guess, the expected information that guess will provide in bits, and the probability that guess is the answer.
    1. If there are under 20 words remaining, the program will also print out those remaining words along with the probability that they are a potential answer based on frequency (which is not the same as the probability that they are the answer to this game).
4. From there, simply type in your guesses and the pattern that was returned to you according to the instructions, and repeat until solved.


