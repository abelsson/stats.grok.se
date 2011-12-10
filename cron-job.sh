#!/bin/sh

DIR=/home/henrik/wikistats/

cd $DIR

echo ./getstats.py --yesterday >> $DIR/cron.log
