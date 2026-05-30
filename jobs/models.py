from django.db import models
from users.models import User


class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    )

    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')

    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)

    salary_min = models.IntegerField()
    salary_max = models.IntegerField()

    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return self.title
