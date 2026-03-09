from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator
import re

# --- GLOBAL XP CONFIG ---

class GlobalXPConfig(models.Model):
    """
    Singleton-style config for XP thresholds and rewards.
    """
    # Overall Level Thresholds
    overall_intermediate = models.IntegerField(default=1000)
    overall_professional = models.IntegerField(default=5000)
    
    # Section Level Thresholds
    section_intermediate = models.IntegerField(default=200)
    section_professional = models.IntegerField(default=1000)
    
    # Points awarded per activity completion (Legacy Default)
    points_per_activity = models.IntegerField(default=5)
    
    # Granular Defaults
    listening_beginner_xp = models.IntegerField(default=5)
    listening_intermediate_xp = models.IntegerField(default=10)
    listening_professional_xp = models.IntegerField(default=15)
    
    speaking_beginner_xp = models.IntegerField(default=5)
    speaking_intermediate_xp = models.IntegerField(default=10)
    speaking_professional_xp = models.IntegerField(default=15)
    
    reading_beginner_xp = models.IntegerField(default=5)
    reading_intermediate_xp = models.IntegerField(default=10)
    reading_professional_xp = models.IntegerField(default=15)
    
    writing_beginner_xp = models.IntegerField(default=5)
    writing_intermediate_xp = models.IntegerField(default=10)
    writing_professional_xp = models.IntegerField(default=15)
    
    learning_beginner_xp = models.IntegerField(default=5)
    learning_intermediate_xp = models.IntegerField(default=10)
    learning_professional_xp = models.IntegerField(default=15)
    
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"XP Config (Last updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

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

    def check_completion_for_level(self, level_name):
        """
        Checks if the student has completed all content for a specific level 
        across Listening, Reading, Writing, and Grammar.
        """
        from lessons_listening.models import ListeningLesson
        from lessons_reading.models import ReadingStory
        from lessons_writing.models import WritingTask
        from lessons_learning.models import Chapter
        from .models import ActivityLog

        # 1. Get total counts for each section at this level
        total_listening = ListeningLesson.objects.filter(level=level_name).count()
        total_reading = ReadingStory.objects.filter(level=level_name).count()
        total_writing = WritingTask.objects.filter(level=level_name).count()
        total_learning = Chapter.objects.filter(level=level_name).count()

        # If no content exists for this level, consider it "completed" to avoid getting stuck
        if total_listening == 0 and total_reading == 0 and total_writing == 0 and total_learning == 0:
            return True

        # 2. Get completed counts for this student
        # We use unique item_id to ensure they can't game it by doing the same lesson twice
        completed_listening = ActivityLog.objects.filter(
            student=self.user, activity_type='LISTENING', quiz_score__gte=80  # Assuming 80% is passing
        ).values('item_id').distinct().count()

        completed_reading = ActivityLog.objects.filter(
            student=self.user, activity_type='READING', quiz_score__gte=80
        ).values('item_id').distinct().count()

        completed_writing = ActivityLog.objects.filter(
            student=self.user, activity_type='WRITING', quiz_score__gte=80
        ).values('item_id').distinct().count()

        completed_learning = ActivityLog.objects.filter(
            student=self.user, activity_type='LEARNING', quiz_score__gte=80
        ).values('item_id').distinct().count()

        # 3. Final Check
        return (
            completed_listening >= total_listening and
            completed_reading >= total_reading and
            completed_writing >= total_writing and
            completed_learning >= total_learning
        )

    @property
    def current_level(self):
        """Calculates level based on curriculum completion."""
        # Check if Beginner completed -> Move to Intermediate
        if self.check_completion_for_level('BEGINNER'):
            # Check if Intermediate completed -> Move to Professional
            if self.check_completion_for_level('INTERMEDIATE'):
                return 'PROFESSIONAL'
            return 'INTERMEDIATE'
        return 'BEGINNER'

    def get_section_level(self, xp=None):
        """
        Returns the universal academy level.
        Section-specific XP is now secondary to curriculum completion.
        """
        return self.current_level

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
    xp_earned = models.IntegerField(default=0, help_text="Specific XP earned for this activity")
    item_id = models.IntegerField(null=True, blank=True, help_text="ID of the lesson/chapter/story")
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # XP is now ONLY awarded for completion/quiz, not time spent
            xp_to_add = 0

            # Rule: Completion or Quiz score present gives XP
            if self.quiz_score is not None:
                if self.xp_earned > 0:
                    xp_to_add = self.xp_earned
                else:
                    # Resolve granular default from config
                    config = GlobalXPConfig.get_config()
                    profile = getattr(self.student, 'profile', None)
                    if profile:
                        # Get section level and resolve field name
                        xp_field = f"{self.activity_type.lower()}_xp"
                        current_section_xp = getattr(profile, xp_field, 0)
                        level = profile.get_section_level(current_section_xp)
                        config_field = f"{self.activity_type.lower()}_{level.lower()}_xp"
                        xp_to_add = getattr(config, config_field, config.points_per_activity)
                    else:
                        xp_to_add = config.points_per_activity
            
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
                        # Update state to point to next chapter
                        from .models import StudentState
                        state, _ = StudentState.objects.get_or_create(student=self.student)
                        state.last_activity_type = 'LEARNING'
                        state.last_item_id = profile.unlocked_chapter
                        state.save()
                        
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
    Ensures students stay students, but PROTECTS superusers/staff.
    """
    user = instance.user
    # If the user is a superuser or staff, we should NOT strip their permissions
    if user.is_superuser or user.is_staff:
        # We also ensure superusers are always "approved" in their profile
        if not instance.is_approved:
            StudentProfile.objects.filter(id=instance.id).update(is_approved=True)
        return
    # We use .update() to avoid triggering the User.post_save signal recursively
    User.objects.filter(id=instance.user.id).update(
        is_active=instance.is_approved,
        is_staff=False,
        is_superuser=False
    )
# --- STUDENT STATE (Persistent App State) ---

class StudentState(models.Model):
    """
    Stores 'live' app state, draft content, and last accessed items 
    to allow resuming from the last point.
    """
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='state')
    last_activity_type = models.CharField(max_length=20, blank=True, null=True)
    last_item_id = models.IntegerField(blank=True, null=True)
    live_data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State for {self.student.username}"

@receiver(post_save, sender=User)
def manage_student_state(sender, instance, created, **kwargs):
    """Ensures every user has a StudentState object."""
    if created:
        StudentState.objects.get_or_create(student=instance)
    else:
        if not hasattr(instance, 'state'):
            StudentState.objects.get_or_create(student=instance)
