import json
import logging
import sys

from core.backtest_engine import BackTestEngine

logger = logging.getLogger(__name__)


def main():
    """
    Usage: backtest.py <backtest_config_filename>
    Example: backtest.py sample.json

    Where the file is a JSON file with strategy parameters to be back-tested
    Check sample.json as an example (used as default file if none provided)
    Check README.md for a more detailed explanation.
    """

    # Default strategy to backtest if no JSON file is provided
    filename = "sample.json"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    # Set up logging for the session.
    logging.basicConfig(filename='session.log', level=logging.DEBUG)

    test_params = None
    try:
        with open(filename) as f:
            test_params = json.load(f)
    except Exception as e:
        print("Sorry mate, something is wrong with your input file {}. {}".format(filename, e))
        print("Sorry mate, something is wrong with your input file {}. {}".format(filename, e))
        return

    # Create a session and configure the session.
    engine = BackTestEngine(test_params)

    # Run the session.
    engine.run()


if __name__ == "__main__":
    main()