# Installation & requirements
Python 3.5+, along with some additional requirements in the requrements.txt file.
Install it via `pip install -r requirements.txt`.

# Usage

From the main folder, simply do a `python backtest.py <backtestfile.json>`.

Check `sample.json` for a reference on how to set up a backtest file, or have a look at the strategy 
specific sample files in the `sample_jsons` folder. 

Logging is done to the local file `session.log`, also used for debugging purposes.

# Implemented strategies

This list should grow as new things are implemented :)
For each implemented strategy, there is a sample .json file with configurations in the `sample_jsons` folder.

The backtest allows for spawning multiple parallel strategies to be tested against each other, by specifying an 
array of strategies via the `strategies` keyword. For testing a single strategy, use the `strategy` keyword instead.

## BuyAndHold

Given a starting amount of cash, this strategy spends it all buying shares of the underlying (no options) 
and stays idle after that.

## CoveredCall

Given a starting amount of cash, this strategy spends it all buying shares of the underlying (no options),
and then keeps selling covered calls against it. On expiration, the options are rolled further out if they are ITM 
(rolling) or are allowed to expire worthless otherwise.

## LeveragedCoveredCall

A Covered Call strategy using deep ITM options as the long leg instead of owning stocks.
It imitates a poor man's covered call (PMCC): deep ITM call options for the long leg,
shorter expiry covered calls for the short leg.

Params:
1. longdte: DTE for the long option leg
1. longdelta: delta for the long option leg
1. shortdte: DTE for the short option leg
1. shortdelta: delta for the short option leg
1. closeonprofit: roll short leg given fraction of profit reached (0.7 -> close short leg when 70% profit reached)
1. creditroll: 1 to force rolling positions for credit, ignoring delta; 0 otherwise

## Wheel

Given a starting amount of cash, this strategy first writes cash secured puts (CSP), and if taking assignment of
the shares, switches to writing covered calls (CC). If the shares are called away, it switches back to writing CSP.

## RndStrategy

Pick an option chain of preferred DTE and run Risk Neutral Distribution (RND) calculation over it.
Based on the RND, place 5 orders with the highest profit percentage options.
Options are close out on expiry.

## DeltaNeutral

A semi-delta neutral strategy using a four legged strategy:
- long (large delta and DTE) Put + Call legs
- short (shorted delta and DTE)  Put + Call legs

Basically, calendar spreads where the long leg is delta neutral, while the short leg attempts to capture theta decay/ 
profits from short-term price fluctuations.
 
Params:
1. longdte: DTE for the long option leg
1. longdelta: delta for the long option leg
1. shortdte: DTE for the short option leg
1. shortdelta: delta for the short option leg
1. closeonprofit: roll short leg given fraction of profit reached (0.7 -> close short leg when 70% profit reached)
1. creditroll: 1 to force rolling positions for credit, ignoring delta; 0 otherwise