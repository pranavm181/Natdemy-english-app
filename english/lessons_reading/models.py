from django.db import models

class ReadingStory(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]

    title = models.CharField(max_length=200)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    story_content = models.TextField()
    background_image_url = models.URLField()
    xp_reward = models.IntegerField(default=5)

    def __str__(self):
        return self.title

class ReadingQuestion(models.Model):
    OPTION_CHOICES = [(0, 'Option 1'), (1, 'Option 2'), (2, 'Option 3')]
    
    story = models.ForeignKey(ReadingStory, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    correct = models.IntegerField(choices=OPTION_CHOICES, default=0)

    def __str__(self):
        return f"Q: {self.text[:50]}..."
