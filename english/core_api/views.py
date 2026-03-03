import random
from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser

# Import all models
from .models import (
    StudentProfile, ActivityLog, ListeningLesson, 
    Chapter, ReadingStory, WritingTask, CallLog
)
from .serializers import StudentProfileSerializer, ActivityLogSerializer
from .permissions import IsApprovedStudent

class StudentViewSet(viewsets.ModelViewSet):
    """
    Handles Profile, Weekly Charts, Activity Logging, and Photo Updates.
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [IsApprovedStudent]
    # Added parsers to handle image uploads
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return StudentProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def weekly_analytics(self, request):
        last_7_days = timezone.now() - timedelta(days=7)
        activities = ActivityLog.objects.filter(
            student=request.user, 
            timestamp__gte=last_7_days
        )
        serializer = ActivityLogSerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def detailed_dashboard(self, request):
        """Returns comprehensive analytics for the student's progress"""
        profile = request.user.profile
        
        xp_sections = {
            "Listening": profile.listening_xp,
            "Speaking": profile.speaking_xp,
            "Reading": profile.reading_xp,
            "Writing": profile.writing_xp,
            "Learning": profile.learning_xp
        }
        
        needs_improvement = min(xp_sections, key=xp_sections.get)
        
        gemini_calls = CallLog.objects.filter(student=request.user, call_type='AI')
        gemini_total_seconds = sum(call.duration_seconds for call in gemini_calls)

        # Level Thresholds
        thresholds = {"BEGINNER": 200, "INTERMEDIATE": 1000, "PROFESSIONAL": float('inf')}
        
        section_progress = {}
        for section, xp in xp_sections.items():
            level = profile.get_section_level(xp)
            next_xp = thresholds.get(level, 1000)
            section_progress[section] = {
                "current_level": level,
                "current_xp": xp,
                "next_level_xp": next_xp,
                "percent": min(100, int((xp / next_xp) * 100)) if next_xp != float('inf') else 100
            }
        
        data = {
            "overall_level": profile.current_level,
            "total_xp": profile.total_xp,
            "section_progress": section_progress,
            "chart_data": xp_sections,
            "needs_improvement": needs_improvement,
            "gemini_stats": {
                "total_calls": gemini_calls.count(),
                "total_minutes": gemini_total_seconds // 60
            }
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def section_reports(self, request):
        """Detailed analysis report for every section"""
        from django.db.models import Avg, Sum, Count
        
        logs = ActivityLog.objects.filter(student=request.user)
        report = {}
        
        sections = ['LISTENING', 'SPEAKING', 'READING', 'WRITING', 'LEARNING']
        
        for section in sections:
            section_logs = logs.filter(activity_type=section)
            stats = section_logs.aggregate(
                avg_score=Avg('quiz_score'),
                total_duration=Sum('duration_minutes'),
                activity_count=Count('id')
            )
            
            # Special case for Speaking to include CallLogs
            if section == 'SPEAKING':
                calls = CallLog.objects.filter(student=request.user)
                stats['total_duration'] = (stats['total_duration'] or 0) + (sum(c.duration_seconds for c in calls) / 60)
                stats['activity_count'] = stats['activity_count'] + calls.count()

            report[section.capitalize()] = {
                "average_quiz_score": round(stats['avg_score'], 1) if stats['avg_score'] else 0,
                "total_time_spent_minutes": round(stats['total_duration'], 1) if stats['total_duration'] else 0,
                "total_sessions": stats['activity_count']
            }
            
        return Response(report)

    @action(detail=False, methods=['post'])
    def log_activity(self, request):
        serializer = ActivityLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def update_photo(self, request):
        """Updates the student's profile picture"""
        profile = request.user.profile
        if 'photo' in request.FILES:
            profile.profile_photo = request.FILES['photo']
            profile.save()
            return Response({
                "message": "Photo updated!", 
                "url": request.build_absolute_uri(profile.profile_photo.url)
            })
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

# --- SKILL SECTION ENDPOINTS ---

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_auto_lesson(request):
    """Listening: Picks random video based on XP Level."""
    profile = request.user.profile
    user_level = profile.current_level  
    lessons = ListeningLesson.objects.filter(level=user_level)
    
    if not lessons.exists():
        return Response({"message": f"No lessons for {user_level} yet."}, status=404)
    
    lesson = random.choice(lessons)
    return Response({
        "lesson_id": lesson.id,
        "video_url": lesson.youtube_url,
        "quiz": [
            {"text": lesson.q1_text, "options": lesson.q1_options, "correct": lesson.q1_correct},
            {"text": lesson.q2_text, "options": lesson.q2_options, "correct": lesson.q2_correct},
            {"text": lesson.q3_text, "options": lesson.q3_options, "correct": lesson.q3_correct}
        ]
    })

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_learning_session(request):
    """Learning: Gets current Chapter with Primary and Backup examples."""
    profile = request.user.profile
    try:
        chapter = Chapter.objects.get(order=profile.unlocked_chapter)
    except Chapter.DoesNotExist:
        return Response({"message": "You have completed all available chapters!"}, status=404)
    
    examples = chapter.examples.filter(is_backup=False)[:5]
    backups = chapter.examples.filter(is_backup=True)[:5]
    quiz = chapter.quizzes.all()[:3]
    
    return Response({
        "chapter_title": chapter.title,
        "grammar_logic": getattr(chapter, 'grammar_rule_malayalam', ""),
        "primary_examples": [{"en": e.english_text, "ml": e.malayalam_explanation} for e in examples],
        "backup_examples": [{"en": b.english_text, "ml": b.malayalam_explanation} for b in backups],
        "quiz": [
            {
                "question": q.question_text,
                "options": [q.option_a, q.option_b, q.option_c, q.option_d],
                "correct": q.correct_option
            } for q in quiz
        ]
    })

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_reading_story(request):
    """Reading: Story with background and point-reduction logic."""
    profile = request.user.profile
    stories = ReadingStory.objects.filter(level=profile.current_level)
    
    if not stories.exists():
        return Response({"message": "No stories available."}, status=404)
        
    story = random.choice(stories)
    return Response({
        "title": story.title,
        "content": story.story_content,
        "background": story.background_image_url,
        "quiz": [
            {"text": story.q1_text, "options": story.q1_options, "correct": story.q1_correct},
            {"text": story.q2_text, "options": story.q2_options, "correct": story.q2_correct},
            {"text": story.q3_text, "options": story.q3_options, "correct": story.q3_correct},
        ]
    })

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_writing_task(request):
    """Writing: Scrambled sentences for drag-and-drop."""
    profile = request.user.profile
    tasks = WritingTask.objects.filter(level=profile.current_level)
    
    if not tasks.exists():
        return Response({"message": "No writing tasks available."}, status=404)
        
    task = random.choice(tasks)
    return Response({
        "id": task.id,
        "malayalam_hint": task.malayalam_meaning,
        "correct_sentence": task.correct_sentence,
        "extra_words": task.extra_words,
    })

# --- SPEAKING SECTION ---

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_recent_calls(request):
    """Returns the 5 most recent unique contacts for quick dial."""
    recent_calls = CallLog.objects.filter(student=request.user).order_by('-timestamp')
    frequent = []
    seen = set()
    for call in recent_calls:
        if call.contact_name not in seen and len(frequent) < 5:
            frequent.append({
                "id": call.id,
                "name": call.contact_name,
                "number": call.contact_number,
                "type": call.call_type,
                "last_called": call.timestamp,
                "recording_url": request.build_absolute_uri(call.recording_file.url) if call.recording_file else None
            })
            seen.add(call.contact_name)
    return Response(frequent)

@api_view(['GET'])
@permission_classes([IsApprovedStudent])
def get_call_history(request):
    """Returns all call history with recording playback links."""
    history = CallLog.objects.filter(student=request.user).order_by('-timestamp')
    data = []
    for call in history:
        data.append({
            "id": call.id,
            "name": call.contact_name,
            "type": call.call_type,
            "duration": call.duration_seconds,
            "timestamp": call.timestamp,
            "recording_url": request.build_absolute_uri(call.recording_file.url) if call.recording_file else None
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([IsApprovedStudent])
def save_call_recording(request):
    """Saves a call log with duration and optional audio recording."""
    duration = request.data.get('duration_seconds', 0)
    contact_name = request.data.get('contact_name', 'Unknown')
    audio_file = request.FILES.get('audio')

    # Audio file is now mandatory
    if not audio_file:
        return Response({"error": "Recording is required to save call log."}, status=400)

    # Basic validation to prevent TypeError
    try:
        duration_int = int(duration)
    except (ValueError, TypeError):
        duration_int = 0

    CallLog.objects.create(
        student=request.user,
        contact_name=contact_name,
        duration_seconds=duration_int,
        recording_file=audio_file,
        call_type='FRIEND' if contact_name != "Gemini" else 'AI'
    )
    return Response({"message": "Call log saved successfully!"})