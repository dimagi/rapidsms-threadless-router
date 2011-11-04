from django.conf.urls.defaults import *

from threadless_router.backends.http import views


urlpatterns = patterns('',
    url(r"^(?P<backend_name>[\w-]+)/$", views.GetOrPostHttpBackendView.as_view(),
        name='get-or-post-http'),
)
