from django.db import models

class ListeningLesson(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]

    title = models.CharField(max_length=100)
    youtube_url = models.URLField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    xp_reward = models.IntegerField(default=5)
    
    def __str__(self):
        return f"[{self.level}] {self.title}"

class ListeningQuestion(models.Model):
    OPTION_CHOICES = [(0, 'Option 1'), (1, 'Option 2'), (2, 'Option 3')]
    
    lesson = models.ForeignKey(ListeningLesson, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    correct = models.IntegerField(choices=OPTION_CHOICES, default=0)

    def __str__(self):
        return f"Q: {self.text[:50]}..."
