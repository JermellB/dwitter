from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_delete


def get_sentinel_user():
    users = get_user_model().objects
    return users.get_or_create(username='[deleted]', is_active=False)[0]


@receiver(pre_delete, sender=User)
def soft_delete_user_dweets(instance, **kwargs):
    for dweet in Dweet.objects.filter(author=instance):
        dweet.delete()


class NotDeletedDweetManager(models.Manager):
    def get_queryset(self):
        base_queryset = super(NotDeletedDweetManager, self).get_queryset()
        return base_queryset.filter(deleted=False)


class Dweet(models.Model):
    code = models.TextField()
    posted = models.DateTimeField(db_index=True)
    reply_to = models.ForeignKey("self", on_delete=models.DO_NOTHING,
                                 null=True, blank=True)

    likes = models.ManyToManyField(User, related_name="liked")
    hotness = models.FloatField(default=1.0, db_index=True)
    deleted = models.BooleanField(default=False)

    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user),
                               null=True, blank=True)

    objects = NotDeletedDweetManager()
    with_deleted = models.Manager()

    def delete(self):
        self.deleted = True
        self.save()

    def __unicode__(self):
        return 'd/' + str(self.id) + ' (' + self.author.username + ')'

    class Meta:
        ordering = ('-posted',)

    def __str__(self):
        model_name = self.__class__.__name__
        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))
        return f"{model_name}({fields_str})"


class Comment(models.Model):
    text = models.TextField()
    posted = models.DateTimeField()
    reply_to = models.ForeignKey(Dweet, on_delete=models.CASCADE,
                                 related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __unicode__(self):
        return ('c/' +
                str(self.id) +
                ' (' +
                self.author.username +
                ') to ' +
                str(self.reply_to))

    class Meta:
        ordering = ('-posted',)

    def __str__(self):
        model_name = self.__class__.__name__
        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))
        return f"{model_name}({fields_str})"
