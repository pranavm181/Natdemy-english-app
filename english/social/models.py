from django.db import models
from django.contrib.auth.models import User

class CallLog(models.Model):
    CALL_TYPES = [('AI', 'Gemini AI'), ('FRIEND', 'Friend')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls')
    contact_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    duration_seconds = models.IntegerField(default=0)
    recording_file = models.FileField(upload_to='recordings/')
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # XP is now flat 5 for session completion, not duration-based
            xp_to_add = 5
            try:
                if hasattr(self.student, 'profile'):
                    profile = self.student.profile
                    profile.total_xp += xp_to_add
                    profile.speaking_xp += xp_to_add
                    profile.save()
            except Exception:
                pass
        super().save(*args, **kwargs)

class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

class SpeakingTopic(models.Model):
    LEVEL_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('PROFESSIONAL', 'Professional'),
    ]
    text = models.CharField(max_length=500)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='BEGINNER')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] {self.text[:50]}..."

class ActiveCall(models.Model):
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_calls')
    topic = models.ForeignKey(SpeakingTopic, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Active" if self.is_active else "Ended"
        return f"{self.caller.username} -> {self.receiver.username} ({status})"
