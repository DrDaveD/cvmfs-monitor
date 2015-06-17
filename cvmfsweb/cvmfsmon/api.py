from django.conf.urls   import url
from tastypie.resources import ModelResource
from tastypie           import fields
from cvmfsmon.models    import Stratum0, Stratum1, Repository

class Stratum0Resource(ModelResource):
    class Meta:
        resource_name   = 'stratum0'
        queryset        = Stratum0.objects.all()
        allowed_methods = [ 'get' ]


class Stratum1Resource(ModelResource):
    repositories = fields.ManyToManyField('cvmfsmon.api.RepositoryResource', 'repository_set', null=True)

    class Meta:
        resource_name   = 'stratum1'
        detail_uri_name = 'alias'
        queryset        = Stratum1.objects.all()
        allowed_methods = [ 'get' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<alias>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class RepositoryResource(ModelResource):
    stratum0  = fields.ForeignKey(Stratum0Resource, 'stratum0')
    stratum1s = fields.ManyToManyField(Stratum1Resource, 'stratum1s', null=True)

    class Meta:
        resource_name   = 'repository'
        detail_uri_name = 'fqrn'
        queryset        = Repository.objects.all()
        allowed_methods = [ 'get' ]

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<fqrn>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

