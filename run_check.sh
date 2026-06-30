#!/bin/bash
# Progress check wrapper for crontab
# Runs check_progress.py and logs output

cd /Users/mai/CascadeProjects/get-stock-data
/usr/bin/env python3 check_progress.py >> /Users/mai/CascadeProjects/get-stock-data/.windsurf_context/command_logs/check_progress_cron.log 2>&1
