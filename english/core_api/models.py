from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator
import re

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

    # Social & Availability
    is_online = models.BooleanField(default=False)
    is_dnd = models.BooleanField(default=False)
    friends = models.ManyToManyField(User, blank=True, related_name='friends_set')

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
            # XP is now ONLY awarded for completion/quiz, not time spent
            xp_to_add = 0

            # Rule: Completion or Quiz score present gives XP
            if self.quiz_score is not None:
                # Every completed section awards 5 XP as per current requirements
                xp_to_add = 5
            
            # Special case for Speaking/CallLogs if needed (usually handled separately 
            # or via activity log with high score)
            
            try:
                if hasattr(self.student, 'profile'):
                    profile = self.student.profile
                    profile.total_xp += xp_to_add
                    if self.activity_type == 'LISTENING': profile.listening_xp += xp_to_add
                    elif self.activity_type == 'SPEAKING': profile.speaking_xp += xp_to_add
                    elif self.activity_type == 'READING': profile.reading_xp += xp_to_add
                    elif self.activity_type == 'WRITING': profile.writing_xp += xp_to_add
                    elif self.activity_type == 'LEARNING': profile.learning_xp += xp_to_add
                    
                    if self.activity_type == 'LEARNING' and self.quiz_score and self.quiz_score >= 70:
                        profile.unlocked_chapter += 1
                        
                    profile.save()
            except Exception:
                pass 
        super().save(*args, **kwargs)

def generate_next_student_id():
    """Finds the highest NAT-XXXX ID and increments it."""
    # Try to find the highest existing ID formatted as NAT-XXXX
    # This queries all profiles and finds the one with the highest string value
    # which works well for zero-padded strings like NAT-0001
    last_profile = StudentProfile.objects.filter(student_id__startswith='NAT-').order_by('-student_id').first()
    
    if last_profile:
        match = re.search(r'NAT-(\d+)', last_profile.student_id)
        if match:
            try:
                last_num = int(match.group(1))
                return f"NAT-{(last_num + 1):04d}"
            except ValueError:
                pass
    
    return "NAT-0001"

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """Creates a profile for new users or ensures one exists for old users."""
    if created:
        StudentProfile.objects.create(
            user=instance, 
            student_id=generate_next_student_id()
        )
    else:
        if not hasattr(instance, 'profile'):
            StudentProfile.objects.get_or_create(
                user=instance, 
                defaults={'student_id': generate_next_student_id()}
            )
        else:
            instance.profile.save()


@receiver(post_save, sender=StudentProfile)
def sync_user_permissions(sender, instance, **kwargs):
    """
    Syncs StudentProfile.is_approved with User.is_active.
    Also ensures students handled via this profile never gain admin perms.
    """
    # We use .update() to avoid triggering the User.post_save signal recursively
    User.objects.filter(id=instance.user.id).update(
        is_active=instance.is_approved,
        is_staff=False,
        is_superuser=False
    )