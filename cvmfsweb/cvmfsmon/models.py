from django.db import models

import cvmfs
import urlparse

class Stratum(models.Model):
    name  = models.CharField('Human readable name of the stratum provider', max_length=100)
    url   = models.URLField('Base URL for the stratum provider')
    alias = models.CharField('Textual identifier', max_length=20)
    level = models.IntegerField('Type of the Stratum 1 (0 or 1)')

    class Meta:
        unique_together = (('alias', 'level',),)  # every alias can have up to
                                                  # one stratum 0 AND stratum 1

    def __unicode__(self):
        return "%s (Stratum %d - %s)" % ( self.name , self.level , self.alias )

    def get_base_url(self):
        return urlparse.urlunparse(urlparse.urlparse(self.url))

    def make_endpoint(self, fqrn):
        return '/'.join([ self.get_base_url(), fqrn ])

    def connect_to(self, fqrn):
        return cvmfs.open_repository(self.make_endpoint(fqrn))

    def is_stratum0(self):
        return self.level == 0

    def is_stratum1(self):
        return self.level == 1


class Repository(models.Model):
    name                = models.CharField('Human readable name of the Repository', max_length=100)
    fqrn                = models.CharField('Fully qualified repository name',       max_length=100)
    project_url         = models.URLField('Project Website',                        max_length=255, blank=True)
    project_description = models.TextField('Project Description',                   blank=True)

    stratum0  = models.ForeignKey(Stratum,      related_name='stratum0')
    stratum1s = models.ManyToManyField(Stratum, related_name='stratum1s')

    def __unicode__(self):
        return self.name + " (" + self.fqrn + ")"
