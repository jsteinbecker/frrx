from django.db import models
from django.contrib.auth.models import User
from frate.models import Employee



class ProfileVerificationToken(models.Model):
    """
    Model for storing the verification token for the user profile
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token',
                                null=True, blank=True)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='verification_token',
                                    editable=False)
    token = models.CharField(max_length=16, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_token_created_by')
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.employee} Verification Token'

    class Meta:
        verbose_name = 'Profile Verification Token'
        verbose_name_plural = 'Profile Verification Tokens'

        permissions = (
            ('can_view', 'Can view Profile Verification Tokens'),
            ('can_create', 'Can create Profile Verification Tokens'),
        )



