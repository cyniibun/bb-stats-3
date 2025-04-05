# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.schedule_utils import fetch_schedule_by_date
from datetime import datetime, timedelta

import warnings
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")

print("⏰ Preloading MLB schedule for today and tomorrow...")

for offset in range(2):  # Today and tomorrow
    target_date = datetime.utcnow().date() + timedelta(days=offset)
    fetch_schedule_by_date(datetime.combine(target_date, datetime.min.time()), force_refresh=True)
