import logging

from core.optionchain import OptionChain
from core.option import Option
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import *
from scipy.special import betainc, beta

logger = logging.getLogger(__name__)

PROB_TH = 0.01


def scatter(x, y, textx=None, texty=None, title=None, x2=None, y2=None):
    fig, ax = plt.subplots()
    plt.scatter(x, y)
    if textx:
        ax.set_xlabel(textx)
    if texty:
        ax.set_ylabel(texty)
    if title:
        ax.set_title(title)
    if x2:
        plt.scatter(x2, y2, marker='.')
    plt.draw()
    plt.waitforbuttonpress(0)
    plt.close()


def curve_fit_optim(x, scale, d1, d2):
    bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
    ba = d1 / 2
    bb = d2 / 2
    return betainc(ba, bb, bx)


def add_call_bull_spreads(sorted_calls, strikes, probs, D=2):
    N = len(sorted_calls)
    for i in range(1, N):
        strike1, op1 = sorted_calls[i]
        if op1.midprice() <= 1:
            # Premium is less than 0.01
            continue
        for j in range(max(0, i - D), i):
            strike0, op0 = sorted_calls[j]
            if op0.midprice() <= 1:
                # Premium is less than 0.01
                continue
            mid_strike = (strike0 + strike1) / 2

            bullspread_premium = (-op0.midprice() + op1.midprice()) / 100
            implied_prob = (bullspread_premium / (strike1 - strike0)) + 1

            if implied_prob < 0:
                implied_prob = 0
            if implied_prob > 1:
                implied_prob = 1
            # print(mid_strike, implied_prob, bullspread_premium)
            strikes.append(mid_strike)
            probs.append(implied_prob)
    return strikes, probs


def add_put_bull_spreads(sorted_puts, strikes, probs, D=2):
    N = len(sorted_puts)
    for i in range(0, N - 1):
        strike1, op1 = sorted_puts[i]
        if op1.midprice() <= 1:
            # Premium is less than 0.01
            continue
        for j in range(i + 1, min(N, i + D + 1)):
            strike0, op0 = sorted_puts[j]
            if op0.midprice() <= 1:
                # Premium is less than 0.01
                continue
            mid_strike = (strike0 + strike1) / 2

            bullspread_premium = (op0.midprice() - op1.midprice()) / 100
            implied_prob = - bullspread_premium / (strike1 - strike0)

            if implied_prob < 0:
                implied_prob = 0
            if implied_prob > 1:
                implied_prob = 1
            # print(mid_strike, implied_prob, bullspread_premium)
            strikes.append(mid_strike)
            probs.append(implied_prob)
    return strikes, probs


def get_RND_distribution(options: OptionChain):
    sorted_calls = options.get_sorted_calls()
    sorted_puts = options.get_sorted_puts()

    # New plan..
    strikes = []
    probs = []
    D = 2
    strikes, probs = add_call_bull_spreads(sorted_calls, strikes, probs, D=D)
    strikes, probs = add_put_bull_spreads(sorted_puts, strikes, probs, D=D)

    popt, _ = curve_fit(curve_fit_optim, strikes, probs)

    """
    For debugging purposes
    # Plot fitted cumulative curve
    fitted = [curve_fit_optim(s, *popt) for s in strikes]
    scatter(strikes, probs, x2=strikes, y2=fitted)
    print('COST F', sqdiffsum(fitted, probs))
    """

    return Distribution('F', popt)


def curve_fit_optim(x, scale, d1, d2):
    bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
    ba = d1 / 2
    bb = d2 / 2
    return betainc(ba, bb, bx)


def sqdiffsum(v1, v2):
    tot = 0
    for a, b, in zip(v1, v2):
        tot += (a - b) ** 2
    return tot * 100


