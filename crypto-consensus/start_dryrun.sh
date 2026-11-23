#!/bin/sh
set -eu
export PYTHONPATH=/freqtrade/crypto-consensus
export CRYPTO_PAPER_PAUSE_FILE=/freqtrade/runtime/PAUSE_ENTRIES
python /freqtrade/crypto-consensus/preflight_dryrun.py /freqtrade/crypto-consensus/config.alwayson.dry.json
echo "Starting ETH Kraken DRY-RUN only; simulated stops never placed on exchange"
exec freqtrade trade \
    --config /freqtrade/crypto-consensus/config.alwayson.dry.json \
    --strategy GuardedConsensusETH \
    --logfile /freqtrade/runtime/freqtrade.log
