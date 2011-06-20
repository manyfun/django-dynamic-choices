from django.db import models
from django.db.models.manager import Manager
from django.db.models.query import EmptyQuerySet
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from dynamic_choices.db.models import DynamicChoicesForeignKey, DynamicChoicesManyToManyField

ALIGNMENT_EVIL = 0
ALIGNMENT_GOOD = 1
ALIGNMENT_NEUTRAL = 2

ALIGNMENTS = (
    (ALIGNMENT_EVIL, 'Evil'),
    (ALIGNMENT_GOOD, 'Good'),
    (ALIGNMENT_NEUTRAL, 'Neutral'),
)

def alignment_display(alignment):
    field = Puppet._meta.get_field('alignment')
    return force_unicode(dict(field.flatchoices).get(int(alignment), alignment), strings_only=True)

class SameAlignmentManager(Manager):
    
    def get_query_set(self, alignment=None):
        return super(SameAlignmentManager, self).get_query_set().filter(alignment=alignment)

class Master(models.Model):
    
    alignment = models.SmallIntegerField(choices=ALIGNMENTS)
    
    def __unicode__(self):
        return u"%s master (%d)" % (self.get_alignment_display(), self.pk)

class Puppet(models.Model):
    
    alignment = models.SmallIntegerField(choices=ALIGNMENTS)
    master = DynamicChoicesForeignKey(Master, manager=SameAlignmentManager())
    secret_lover = DynamicChoicesForeignKey('self',
                                            related_name='secret_lover_set',
                                            blank=True, null=True)
    friends = DynamicChoicesManyToManyField('self', choices='choices_for_friends', blank=True, null=True)
    enemies = DynamicChoicesManyToManyField('self', through='Enemy', symmetrical=False, blank=True, null=True)
    
    def choices_for_friends(self, queryset, id=None, alignment=None):
        """
            Make sure our friends share our alignment or are neutral
        """
        same_alignment = queryset.filter(alignment=alignment).exclude(id=id)
        if alignment in (None, ALIGNMENT_NEUTRAL):
            return same_alignment
        else:
            return (
                        (alignment_display(alignment), same_alignment),
                        ('Neutral', queryset.filter(alignment=ALIGNMENT_NEUTRAL))
                    )
    
    def __unicode__(self):
        return u"%s puppet (%d)" % (self.get_alignment_display(), self.id)

class Enemy(models.Model):
    
    puppet = DynamicChoicesForeignKey(Puppet)
    enemy = DynamicChoicesForeignKey(Puppet, choices='choices_for_enemy', related_name='bob')
    because_of = DynamicChoicesForeignKey(Master, choices='choices_for_because_of', related_name='becauses_of')
    since = models.DateField()
    
    def choices_for_because_of(self, queryset, enemy__alignment=None):
        return queryset.filter(alignment=enemy__alignment)
    
    def choices_for_enemy(self, queryset, puppet__alignment=None):
        """
            Filter our enemies
        """
        if puppet__alignment is None:
            return EmptyQuerySet()
        else:
            choices = []
            for alignment in ALIGNMENTS:
                value, display = alignment
                if value != puppet__alignment:
                    choices.append((_(display), queryset.filter(alignment=value)))
            return tuple(choices)
