from django.dispatch import receiver
from django.db.models.signals import post_save
import random
import datetime
from .models import ProfileVerificationToken


@receiver(post_save, sender=ProfileVerificationToken)
def create_profile_verification_token(sender, instance, created, **kwargs):
    """
    Create a verification token for the user profile
    """
    if created and instance.created_by.is_superuser:
        token = random.randint(10000, 99999)
        prefix = instance.employee.initials
        instance.token = f'{prefix}{token}'
        instance.expires_at = datetime.datetime.now() + datetime.timedelta(days=1)
        instance.save()




