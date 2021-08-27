
# Overview
Bothered with evaluating poker hands?

*Tonteki* is a very simple Python library that helps you calculate the strength from seven cards on Texas Hold'em.

*Tonteki* uses only 2.6MB lookup tables, so it could be installed in almost any environment, and you would be able to rewrite it in another language easily because of its simple implementation.

# Functions
*Tonteki* defines only two functions, no classes.

## `evaluate`
It is known that every poker hand can be expressed its strength with a 7462 resolution value. This function directly calculates that value from seven cards, so you don't need to pick up the best five cards from the seven, nor to sort cards in advance.

Instead, according to a given map, you need to create a 52-bit bit pattern that represents the seven cards. The following is an example.

``` Python
from tonteki import evaluate

#              AKQJT98765432_AKQJT98765432_AKQJT98765432_AKQJT98765432
x = evaluate(0b1000000000010_1000000000000_0011000000001_0001000000000)
print(x)  # returned 2491
```

The bit pattern above means a combination of `A♣ 3♣ A♦ Q♡ J♡ 2♡ J♠`, and returned 2491 means AJ two pair with a Q kicker.

Average execution time was 1.3μs (observed on author's local PC). This is enough fast for normal use, but a little unsatisfied for calculating showdown equity mentioned below.

## `calculate_equity`
You can also calculate showdown equity, which is often seen on poker tournament TV programs. The following is an example to calculate showdown equity of two players on pre-flop.

``` Python
from tonteki import calculate_equity

x = calculate_equity(['A♠ A♣', '7♡ 2♢'], [], '')
print(x)  # returned [0.8742244367822536, 0.12577556321774638]
```

This is the worst case in aspect of execution time because there are still 48 cards left in the deck. Here, the function `evaluate()` is called 3,424,608 (48C5 * 2) times, therefore it totally takes longer than 5 seconds to execute. Outside of a pre-flop situation, this execution time won't be a problem.

For those who cannot stand this execution time on pre-flop, I have prepared a parallel execution version `calculate_equity_in_parallel()`. This is worth a try if your environment matches.
