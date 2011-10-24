import urllib
import urllib2

from threadless_router.backends.base import BackendBase


EXAMPLE_URL = 'http://127.0.0.1/'
DEFAULT_OUTGOING_IDENTITY_PARAM = "identity"
DEFAULT_OUTGOING_TEXT_PARAM = "text"

class HttpBackend(BackendBase):

    def send(self, message):
        self.info('Sending message: %s' % message)
        outgoing_identity = self.b_config.get("outgoing_identity", DEFAULT_OUTGOING_IDENTITY_PARAM)
        outgoing_text = self.b_config.get("outgoing_text", DEFAULT_OUTGOING_TEXT_PARAM)
        url = self.b_config.get('outgoing_url', EXAMPLE_URL)
        data = {outgoing_text: message.text,
                outgoing_identity: message.connection.identity}
        try:
            self.debug('Opening URL: %s' % url)
            response = urllib2.urlopen(url, urllib.urlencode(data))
        except Exception, e:
            self.exception(e)
            return False
        self.info('SENT')
        self.debug('response: %s' % response.read())
        return True
