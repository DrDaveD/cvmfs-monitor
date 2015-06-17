from django.conf.urls    import url
from tastypie.resources  import Resource, ModelResource
from tastypie            import fields, http
from tastypie.bundle     import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from cvmfsmon.models     import Stratum0, Stratum1, Repository
from tastypie.utils      import trailing_slash


class Stratum1Resource(ModelResource):
    repositories = fields.ManyToManyField('cvmfsmon.api.RepositoryResource', 'repository_set', null=True)

    class Meta:
        resource_name   = 'stratum1'
        detail_uri_name = 'alias'
        queryset        = Stratum1.objects.all()
        allowed_methods = [ 'get' ]
        excludes        = [ 'id' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<alias>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class RepositoryResource(ModelResource):
    stratum1s = fields.ManyToManyField(Stratum1Resource, 'stratum1s', null=True)

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


class EndpointStatus(object):
    def __init__(self, stratum=None, fqrn=None):
        if stratum and fqrn:
            self._stratum = stratum
            repo = self._stratum.connect_to(fqrn)
            self.__read_status(repo)

    def __read_status(self, repo):
        self.fqrn             = repo.manifest.repository_name
        self.revision         = repo.manifest.revision
        self.last_modified    = repo.manifest.last_modified
        self.whitelist_expiry = repo.retrieve_whitelist().expires
        self.endpoint         = repo.endpoint

    def make_endpoint_id(self):
        stratum0 = self._stratum.is_stratum0()
        kwargs = {}
        kwargs['stratum_type']  = 'stratum0' if stratum0 else 'stratum1'
        kwargs['stratum_alias'] = self._stratum.alias
        kwargs['fqrn']          = self.fqrn
        return kwargs


class EndpointStatusResource(Resource):
    fqrn             = fields.CharField(attribute='fqrn')
    revision         = fields.IntegerField(attribute='revision')
    last_modified    = fields.DateTimeField(attribute='last_modified')
    whitelist_expiry = fields.DateTimeField(attribute='whitelist_expiry')
    endpoint         = fields.CharField(attribute='endpoint')

    class Meta:
        resource_name   = 'endpoint'
        detail_uri_name = 'endpoint_definition'
        object_class    = EndpointStatus

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<stratum_type>[\w\d_.-]+)/(?P<fqrn>[\w\d_.-]+)/(?P<stratum_alias>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        is_bundle = isinstance(bundle_or_obj, Bundle)
        obj = bundle_or_obj.obj if is_bundle else bundle_or_obj
        return obj.make_endpoint_id()

    def obj_get(self, bundle, **kwargs):
        stratum_class = Stratum0 if   kwargs['stratum_type'] == 'stratum0' \
                                 else Stratum1
        stratum = stratum_class.objects.get(alias=kwargs['stratum_alias'])
        return EndpointStatus(stratum, kwargs['fqrn'])

    def obj_get_list(self, bundle, **kwargs):
        raise ImmediateHttpResponse(response=http.HttpBadRequest())

    def rollback(self, bundles):
        pass
