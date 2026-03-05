import os
import django
from django.conf import settings

# Setup Django environment
import sys
sys.path.append('c:/Users/aswin/OneDrive/Desktop/SKILL PARK/APPS/ENGLISH/english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'natdemy_english.settings')
django.setup()

from django.contrib.auth.models import User
from core_api.models import StudentProfile, ActivityLog

def check():
    print("Checking for user with student_id='test' or username='test'...")
    p_by_sid = StudentProfile.objects.filter(student_id='test').first()
    p_by_uname = StudentProfile.objects.filter(user__username='test').first()
    
    profile = p_by_sid or p_by_uname
    
    if not profile:
        print("User NOT found.")
        # List all students to help debug
        print("\nExisting Students:")
        for p in StudentProfile.objects.all()[:20]:
            print(f"- Username: {p.user.username}, ID: {p.student_id}, Approved: {p.is_approved}, XP: {p.total_xp}")
        return

    user = profile.user
    print(f"User Found: {user.username}")
    print(f"Student ID: {profile.student_id}")
    print(f"Is Approved: {profile.is_approved}")
    print(f"Total XP: {profile.total_xp}")
    print(f"Current Level: {profile.current_level}")
    
    print("\nSection XP:")
    print(f"- Listening: {profile.listening_xp} ({profile.listening_level})")
    print(f"- Speaking: {profile.speaking_xp} ({profile.speaking_level})")
    print(f"- Reading: {profile.reading_xp} ({profile.reading_level})")
    print(f"- Writing: {profile.writing_xp} ({profile.writing_level})")
    print(f"- Learning: {profile.learning_xp} ({profile.learning_level})")
    
    print("\nRecent Activity Logs:")
    logs = ActivityLog.objects.filter(student=user).order_by('-timestamp')[:10]
    for log in logs:
        print(f"- {log.timestamp}: {log.activity_type}, Duration: {log.duration_minutes}, Quiz: {log.quiz_score}")

if __name__ == "__main__":
    check()
