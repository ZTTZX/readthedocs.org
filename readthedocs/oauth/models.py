"""OAuth service models"""

import json

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.urlresolvers import reverse

from readthedocs.projects.constants import REPO_CHOICES
from readthedocs.projects.models import Project

from .constants import OAUTH_SOURCE
from .managers import RemoteRepositoryManager, RemoteOrganizationManager


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')


class RemoteOrganization(models.Model):

    """Organization from remote service

    This encapsulates both Github and Bitbucket
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_organizations')
    active = models.BooleanField(_('Active'), default=False)

    slug = models.CharField(_('Slug'), max_length=255, unique=True)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(_('Avatar image URL'), null=True, blank=True)
    url = models.URLField(_('URL to organization page'), max_length=200,
                          null=True, blank=True)

    source = models.CharField(_('Repository source'), max_length=16,
                              choices=OAUTH_SOURCE)
    json = models.TextField(_('Serialized API response'))

    objects = RemoteOrganizationManager()

    def __unicode__(self):
        return "Remote Organization: %s" % (self.url)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass


class RemoteRepository(models.Model):

    """Remote importable repositories

    This models Github and Bitbucket importable repositories
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # This should now be a OneToOne
    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_repositories')
    organization = models.ForeignKey(
        RemoteOrganization, verbose_name=_('Organization'),
        related_name='repositories', null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)

    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True,
                                   help_text=_('Description of the project'))
    avatar_url = models.URLField(_('Owner avatar image URL'), null=True,
                                 blank=True)

    ssh_url = models.URLField(_('SSH URL'), max_length=512, blank=True,
                              validators=[URLValidator(schemes=['ssh'])])
    clone_url = models.URLField(
        _('Repository clone URL'),
        max_length=512,
        blank=True,
        validators=[
            URLValidator(schemes=['http', 'https', 'ssh', 'git', 'svn'])])
    html_url = models.URLField(_('HTML URL'), null=True, blank=True)

    private = models.BooleanField(_('Private repository'), default=False)
    admin = models.BooleanField(_('Has admin privilege'), default=False)
    vcs = models.CharField(_('vcs'), max_length=200, blank=True,
                           choices=REPO_CHOICES)

    source = models.CharField(_('Repository source'), max_length=16,
                              choices=OAUTH_SOURCE)
    json = models.TextField(_('Serialized API response'))

    objects = RemoteRepositoryManager()

    class Meta:
        ordering = ['organization__name', 'name']

    def __unicode__(self):
        return "Remote importable repository: %s" % (self.html_url)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass

    def matches(self, user):
        """Projects that exist with repository URL already"""

        # TODO
        # ghetto_repo = self.clone_url.replace('git://', '').replace('.git', '')
        projects = (Project
                    .objects
                    .public(user)
                    .filter(repo=self.clone_url))
        #            .filter(Q(repo__endswith=ghetto_repo) |
        #                    Q(repo__endswith=ghetto_repo + '.git')))
        # if projects:
        #    repo.matches = [project.slug for project in projects]
        # else:
        #    repo.matches = []
        return [{'id': project.slug,
                 'url': reverse('projects_detail',
                                kwargs={'project_slug': project.slug})}
                for project in projects]