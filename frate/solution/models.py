from django.db import models


class SolutionAttempt(models.Model):
    version = models.ForeignKey('Version', on_delete=models.CASCADE, related_name='solution_attempts')
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='solution_attempts')
    changed = models.ManyToManyField('Slot', related_name='solution_attempts')

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f'{self.version} {self.created_by} {self.created}'
