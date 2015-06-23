from django.conf.urls import patterns, include, url

from cvmfsmon     import views
from tastypie.api import Api
from cvmfsmon.api import *

v1_api = Api(api_name='v1.0')
v1_api.register(StratumResource())
v1_api.register(RepositoryResource())
v1_api.register(EndpointResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),
)
