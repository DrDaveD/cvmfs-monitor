from django.conf.urls    import url
from tastypie.resources  import Resource, ModelResource
from tastypie            import fields, http
from tastypie.bundle     import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from cvmfsmon.models     import Stratum, Repository
from tastypie.utils      import trailing_slash


class Stratum1Resource(ModelResource):
    repositories = fields.ManyToManyField('cvmfsmon.api.RepositoryResource', 'stratum1s', null=True)

    class Meta:
        resource_name   = 'stratum1'
        detail_uri_name = 'alias'
        queryset        = Stratum.objects.filter(level=1)
        allowed_methods = [ 'get' ]
        excludes        = [ 'id' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<alias>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class EndpointResource(ModelResource):
    class Meta:
        resource_name   = 'endpoint'
        detail_uri_name = 'fqrn'
        queryset        = Stratum.objects.all()
        allowed_methods = [ 'get' ]
        fields          = [ 'endpoint' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/stratum(?P<level>[\d]+)/(?P<alias>[\w\d_.-]+)/(?P<fqrn>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def dehydrate(self, bundle):
        bundle.data['endpoint'] = bundle.obj.make_endpoint(bundle.obj.fqrn)
        return bundle

    def resource_uri_kwargs(self, bundle_or_obj=None):
        kwargs = super(EndpointResource, self).resource_uri_kwargs(bundle_or_obj)
        is_bundle = isinstance(bundle_or_obj, Bundle)
        obj = bundle_or_obj if not is_bundle else bundle_or_obj.obj
        kwargs['alias'] = obj.alias
        kwargs['level'] = obj.level
        return kwargs

    def obj_get(self, bundle, **kwargs):
        fqrn = kwargs['fqrn']
        del kwargs['fqrn']
        stratum = super(EndpointResource, self).obj_get(bundle, **kwargs)
        stratum.fqrn = fqrn
        return stratum

    def obj_get_list(self, bundle, **kwargs):
        raise ImmediateHttpResponse(response=http.HttpBadRequest())


class RepositoryResource(ModelResource):
    endpoints = fields.ManyToManyField(EndpointResource, attribute=lambda bundle: RepositoryResource._wrap_endpoints(bundle), null=True, full=True)

    class Wrapper:
        def __init__(self, list):
            self.list = list
        def all(self):
            return self.list

    @staticmethod
    def _wrap_endpoints(bundle):
        stratums = []
        for s in Stratum.objects.filter(level=1):
            s.fqrn = bundle.obj.fqrn
            stratums.append(s)
        return RepositoryResource.Wrapper(stratums)

    class Meta:
        resource_name   = 'repository'
        detail_uri_name = 'fqrn'
        queryset        = Repository.objects.all()
        allowed_methods = [ 'get' ]
        excludes        = [ 'id' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<fqrn>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
