from django.db import models
from users.models import User
from jobs.models import Job


class ApplicationStatus(models.TextChoices):
    PENDING = 'pending'
    REVIEWED = 'reviewed'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')

    resume = models.FileField(upload_to='applications/')
    cover_letter = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['-applied_at']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"
