from django.db import models

class WritingTask(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]
    malayalam_meaning = models.CharField(max_length=500)
    correct_sentence = models.CharField(max_length=500)
    extra_words = models.CharField(max_length=200, blank=True, null=True, help_text="Comma separated words to confuse the user (e.g. 'is, are, was')")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    xp_reward = models.IntegerField(default=5)

    def __str__(self):
        return f"[{self.level}] {self.malayalam_meaning[:50]}"
