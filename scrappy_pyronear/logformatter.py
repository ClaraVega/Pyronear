from scrapy.logformatter import LogFormatter
from twisted.internet.error import TimeoutError, TCPTimedOutError
from twisted.internet.defer import TimeoutError as DeferTimeoutError
from twisted.web.client import ResponseNeverReceived

class SilentTimeoutLogFormatter(LogFormatter):
    def download_error(self, failure, request, spider):
        # Ignore timeouts: aucun log émis pour ces erreurs
        if failure.check(TimeoutError, TCPTimedOutError, ResponseNeverReceived, DeferTimeoutError):
            return None
        return super().download_error(failure, request, spider)