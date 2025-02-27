import datetime
import json
import logging
from typing import Any
from . import USER_VARS, SYS_VARS
from helpers import print_motion_graphics

USER_VAR_FILE = "./config/user_vars.json"
SYS_VAR_FILE = "./config/sys_vars.json"


def user_setup(init_setup: bool):
    """Function to setup user variables
    Args:
        init_setup (bool): is this the first setup?
    Returns:
        USER_VARS (dict): updated User Variables object
    """
    for key, value in USER_VARS.items():
        new_value = input(f"{key} ({value}):")
        if len(new_value) == 0:
            continue
        USER_VARS[key] = new_value

    _ = save_vars(user=True)
    
    if init_setup:
        SYS_VARS['FIRST_RUN'] = False
        _ = save_vars(sys=True)

    return USER_VARS


def save_vars(sys: bool = False, 
              user: bool = False):
    """Function to save current variable state.
    Args:
        sys (bool): Save System Variables
                    Default: False
        user (bool): Save User Variables
                    Default: False
    Returns:
        True: Success Mode
        False: Failure Mode - occurs on both Sys and user
                params being False
    """
    log_id = f"{__name__}.save_vars"
    if not any([sys, user]):
        logging.debug(f"""{log_id} | Nothing to save, exiting;
                      """)
        return False

    if sys:
        with open(SYS_VAR_FILE, "w") as svf:
            svf.write(json.dumps(SYS_VARS, indent=4, default=str))

    if user:
        with open(USER_VAR_FILE, "w") as svf:
            svf.write(json.dumps(USER_VARS, indent=4, default=str))
    
    return True


def set_var(var_key: str,
            var_value: Any):
    """Function to set a user variable value -
    immediately saves updated state to the user_vars.json
    config file.
    Args:
        var_key (str): Key of the variable to update
        var_value (str): New value of the variable to be set
    Returns:
        True: Success Mode 
    
    """
    log_id = f"{__name__}.set_var"
    if var_key not in USER_VARS.keys():
        logging.debug(f"{log_id} | {var_key} is not a valid user variable: {USER_VARS.keys()}")
    USER_VARS[var_key] = var_value
    save_vars(user=True)
    return True


def teardown():
    """Teardown script for config - saves the current time as 
    the session_endtime
    Args:
        None
    Returns
        session_endtime (str): End time of the session
    """
    log_id = f"{__name__}.teardown"
    session_endtime = datetime.datetime.now().strftime(SYS_VARS['DTFORMAT'])
    SYS_VARS['SESHEND'] = session_endtime
    save_vars(sys=True, user=True)
    logging.debug(f"{log_id} | Teardown Complete - session end {session_endtime}")
    return session_endtime


def show_vars(include_sys: bool = False):
    """Function to print out the User variables, and the System variables
    too with the right flag.
    Args:
        include_sys (bool): include system variables in readout
    Returns: True - Default Success Mode
    """
    print(
        json.dumps(
            USER_VARS,
            indent=4,
            default=str
        )
    )
    if include_sys:
        print(
            json.dumps(
                SYS_VARS,
                indent=4,
                default=str
            )
        )
