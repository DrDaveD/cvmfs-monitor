from django.conf.urls    import url
from tastypie.resources  import Resource, ModelResource
from tastypie            import fields, http
from tastypie.bundle     import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils      import trailing_slash

from cvmfsmon.models     import Stratum, Repository
from cvmfs               import Availability


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

    def _dehydrate_optional_field(self, bundle, field_name):
        obj = bundle.obj
        if hasattr(obj, field_name):
            bundle.data[field_name] = getattr(obj, field_name)


    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data['endpoint'] = obj.make_endpoint(bundle.obj.fqrn)
        self._dehydrate_optional_field(bundle, 'revision')
        self._dehydrate_optional_field(bundle, 'last_replication')
        self._dehydrate_optional_field(bundle, 'health')
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

        if bundle.request.repo_status:
            RepositoryResource._append_stratum1_status(bundle.obj, stratums)

        return RepositoryResource.Wrapper(stratums)

    @staticmethod
    def _append_stratum1_status(repo, stratum1s):
        stratum0 = repo.stratum0.connect_to(repo.fqrn)
        avail = Availability(stratum0)
        for s1 in stratum1s:
            s1repo              = s1.connect_to(repo.fqrn)
            s1.revision         = s1repo.manifest.revision
            s1.last_replication = s1repo.last_replication
            s1.health           = avail.get_stratum1_health_score(s1repo)

    class Meta:
        resource_name   = 'repository'
        detail_uri_name = 'fqrn'
        queryset        = Repository.objects.all()
        allowed_methods = [ 'get' ]
        excludes        = [ 'id' ]

    def dispatch_status_detail(self, request, **kwargs):
        request.repo_status = True
        return self.dispatch_detail(request, **kwargs)

    def dispatch_bare_detail(self, request, **kwargs):
        request.repo_status = False
        return self.dispatch_detail(request, **kwargs)

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if isinstance(bundle_or_obj, Bundle) and \
            bundle_or_obj.request.repo_status:
            url_name = 'api_dispatch_status_detail'
            try:
                return self._build_reverse_url(
                                url_name,
                                kwargs=self.resource_uri_kwargs(bundle_or_obj))
            except NoReverseMatch:
                return ''
        else:
            return super(RepositoryResource, self).get_resource_uri(bundle_or_obj,
                                                                    url_name)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<fqrn>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_bare_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<fqrn>[\w\d_.-]+)/status/$" % self._meta.resource_name, self.wrap_view('dispatch_status_detail'), name="api_dispatch_status_detail"),
        ]
