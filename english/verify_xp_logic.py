import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/aswin/OneDrive/Desktop/SKILL PARK/APPS/ENGLISH/english')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'natdemy_english.settings')
django.setup()

from django.contrib.auth.models import User
from core_api.models import StudentProfile, ActivityLog

def verify_logic():
    user = User.objects.get(username='test')
    profile = user.profile
    
    # Reset XP for clean test
    profile.total_xp = 0
    profile.listening_xp = 0
    profile.reading_xp = 0
    profile.writing_xp = 0
    profile.learning_xp = 0
    profile.speaking_xp = 0
    profile.unlocked_chapter = 1
    profile.save()
    
    print(f"Initial State: Level={profile.current_level}, XP={profile.total_xp}")
    
    # 1. Test XP Gain (5 XP per completion)
    print("\nSimulating 1 Listening activity with quiz...")
    ActivityLog.objects.create(student=user, activity_type='LISTENING', quiz_score=80)
    profile.refresh_from_db()
    print(f"Listening XP: {profile.listening_xp}, Total XP: {profile.total_xp}")
    
    # 2. Test Section Level Threshold (200 for INTERMEDIATE)
    print("\nSimulating 40 more Reading activities (200 XP)...")
    for _ in range(40):
        ActivityLog.objects.create(student=user, activity_type='READING', quiz_score=100)
    profile.refresh_from_db()
    print(f"Reading XP: {profile.reading_xp}, Reading Level: {profile.reading_level}")
    
    # 3. Test Overall Level Threshold (1000 for INTERMEDIATE)
    print("\nSimulating 160 more activities (800 XP, Total 1005)...")
    for _ in range(160):
        ActivityLog.objects.create(student=user, activity_type='WRITING', quiz_score=90)
    profile.refresh_from_db()
    print(f"Total XP: {profile.total_xp}, Overall Level: {profile.current_level}")
    
    # 4. Test Chapter Unlock (needs LEARNING and quiz >= 70)
    print(f"\nCurrent Chapter: {profile.unlocked_chapter}")
    print("Simulating Learning activity with score 85...")
    ActivityLog.objects.create(student=user, activity_type='LEARNING', quiz_score=85)
    profile.refresh_from_db()
    print(f"New Chapter: {profile.unlocked_chapter}")

if __name__ == "__main__":
    verify_logic()
