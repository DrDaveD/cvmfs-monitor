from django.db import models

import cvmfs
import urlparse

class Stratum:
    def connect_to(self, fqrn):
        endpoint = urlparse.urljoin(self.get_base_url(), fqrn)
        return cvmfs.open_repository(endpoint)

    def is_stratum0(self):
        return False

    def is_stratum1(self):
        return False


class Stratum0(models.Model, Stratum):
    name  = models.CharField('Human readable name of the Stratum0 provider', max_length=100)
    url   = models.URLField('Base URL for the Stratum Server')

    def __unicode__(self):
        return self.name

    def get_base_url(self):
        return self.url

    def is_stratum0(self):
        return True


class Stratum1(models.Model, Stratum):
    name  = models.CharField('Human readable name of the stratum 1 provider', max_length=100)
    url   = models.URLField('Base URL for the stratum 1 provider')
    alias = models.CharField('Textual identifier', max_length=20, unique=True)

    def __unicode__(self):
        return self.name

    def get_base_url(self):
        return self.url

    def is_stratum1(self):
        return True


class Repository(models.Model):
    name                = models.CharField('Human readable name of the Repository', max_length=100)
    fqrn                = models.CharField('Fully qualified repository name',       max_length=100)
    project_url         = models.URLField('Project Website',                        max_length=255, blank=True)
    project_description = models.TextField('Project Description',                   blank=True)

    stratum0  = models.ForeignKey(Stratum0)
    stratum1s = models.ManyToManyField(Stratum1)

    def __unicode__(self):
        return self.name + " (" + self.fqrn + ")"
