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
and then keeps selling covered calls against it. On expiration, the options are bought back by the portfolio.