class Distribution:
    def __init__(self, type, params):
        self.type = type
        self.params = [float(p) for p in params]
        self.mean_reference = self.get_mean()
        self.steps = 400
        self.min_strike = 0
        self.max_strike = 100000
        self.mean_shift = 0
        self.var_level = 1
        self.adjust_min_strike()
        self.adjust_max_strike()
        self.mean_shift_reference = (self.max_strike - self.min_strike)
        self.lut = {}
        self.problut = {}

    def solve_lower_bound(self, th):
        lower = 0
        upper = 10000
        while lower <= upper:
            mid = (lower + upper) / 2
            prob = self.get_cumulative(mid)
            if prob < th:
                lower = mid + 0.01
            else:
                upper = mid - 0.01
        return mid

    def solve_upper_bound(self, th):
        lower = 0
        upper = 10000
        while lower <= upper:
            mid = (lower + upper) / 2
            prob = self.get_cumulative(mid)
            if prob < 1 - th:
                lower = mid + 0.01
            else:
                upper = mid - 0.01
        return mid

    def adjust_min_strike(self):
        self.lut = {}
        self.problut = {}
        self.min_strike = self.solve_lower_bound(PROB_TH)

    def adjust_max_strike(self):
        self.lut = {}
        self.problut = {}
        self.max_strike = self.solve_upper_bound(PROB_TH)

    def set_mean_shift_level(self, level):
        self.lut = {}
        self.problut = {}
        amount = level * 0.02 * self.mean_shift_reference
        self.mean_shift = amount

    def set_var_shift_level(self, level):
        self.lut = {}
        self.problut = {}
        scale = 0.9 ** level
        self.var_level = scale

    def get_mean(self):
        if self.type == 'F':
            return (self.params[2] / (self.params[2] - 2)) * self.params[0]
        if self.type == 'FF':
            m1 = (self.params[2] / (self.params[2] - 2)) * self.params[0]
            m2 = (self.params[5] / (self.params[5] - 2)) * self.params[3]
            r = self.params[6]
            return r * m1 + (1 - r) * m2

    def get_cumulative(self, x):
        if x in self.lut:
            return self.lut[x]
        x = (x - self.mean_reference) * self.var_level + self.mean_reference + self.mean_shift
        if self.type == 'F':
            scale, d1, d2 = self.params
            bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
            ba = d1 / 2
            bb = d2 / 2
            self.lut[x] = betainc(ba, bb, bx)
            return self.lut[x]
        if self.type == 'FF':
            scale, d1, d2, scaleB, d1B, d2B, r = self.params
            bx = d1 * (x / scale) / (d1 * (x / scale) + d2)
            ba = d1 / 2
            bb = d2 / 2
            bx2 = d1B * (x / scaleB) / (d1B * (x / scaleB) + d2B)
            ba2 = d1B / 2
            bb2 = d2B / 2
            self.lut[x] = r * betainc(ba, bb, bx) + (1 - r) * betainc(ba2, bb2, bx2)
            return self.lut[x]

    def get_probability(self, x, strike_lower=0, strike_higher=10000):
        x_min = (strike_lower + x) / 2
        x_max = (strike_higher + x) / 2
        if self.type == 'F':
            prob = self.get_cumulative(x_max) - self.get_cumulative(x_min)
            return prob
        if self.type == 'FF':
            prob = self.get_cumulative(x_max) - self.get_cumulative(x_min)
            return prob

    def get_prob_arrays(self, steps=500, th_lower=0.01, th_upper=0.01, strike_min=None, strike_max=None):
        if strike_min is None:
            strike_min = self.solve_lower_bound(th_lower)
        if strike_max is None:
            strike_max = self.solve_upper_bound(th_upper)

        lut_key = (steps, strike_min, strike_max)
        if lut_key in self.problut:
            return self.problut[lut_key]

        strikes = np.arange(strike_min, strike_max, (strike_max - strike_min) / steps)
        prob_array, cum_array = [0], []
        for i in range(1, len(strikes) - 1):
            prob = self.get_probability(strikes[i], strikes[i - 1], strikes[i + 1])
            prob_array.append(prob)
            cum = self.get_cumulative(strikes[i]) - self.get_cumulative(strikes[i - 1])
            cum_array.append(cum)
        prob_array.append(0)

        # Save to look-up table
        self.problut[lut_key] = (strikes, prob_array, cum_array)
        return strikes, prob_array, cum_array

    def get_option_expected_return(self, o: Option):
        strikes, prob_array, cum_array = self.get_prob_arrays()

        expected_return = 0
        for st, pr in zip(strikes, prob_array):
            expected_return += pr * o.get_profit(st)

        return expected_return
