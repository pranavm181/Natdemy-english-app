from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator

# --- STUDENT PROFILE ---

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    student_id = models.CharField(max_length=20, unique=True)
    is_approved = models.BooleanField(default=False) 
    
    # Progress Data
    total_xp = models.IntegerField(default=0)
    listening_xp = models.IntegerField(default=0)
    speaking_xp = models.IntegerField(default=0)
    reading_xp = models.IntegerField(default=0)
    writing_xp = models.IntegerField(default=0)
    learning_xp = models.IntegerField(default=0)
    
    current_streak = models.IntegerField(default=0)
    daily_goal_minutes = models.IntegerField(default=20)
    unlocked_chapter = models.IntegerField(default=1)
    rank_percentage = models.FloatField(default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    profile_photo = models.ImageField(
        upload_to='profile_photos/', 
        null=True, 
        blank=True,
        default='profile_photos/default_user.png'
    )

    @property
    def current_level(self):
        """Calculates level based on total XP points"""
        if self.total_xp < 1000: return 'BEGINNER'
        elif self.total_xp < 5000: return 'INTERMEDIATE'
        else: return 'PROFESSIONAL'

    def get_section_level(self, xp):
        """Calculates level for a specific section based on its XP"""
        if xp < 200: return 'BEGINNER'
        elif xp < 1000: return 'INTERMEDIATE'
        else: return 'PROFESSIONAL'

    @property
    def listening_level(self): return self.get_section_level(self.listening_xp)

    @property
    def speaking_level(self): return self.get_section_level(self.speaking_xp)

    @property
    def reading_level(self): return self.get_section_level(self.reading_xp)

    @property
    def writing_level(self): return self.get_section_level(self.writing_xp)

    @property
    def learning_level(self): return self.get_section_level(self.learning_xp)

    def __str__(self):
        status = "✅" if self.is_approved else "⏳ Pending"
        return f"{self.user.username} ({self.current_level}) - {status}"

# --- LISTENING SECTION ---

class ListeningLesson(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]
    title = models.CharField(max_length=100)
    youtube_url = models.URLField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    
    q1_text = models.CharField(max_length=255)
    q1_options = models.JSONField(help_text="Format: ['Option1', 'Option2', 'Option3']")
    q1_correct = models.IntegerField(help_text="Index 0-2")

    q2_text = models.CharField(max_length=255)
    q2_options = models.JSONField()
    q2_correct = models.IntegerField()

    q3_text = models.CharField(max_length=255, blank=True, null=True, help_text="Backup for failures")
    q3_options = models.JSONField(blank=True, null=True)
    q3_correct = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"[{self.level}] {self.title}"

# --- LEARNING (CHAPTER) SECTION ---

class Chapter(models.Model):
    order = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    grammar_rule_malayalam = models.TextField()

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

# --- READING SECTION ---

class ReadingStory(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]
    title = models.CharField(max_length=200)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    story_content = models.TextField()
    background_image_url = models.URLField()

    q1_text = models.CharField(max_length=255)
    q1_options = models.JSONField()
    q1_correct = models.IntegerField()

    q2_text = models.CharField(max_length=255)
    q2_options = models.JSONField()
    q2_correct = models.IntegerField()

    q3_text = models.CharField(max_length=255)
    q3_options = models.JSONField()
    q3_correct = models.IntegerField()

# --- WRITING SECTION ---

class WritingTask(models.Model):
    LEVEL_CHOICES = [('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('PROFESSIONAL', 'Professional')]
    malayalam_meaning = models.CharField(max_length=500)
    correct_sentence = models.CharField(max_length=500)
    extra_words = models.CharField(max_length=200, blank=True, null=True, help_text="Comma separated words to confuse the user (e.g. 'is, are, was')")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

# --- SPEAKING & ACTIVITY LOGS ---

class ActivityLog(models.Model):
    ACTIVITY_CHOICES = [
        ('LISTENING', 'Listening'), ('SPEAKING', 'Speaking'), 
        ('LEARNING', 'Learning'), ('READING', 'Reading'), ('WRITING', 'Writing'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    duration_minutes = models.FloatField(default=0.0)
    quiz_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Base XP calculation
            xp_to_add = int(self.duration_minutes * 10)
            
            # Penalize for low quiz scores
            if self.quiz_score is not None:
                if self.quiz_score < 50:
                    xp_to_add = xp_to_add // 2 if self.quiz_score > 0 else 0
            
            try:
                # Direct check if profile exists to prevent RelatedObjectDoesNotExist
                if hasattr(self.student, 'profile'):
                    profile = self.student.profile
                    profile.total_xp += xp_to_add
                    
                    # Distribute to specific section
                    if self.activity_type == 'LISTENING': profile.listening_xp += xp_to_add
                    elif self.activity_type == 'SPEAKING': profile.speaking_xp += xp_to_add
                    elif self.activity_type == 'READING': profile.reading_xp += xp_to_add
                    elif self.activity_type == 'WRITING': profile.writing_xp += xp_to_add
                    elif self.activity_type == 'LEARNING': profile.learning_xp += xp_to_add
                    
                    # Automatically unlock next chapter if Learning session is passed (score > 70)
                    if self.activity_type == 'LEARNING' and self.quiz_score and self.quiz_score >= 70:
                        profile.unlocked_chapter += 1
                        
                    profile.save()
            except Exception:
                pass 
        super().save(*args, **kwargs)

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
            # Speaking earns more XP (15 per minute)
            xp_to_add = int((self.duration_seconds / 60) * 15)
            try:
                if hasattr(self.student, 'profile'):
                    profile = self.student.profile
                    profile.total_xp += xp_to_add
                    profile.speaking_xp += xp_to_add
                    profile.save()
            except Exception:
                pass
        super().save(*args, **kwargs)

# --- SIGNALS ---

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """Creates a profile for new users or ensures one exists for old users."""
    if created:
        StudentProfile.objects.create(
            user=instance, 
            student_id=f"NAT-{instance.id:04d}"
        )
    else:
        # For existing users, ensure profile is saved if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            StudentProfile.objects.get_or_create(
                user=instance, 
                defaults={'student_id': f"NAT-{instance.id:04d}"}
            )