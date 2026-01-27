import copy

from uvicorn.config import LOGGING_CONFIG


def get_privacy_log_config():
    """Returns a Uvicorn log config that hides client IP addresses."""
    config = copy.deepcopy(LOGGING_CONFIG)
    
    # Custom format that replaces client_addr with [RESTRICTED]
    # Default is: %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s
    new_format = '%(levelprefix)s [RESTRICTED] - "%(request_line)s" %(status_code)s'
    
    if "formatters" in config:
        if "access" in config["formatters"]:
            config["formatters"]["access"]["fmt"] = new_format
            
    return config
