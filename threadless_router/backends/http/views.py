from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic.edit import FormMixin, ProcessFormView
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rapidsms.log.mixin import LoggerMixin

from threadless_router.base import incoming
from threadless_router.backends.http.forms import HttpForm


class BaseHttpBackendView(FormMixin, LoggerMixin, ProcessFormView):

    http_method_names = ['post']
    conf = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(BaseHttpBackendView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.backend_name = kwargs.get('backend_name')
        if self.conf is None:
            self.conf = settings.INSTALLED_BACKENDS[self.backend_name]
        return super(BaseHttpBackendView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.debug('form is valid')
        incoming(self.backend_name, **form.get_incoming_data())
        return HttpResponse('OK')

    def form_invalid(self, form):
        self.debug('form failed to validate')
        errors = dict((k, v[0]) for k, v in form.errors.items())
        self.debug(unicode(errors))
        return HttpResponseBadRequest('form failed to validate')


class SimpleHttpBackendView(BaseHttpBackendView):

    form_class = HttpForm

    def get_form_kwargs(self):
        kwargs = super(SimpleHttpBackendView, self).get_form_kwargs()
        kwargs.update({
            'identity': self.conf.get('incoming_identity', 'identity'),
            'text': self.conf.get('incoming_text', 'text'),
        })
        return kwargs

"""
This class is intended to allow an HTTP backend to use either GET
or POST when accepting HTTP requests.

The parameters must all be GET parameters if a GET request is used,
or all be POST parameters if a POST request is used.

The names of the expected request parameters can be specified in 
localsettings.py as "incoming_identity" and "incoming_text". For example:

INSTALLED_BACKENDS = {
    ...
    "http_backend": {
        "ENGINE": "threadless_router.backends.http.outgoing",
        ...
        "incoming_identity": "snr",
        "incoming_text": "msg"
    }
    ...
}

If "incoming_identity" is not specified, it is defaulted to "identity".
If "incoming_text" is not specified, it is defaulted to "text".

"""
class GetOrPostHttpBackendView(View):

    # Restrict requests to use only GET or POST; all other request methods will return a 405
    http_method_names = ["get","post"]

    """
    Allow POST requests to be csrf exempt.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(GetOrPostHttpBackendView, self).dispatch(*args, **kwargs)

    """
    On a GET request, call handle_incoming to handle the request.
    """
    def get(self, request, *args, **kwargs):
        return self.handle_incoming(request, *args, **kwargs)

    """
    On a POST request, call handle_incoming to handle the request.
    """
    def post(self, request, *args, **kwargs):
        return self.handle_incoming(request, *args, **kwargs)

    """
    This method does the handling of the request for both GET and POST requests.
    """
    def handle_incoming(self, request, *args, **kwargs):
        # Get backend name and load configuration settings
        backend_name = kwargs.get("backend_name")
        conf = settings.INSTALLED_BACKENDS[backend_name]
        
        # Retrieve parameter names for identity and text from configuration, or default them if not present
        identity_param_name = conf.get("incoming_identity", "identity")
        text_param_name = conf.get("incoming_text", "text")
        
        # Retrieve identity and text
        request_params = None
        if request.method == "GET":
            request_params = request.GET
        else:
            request_params = request.POST
        
        identity = request_params.get(identity_param_name, "")
        text = request_params.get(text_param_name, "")
        
        # If identity or text are not specified, return a 400, otherwise process request
        if identity == "" or text == "":
            return HttpResponseBadRequest("Insufficient Parameters")
        else:
            incoming(backend_name, identity, text)
            return HttpResponse("OK")

