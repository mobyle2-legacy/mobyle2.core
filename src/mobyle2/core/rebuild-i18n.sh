#!/usr/bin/env bash



domain="mobyle2"
cd $(dirname $0)/../../..
$INS/bin/pyramidpy setup.py  extract_messages
$INS/bin/pyramidpy setup.py  update_catalog -D $domain
$INS/bin/pyramidpy setup.py  compile_catalog -D $domain
# vim:set et sts=4 ts=4 tw=0:
