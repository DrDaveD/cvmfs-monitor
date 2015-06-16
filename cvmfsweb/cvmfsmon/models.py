from django.db import models

class Stratum0(models.Model):
    name = models.CharField('Human readable name of the Stratum0 provider', max_length=100)
    url  = models.URLField('Base URL for the Stratum Server')

    def __unicode__(self):
        return self.name


class Stratum1(models.Model):
    name  = models.CharField('Human readable name of the stratum 1 provider', max_length=100)
    url   = models.URLField('Base URL for the stratum 1 provider')
    alias = models.CharField('Textual identifier', max_length=20, unique=True)

    def __unicode__(self):
        return self.name


class Repository(models.Model):
    name                = models.CharField('Human readable name of the Repository', max_length=100)
    fqrn                = models.CharField('Fully qualified repository name',       max_length=100)
    project_url         = models.URLField('Project Website',                        max_length=255, blank=True)
    project_description = models.TextField('Project Description',                   blank=True)

    stratum0  = models.ForeignKey(Stratum0)
    stratum1s = models.ManyToManyField(Stratum1)

    def __unicode__(self):
        return self.name + " (" + self.fqrn + ")"
