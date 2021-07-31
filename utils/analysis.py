import logging

logger = logging.getLogger(__name__)


def mean(arr):
    return sum(arr) / len(arr)


def analyze(test_params, ticker_summary):
    """
    Run some quick statistical analysis based on configuraiton file
    :param test_params: contains parameters to evaluate
    :param ticker_summary: result of a BacktestEngine test-run based on the same test_params configuration
    """

    if "analyze" in test_params:
        for detail in test_params["analyze"]:
            stratname = detail["strategy"]
            params = detail["params"]

            logger.info("Statistics strategy {}".format(stratname))

            for p in params:
                buckets_perf = {}
                buckets_drawdown = {}
                param_val_list = []

                # Do bucketing of summary results based on param list
                for ticker, summary in ticker_summary.items():
                    for perf, drawdown, netval, id, strat in summary:
                        if strat.params["strategy"] == stratname:
                            param_val = strat.params[p]
                            if param_val not in buckets_perf:
                                buckets_perf[param_val] = []
                                buckets_drawdown[param_val] = []
                                param_val_list.append(param_val)
                            buckets_perf[param_val].append(perf)
                            buckets_drawdown[param_val].append(drawdown)

                # Print stats
                param_val_list.sort()
                for pv in param_val_list:
                    avg_perf = mean(buckets_perf[pv])
                    avg_drawdown = mean(buckets_drawdown[pv])
                    logger.info("{} val {} avg_performance {} avg_maxdrawdown {}".format(p, pv, avg_perf, avg_drawdown))

