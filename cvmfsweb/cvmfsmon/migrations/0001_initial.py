# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Stratum0'
        db.create_table('cvmfsmon_stratum0', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('cvmfsmon', ['Stratum0'])

        # Adding model 'Stratum1'
        db.create_table('cvmfsmon_stratum1', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('alias', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
        ))
        db.send_create_signal('cvmfsmon', ['Stratum1'])

        # Adding model 'Repository'
        db.create_table('cvmfsmon_repository', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('fqrn', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('project_url', self.gf('django.db.models.fields.URLField')(max_length=255, blank=True)),
            ('project_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('stratum0', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cvmfsmon.Stratum0'])),
        ))
        db.send_create_signal('cvmfsmon', ['Repository'])

        # Adding M2M table for field stratum1s on 'Repository'
        m2m_table_name = db.shorten_name('cvmfsmon_repository_stratum1s')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('repository', models.ForeignKey(orm['cvmfsmon.repository'], null=False)),
            ('stratum1', models.ForeignKey(orm['cvmfsmon.stratum1'], null=False))
        ))
        db.create_unique(m2m_table_name, ['repository_id', 'stratum1_id'])


    def backwards(self, orm):
        # Deleting model 'Stratum0'
        db.delete_table('cvmfsmon_stratum0')

        # Deleting model 'Stratum1'
        db.delete_table('cvmfsmon_stratum1')

        # Deleting model 'Repository'
        db.delete_table('cvmfsmon_repository')

        # Removing M2M table for field stratum1s on 'Repository'
        db.delete_table(db.shorten_name('cvmfsmon_repository_stratum1s'))


    models = {
        'cvmfsmon.repository': {
            'Meta': {'object_name': 'Repository'},
            'fqrn': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'project_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'stratum0': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cvmfsmon.Stratum0']"}),
            'stratum1s': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cvmfsmon.Stratum1']", 'symmetrical': 'False'})
        },
        'cvmfsmon.stratum0': {
            'Meta': {'object_name': 'Stratum0'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'cvmfsmon.stratum1': {
            'Meta': {'object_name': 'Stratum1'},
            'alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['cvmfsmon']