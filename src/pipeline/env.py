import os
import zoneinfo


STREAMING_LOG_LEVEL = int(os.getenv("STREAMING_LOG_LEVEL", "30"))
FILE_LOG_LEVEL = int(os.getenv("FILE_LOG_LEVEL", "10"))
LOG_FILEPATH = os.getenv("LOG_FILEPATH", "./runtime.log")
# NOTE: Although LOG_FMT and LOG_DATEFMT are in env.py, we do not expect
#       them to be changed by environment variables. They define the logging
#       style of the project and should not be changed.
LOG_FMT = "%(asctime)s [%(name)s | %(levelname)s]: %(message)s"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%SZ"
TZ = zoneinfo.ZoneInfo(os.getenv("TZ", "UTC"))