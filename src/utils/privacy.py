import logging
import re


class PrivacyFilter(logging.Filter):
    """
    Filter that masks IP addresses and localhost in log messages.
    Supports IPv4, IPv4:PORT, and host='...' formats.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        
        # 1. Mask IPv4 with optional port: 127.0.0.1:8008 -> [RESTRICTED]
        msg = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?\b", "[RESTRICTED]", msg)
        
        # 2. Mask host='127.0.0.1' or host="127.0.0.1" (aiohttp specific)
        msg = re.sub(r"host=['\"]\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}['\"]", "host=[RESTRICTED]", msg)
        
        # 3. Mask Google Project IDs / Identifiers (10-12 digit numbers)
        # Avoid masking Discord IDs (18-19 digits) by bounding the length.
        msg = re.sub(r"\b\d{10,12}\b", "[RESTRICTED_ID]", msg)
        msg = re.sub(r"project\s+[0-9]+", "project [RESTRICTED_ID]", msg)

        # 4. Mask localhost and 127.0.0.1 literally just in case regex misses boundaries
        msg = msg.replace("localhost", "[RESTRICTED]").replace("127.0.0.1", "[RESTRICTED]")
        
        record.msg = msg

        # Also mask in formatted message and arguments if they exist
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    arg = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?\b", "[RESTRICTED]", arg)
                    arg = arg.replace("localhost", "[RESTRICTED]").replace("127.0.0.1", "[RESTRICTED]")
                new_args.append(arg)
            record.args = tuple(new_args)

        return True
