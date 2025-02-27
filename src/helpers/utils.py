from datetime import datetime
import inspect

def is_date(s: str):
    """Test if input string 's' is a timestamp 
    string
    Arg:
        s (str): String to test
    Return:
        True/ False depending on outcome
    """
    format_s = "%Y-%m-%dT%H:%M:%SZ"
    try:
        datetime.strptime(s, format_s)
        return True

    except:
        return False

def get_var_name(var):
    print('\n'.join(str(v) for v in inspect.currentframe().f_back.f_locals.items()))
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    for var_name, var_val in callers_local_vars:
        if var_val is var:
            return var_name