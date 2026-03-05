from django.db import models

class Chapter(models.Model):
    order = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    grammar_rule_malayalam = models.TextField()
    level = models.CharField(
        max_length=20, 
        choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')], 
        default='BEGINNER'
    )
    xp_reward = models.IntegerField(default=5)

    def __str__(self):
        return f"Chapter {self.order}: {self.title}"

class GrammarExample(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='examples')
    english_text = models.CharField(max_length=500)
    malayalam_explanation = models.CharField(max_length=500)
    is_backup = models.BooleanField(default=False)

class GrammarQuiz(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='quizzes')
    question_text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.IntegerField(help_text="Index 0-3")
