import datetime
import json
import logging
from typing import Any

with open("./config/user_vars.json", "r") as uvf:
    USER_VARS = json.load(uvf) 

with open("./config/sys_vars.json", "r") as svf:
    SYS_VARS = json.load(svf)
