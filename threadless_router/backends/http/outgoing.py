import urllib
import urllib2

from threadless_router.backends.base import BackendBase


EXAMPLE_URL = 'http://127.0.0.1/'
DEFAULT_OUTGOING_IDENTITY_PARAM = "identity"
DEFAULT_OUTGOING_TEXT_PARAM = "text"
DEFAULT_OUTGOING_ADDITIONAL_PARAMS = {}
DEFAULT_OUTGOING_METHOD = "POST"

class HttpBackend(BackendBase):

    def send(self, message):
        self.info('Sending message: %s' % message)
        outgoing_identity = self.b_config.get("outgoing_identity", DEFAULT_OUTGOING_IDENTITY_PARAM)
        outgoing_text = self.b_config.get("outgoing_text", DEFAULT_OUTGOING_TEXT_PARAM)
        outgoing_method = self.b_config.get("outgoing_method", DEFAULT_OUTGOING_METHOD)
        url = self.b_config.get('outgoing_url', EXAMPLE_URL)
        outgoing_params = self.b_config.get("outgoing_additional_params", DEFAULT_OUTGOING_ADDITIONAL_PARAMS)
        outgoing_params[outgoing_text] = message.text
        outgoing_params[outgoing_identity] = message.connection.identity
        try:
            self.debug('Opening URL: %s' % url)
            response = None
            parameter_list = urllib.urlencode(outgoing_params)
            if outgoing_method == "GET":
                response = urllib2.urlopen(url + "?" + parameter_list)
            else:
                response = urllib2.urlopen(url, parameter_list)
        except Exception, e:
            self.exception(e)
            return False
        self.info('SENT')
        self.debug('response: %s' % response.read())
        return True
