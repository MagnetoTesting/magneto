import logging
import coloredlogs

Logger = logging.getLogger('Magneto')

# Initialize coloredlogs.
coloredlogs.install(level=logging.DEBUG,
                    show_timestamps=False,
                    show_hostname=False,
                    show_name=False)
