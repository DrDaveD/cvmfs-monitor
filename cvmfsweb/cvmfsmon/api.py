from tastypie.resources import ModelResource
from tastypie           import fields
from cvmfsmon.models    import Stratum0, Stratum1, Repository

class Stratum0Resource(ModelResource):
    class Meta:
        resource_name   = 'stratum0'
        queryset        = Stratum0.objects.all()
        allowed_methods = [ 'get' ]


class Stratum1Resource(ModelResource):
    class Meta:
        resource_name   = 'stratum1'
        queryset        = Stratum1.objects.all()
        allowed_methods = [ 'get' ]


class RepositoryResource(ModelResource):
    stratum0  = fields.ForeignKey(Stratum0Resource, 'stratum0')
    stratum1s = fields.ManyToManyField(Stratum1Resource, 'stratum1s')

    class Meta:
        resource_name   = 'repository'
        queryset        = Repository.objects.all()
        allowed_methods = [ 'get' ]
