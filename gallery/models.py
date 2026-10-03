from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    must_change_password = models.BooleanField(
        default=True,
    )
    can_manage_private = models.BooleanField(
        default=False,
    )


    def __str__(self):
        return self.user.username