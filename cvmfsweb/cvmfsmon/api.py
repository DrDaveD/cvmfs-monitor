from django.conf.urls    import url
from tastypie.resources  import Resource, ModelResource
from tastypie            import fields, http
from tastypie.bundle     import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils      import trailing_slash

from cvmfsmon.models     import Stratum, Repository
from cvmfs               import Availability


class StratumResource(ModelResource):
    repositories = fields.ManyToManyField('cvmfsmon.api.RepositoryResource', attribute=lambda bundle: StratumResource._populate_repositories(bundle), null=True)

    @staticmethod
    def _populate_repositories(bundle):
        if bundle.obj.level == 0:
            return Repository.objects.filter(stratum0=bundle.obj)
        else:
            return Repository.objects.filter(stratum1s=bundle.obj)

    class Meta:
        resource_name   = 'stratum'
        detail_uri_name = 'alias'
        queryset        = Stratum.objects.all()
        allowed_methods = [ 'get' ]
        excludes        = [ 'id', 'level' ]

    def detail_uri_kwargs(self, bundle_or_obj):
        is_bundle = isinstance(bundle_or_obj, Bundle)
        stratum = bundle_or_obj if not is_bundle else bundle_or_obj.obj
        kwargs = super(StratumResource, self).detail_uri_kwargs(bundle_or_obj)
        kwargs.update({
            'level' : stratum.level,
            'alias' : stratum.alias
        })
        return kwargs

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)(?P<level>\d+)/(?P<alias>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]




class Endpoint:
    def __init__(self, stratum = None, fqrn = '', status = False):
        if stratum:
            self.stratum  = stratum
            self.fqrn     = fqrn
            self.endpoint = stratum.make_endpoint(fqrn)
        if status:
            self._retrieve_status()

    def connect(self):
        if not hasattr(self, '_connection'):
            self._connection = self.stratum.connect_to(self.fqrn)
        return self._connection

    def _retrieve_status(self):
        connection = self.connect()
        self.revision = connection.manifest.revision
        self.last_replication = None
        if self.stratum.level > 0:
            self.last_replication = connection.last_replication
        self.last_modified = connection.manifest.last_modified


class EndpointResource(Resource):
    stratum          = fields.ForeignKey(StratumResource, attribute=lambda bundle: bundle.obj.stratum)
    fqrn             = fields.CharField(attribute='fqrn')
    endpoint         = fields.CharField(attribute='endpoint')
    revision         = fields.IntegerField(attribute='revision', null=True)
    last_modified    = fields.DateTimeField(attribute='last_modified', null=True)
    last_replication = fields.DateTimeField(attribute='last_replication', null=True)

    class Meta:
        resource_name   = 'endpoint'
        detail_uri_name = 'fqrn'
        object_class    = Endpoint

    def dehydrate(self, bundle):
        data = bundle.data
        if not bundle.request.repo_status:
            del data['revision']
            del data['last_modified']
            del data['last_replication']
        return bundle

    def obj_get(self, bundle, **kwargs):
        stratum_alias = kwargs['alias']
        stratum_level = kwargs['level']
        fqrn          = kwargs['fqrn']
        status        = bundle.request.repo_status
        stratum = Stratum.objects.filter(alias=stratum_alias,
                                         level=stratum_level).get()
        return Endpoint(stratum, fqrn, status)

    def detail_uri_kwargs(self, bundle_or_obj):
        is_bundle = isinstance(bundle_or_obj, Bundle)
        endpoint  = bundle_or_obj if not is_bundle else bundle_or_obj.obj
        kwargs = {
            'level' : endpoint.stratum.level,
            'alias' : endpoint.stratum.alias,
            'fqrn'  : endpoint.fqrn,
        }
        return kwargs

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
            return super(EndpointResource, self).get_resource_uri(bundle_or_obj,
                                                                  url_name)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/stratum(?P<level>[\d]+)/(?P<alias>[\w\d_.-]+)/(?P<fqrn>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_bare_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/stratum(?P<level>[\d]+)/(?P<alias>[\w\d_.-]+)/(?P<fqrn>[\w\d_.-]+)/status/$" % self._meta.resource_name, self.wrap_view('dispatch_status_detail'), name="api_dispatch_status_detail"),
        ]



class RepositoryResource(ModelResource):
    stratum1_endpoints = fields.ManyToManyField(EndpointResource, attribute=lambda bundle: RepositoryResource._get_stratum1_endpoints(bundle), null=True, full=True)
    stratum0_endpoint  = fields.ForeignKey(EndpointResource, attribute=lambda bundle:RepositoryResource._get_stratum0_endpoint(bundle), full=False)

    class Wrapper:
        def __init__(self, list):
            self.list = list
        def all(self):
            return self.list

    @staticmethod
    def _get_stratum1_endpoints(bundle):
        fqrn      = bundle.obj.fqrn
        status    = bundle.request.repo_status
        stratum1s = bundle.obj.stratum1s.all()
        endpoints = [ Endpoint(s1, fqrn, status) for s1 in stratum1s ]
        return RepositoryResource.Wrapper(endpoints)

    @staticmethod
    def _get_stratum0_endpoint(bundle):
        fqrn      = bundle.obj.fqrn
        status    = bundle.request.repo_status
        stratum0  = bundle.obj.stratum0
        return Endpoint(stratum0, fqrn, status)

    class Meta:
        resource_name   = 'repository'
        detail_uri_name = 'fqrn'
        queryset        = Repository.objects.all()
        allowed_methods = [ 'get' ]
        excludes        = [ 'id' ]

    def _dehydrate_redundant_fields(self, bundle):
        for s1_endpoint in bundle.data['stratum1_endpoints']:
            del s1_endpoint.data['fqrn']

    def _dehydrate_repo_status(self, bundle):
        s0_connection  = self.stratum0_endpoint.fk_resource.instance.connect()
        avail = Availability(s0_connection)
        for s1_endpoint_bundle in bundle.data['stratum1_endpoints']:
            s1_connection = s1_endpoint_bundle.obj.connect()
            avail.add_stratum1(s1_connection)
            health = avail.get_stratum1_health_score(s1_connection)
            s1_endpoint_bundle.data['health'] = health

        bundle.data['health'] = avail.get_repository_health_score()


    def dehydrate(self, bundle):
        self._dehydrate_redundant_fields(bundle)
        if bundle.request.repo_status:
            self._dehydrate_repo_status(bundle)
        return bundle

    def obj_get(self, bundle, **kwargs):
        return super(RepositoryResource, self).obj_get(bundle, **kwargs)

    def dispatch_status_detail(self, request, **kwargs):
        request.repo_status = True
        return self.dispatch_detail(request, **kwargs)

    def dispatch_bare_detail(self, request, **kwargs):
        request.repo_status = False
        return self.dispatch_detail(request, **kwargs)

    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if isinstance(bundle_or_obj, Bundle)             and \
           hasattr(bundle_or_obj.request, 'repo_status') and \
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
