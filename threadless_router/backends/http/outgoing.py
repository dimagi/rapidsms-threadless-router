import urllib
import urllib2
import re
import traceback

from threadless_router.backends.base import BackendBase
from django.core.mail import EmailMessage


EXAMPLE_URL = 'http://127.0.0.1/'
DEFAULT_OUTGOING_IDENTITY_PARAM = "identity"
DEFAULT_OUTGOING_TEXT_PARAM = "text"
DEFAULT_OUTGOING_ADDITIONAL_PARAMS = {}
DEFAULT_OUTGOING_METHOD = "POST"

"""

Here is an example showing all of the configuration options available for the HttpBackend:

INSTALLED_BACKENDS = {
...
    "< backend name >": {
        "ENGINE": "threadless_router.backends.http.outgoing"
       ,"outgoing_url": < primary url of SMS gateway >
       ,"outgoing_identity": < optional, default 'identity'; name of the parameter which the SMS gateway expects to represent the destination mobile number >
       ,"outgoing_text": < optional, default 'text'; name of the parameter which the SMS gateway expects to represent the text of the SMS >
       ,"outgoing_additional_params": < optional, default empty; a dictionary of additional name-value pairs to send to SMS gateway on each request >
       ,"outgoing_method": < optional, default 'POST'; method to use for requests to the gateway (GET or POST) >
       ,"incoming_identity": < optional, default 'identity'; name of the parameter which the SMS gateway will send to represent source mobile number >
       ,"incoming_text": < optional, default 'text'; name of the parameter which the SMS gateway will send to represent the text of the SMS >
       ,"failover_urls": < optional, default empty; list of urls to use if outgoing_url is not reachable - the urls will be tried in the order given until one gets through >
       ,"error_email_recipients": < optional, default empty; list of recipients for exception emails - if empty, no email is sent if exceptions are raised when communicating with SMS gateway >
       ,"success_response_regex": < optional, default None; if specified, responses from the SMS gateway will be validated against this regular expression and an email notification will go out if a match is not made - note that failover does not occur if the reply does not match since the backend was able to reach the gateway >
    },
...
}

Note that for exception email functionality to work, email settings must also be configured in django. For example:
EMAIL_USE_TLS
EMAIL_HOST
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_PORT

"""

class HttpBackend(BackendBase):

    """
    Sends an email alert with the given message body to the recipients 
    defined in the configuration.
    """
    def send_email_alert(self, body_text):
        try:
            error_email_recipients = self.b_config.get("error_email_recipients", None)
            subject_text = "Threadless Router Backend '" + self.name + "' Error"
            if error_email_recipients is not None:
                email = EmailMessage (
                    subject = subject_text
                   ,body = body_text
                   ,to = error_email_recipients
                )
                email.send()
        except Exception, e:
            # Log email exceptions but prevent them from bubbling
            self.exception(e)
            pass

    def send(self, message):
        self.info('Sending message: %s' % message)
        outgoing_identity = self.b_config.get("outgoing_identity", DEFAULT_OUTGOING_IDENTITY_PARAM)
        outgoing_text = self.b_config.get("outgoing_text", DEFAULT_OUTGOING_TEXT_PARAM)
        outgoing_method = self.b_config.get("outgoing_method", DEFAULT_OUTGOING_METHOD)
        outgoing_url = self.b_config.get('outgoing_url', EXAMPLE_URL)
        outgoing_params = self.b_config.get("outgoing_additional_params", DEFAULT_OUTGOING_ADDITIONAL_PARAMS)
        outgoing_params[outgoing_text] = message.text
        outgoing_params[outgoing_identity] = message.connection.identity
        parameter_list = urllib.urlencode(outgoing_params)
        success_response_regex = self.b_config.get("success_response_regex", None)
        if success_response_regex is not None:
            success_response_regex = re.compile(success_response_regex)
        
        # Build list of urls to use to send the SMS; outgoing_url is kept as a separate url
        # to maintain backwards-compatibility with previous versions of the threadless router
        url_list = self.b_config.get("failover_urls", [])
        url_list.insert(0, outgoing_url)
        
        # Try each url until one is reachable
        for url in url_list:
            try:
                self.debug('Opening URL: %s' % url)
                response = None
                
                # Send the request
                if outgoing_method == "GET":
                    response = urllib2.urlopen(url + "?" + parameter_list)
                else:
                    response = urllib2.urlopen(url, parameter_list)
                
                # If the request succeeded but the response matches the error response regex, then
                # send a notification email.
                response_body = response.read()
                self.info('SENT')
                self.debug('response: %s' % response_body)
                if success_response_regex is not None:
                    if success_response_regex.match(response_body):
                        self.info("Success regex matched")
                    else:
                        self.info("Success regex not matched")
                        body_text = "Error response received from url " + url + " : " + response_body
                        self.send_email_alert(body_text)
                return True
            except Exception, e:
                # Log the exception and send an email alert
                self.exception(e)
                body_text = "Exception raised when accessing url '" + url + "': " + traceback.format_exc()
                self.send_email_alert(body_text)
        return False

