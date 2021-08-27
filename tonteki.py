import multiprocessing
import offsuit
import suited
from functools import reduce
from itertools import combinations


def evaluate(pattern):
    """
    Evaluates a hand composed of seven cards.

    Args:
        pattern (int): A 52-bit bit pattern that represents seven cards.
                       Note that the number of ON bits must be definitely seven.
                       For example, the following bit pattern means a combination of K♣ 3♣ A♦ Q♡ J♡ 2♡ J♠.
                               ♣      |      ♦      |      ♡      |      ♠
                         AKQJT98765432_AKQJT98765432_AKQJT98765432_AKQJT98765432
                       0b0100000000010_1000000000000_0011000000001_0001000000000 = 0x4014000c02200
    Returns:
        int: The strength of the given hand, expressed as a 7462 resolution value. Smaller value means stronger hand.
             Two different hands may have the same value since only the best five cards matter.

                1 -   10: Straight flush
               11 -  166: Four of a kind
              167 -  322: Full house
              323 - 1599: Flush
             1600 - 1609: Straight
             1610 - 2467: Three of a kind
             2468 - 3325: Two pair
             3326 - 6185: One pair
             6186 - 7462: High card
    """
    octet = 0
    value = 9999
    for i in range(0, 52, 13):  # goes around 4 times
        o, v = suited.TABLE[(pattern >> i) & 0x1fff]
        octet += o
        value = min(v, value)
    res = min(offsuit.TABLE[octet], value)
    return res


def _define_bit_positions(codes, suits):
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    for i, suit in enumerate(suits):
        for j, rank in enumerate(ranks):
            codes[rank + suit] = i * 13 + j


_POS = {}
_define_bit_positions(_POS, ['♠', '♡', '♢', '♣'])
_define_bit_positions(_POS, ['♤', '♥', '♦', '♧'])


def _make_bit_pattern(*args):
    pattern = 0
    for arg in args:
        cards = str.join(' ', arg) if isinstance(arg, list) else arg
        for card in cards.split():
            pattern |= 1 << _POS[card]
    return pattern


def _all_possibilities(mask, r):
    return [sum(x) for x in combinations([1 << i for i in range(52) if ((1 << i) & mask) == 0], r)]


def _judge_winners(ranks):
    best = 9999
    winners = []
    for i, rank in enumerate(ranks):
        if rank < best:
            winners = [i]
            best = rank
        elif rank == best:
            winners.append(i)
    return winners


def _func(present_patterns, future_patterns):
    sums = [0] * len(present_patterns)
    for future in future_patterns:
        ranks = [evaluate(present | future) for present in present_patterns]
        winners = _judge_winners(ranks)
        for i in winners:
            sums[i] += 1 / len(winners)
    return sums


def calculate_equity(active_hands, mucked_hands, board):
    """
    Calculates showdown equity for each active hand on the given situation.

    Args:
        active_hands ([str]): A list of card pairs. e.g) ["A♠ K♢", "6♢ 6♣"]
                              The length of the list here must be two or more.
        mucked_hands ([str]): A list of card pairs. e.g) ["7♡ 2♠", "8♣ Q♢", "T♡ 5♣"]
                              These cards will be excluded from the possibility since they are no more in the deck.
                              Give an empty list even if no cards mucked.
        board (str): A space-separated string that represents 0/3/4/5 cards. e.g) "T♣ A♡ 9♠"
                     Give an empty string even if no cards on the board.
    Returns:
        [float]: A list of values between 0.0 and 1.0 that means showdown equity for each active hand.
    """
    present_patterns = [_make_bit_pattern(hand, board) for hand in active_hands]
    mask_pattern = _make_bit_pattern(active_hands, mucked_hands, board)
    future_patterns = _all_possibilities(mask_pattern, 5 - len(board.split()))

    sums = _func(present_patterns, future_patterns)
    return [sum / len(future_patterns) for sum in sums]


def _chunk(list_, d):
    n = len(list_)
    s = 0
    for i in range(d):
        e = (i + 1) * n // d
        yield list_[s:e]
        s = e


def calculate_equity_in_parallel(active_hands, mucked_hands, board):
    """
    Works completely same as calculate_equity() except trying multi-processing.
    """
    present_patterns = [_make_bit_pattern(hand, board) for hand in active_hands]
    mask_pattern = _make_bit_pattern(active_hands, mucked_hands, board)
    future_patterns = _all_possibilities(mask_pattern, 5 - len(board.split()))

    cpu_count = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(cpu_count)
    args = [(present_patterns, chunked) for chunked in _chunk(future_patterns, cpu_count)]
    results = pool.starmap(_func, args)

    n = len(active_hands)
    sums = reduce(lambda a, b: [a[i] + b[i] for i in range(n)], results, [0] * n)
    return [sum / len(future_patterns) for sum in sums]
