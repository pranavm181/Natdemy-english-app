from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
import csv
import io
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

# Import models & serializers from core_api
from .models import StudentProfile, ActivityLog
from .serializers import StudentProfileSerializer, ActivityLogSerializer
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear

# Import models from other apps for stats
from lessons_listening.models import ListeningLesson
from lessons_reading.models import ReadingStory
from lessons_writing.models import WritingTask
from lessons_learning.models import Chapter
from .permissions import IsApprovedStudent

# Import mixins from new apps
from lessons_listening.views import ListeningMixin
from lessons_reading.views import ReadingMixin
from lessons_writing.views import WritingMixin
from lessons_learning.views import LearningMixin
from social.views import SpeakingMixin
from social.models import CallLog

class AnalyticsMixin:
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

    @action(detail=False, methods=['get'])
    def digital_wellbeing(self, request):
        """Digital Wellbeing: Daily breakdown of time spent per section for last 7 days."""
        from django.db.models import Sum
        from django.db.models.functions import TruncDate
        
        last_7_days = timezone.now().date() - timedelta(days=6)
        
        # 1. Aggregate Lesson Activities
        lesson_stats = ActivityLog.objects.filter(
            student=request.user,
            timestamp__date__gte=last_7_days
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day', 'activity_type').annotate(
            total_minutes=Sum('duration_minutes')
        ).order_by('day')

        # 2. Aggregate Speaking/Calls
        call_stats = CallLog.objects.filter(
            student=request.user,
            timestamp__date__gte=last_7_days
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day').annotate(
            total_seconds=Sum('duration_seconds')
        ).order_by('day')

        # Organize by date
        wellbeing_data = {}
        for i in range(7):
            day = last_7_days + timedelta(days=i)
            wellbeing_data[str(day)] = {
                "Listening": 0, "Reading": 0, "Writing": 0, "Learning": 0, "Speaking": 0, "Total": 0
            }

        for stat in lesson_stats:
            date_str = str(stat['day'])
            section = stat['activity_type'].capitalize()
            if date_str in wellbeing_data:
                wellbeing_data[date_str][section] = round(stat['total_minutes'], 1)
                wellbeing_data[date_str]["Total"] += round(stat['total_minutes'], 1)

        for stat in call_stats:
            date_str = str(stat['day'])
            if date_str in wellbeing_data:
                minutes = round(stat['total_seconds'] / 60, 1)
                wellbeing_data[date_str]["Speaking"] += minutes
                wellbeing_data[date_str]["Total"] += minutes

        return Response(wellbeing_data)

import csv
import io
from rest_framework.pagination import PageNumberPagination

class StudentViewSet(viewsets.GenericViewSet, 
                     mixins.ListModelMixin, 
                     mixins.RetrieveModelMixin, 
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     ListeningMixin,
                     ReadingMixin,
                     WritingMixin,
                     LearningMixin,
                     SpeakingMixin,
                     AnalyticsMixin):
    """
    Handles Profile, Weekly Charts, Activity Logging, and all Skill Section logic.
    """
    serializer_class = StudentProfileSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsApprovedStudent]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    search_fields = ['user__username', 'user__email', 'student_id']

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use utf-8-sig to handle BOM (Byte Order Mark) from Excel/Windows CSVs
            decoded_file = file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            raw_headers = reader.fieldnames
            if not raw_headers:
                return Response({"error": "CSV file appears to be empty or has no headers."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a mapping from clean lowercase version to raw header name
            header_map = {}
            for h in raw_headers:
                clean = h.lower().replace(' ', '').replace('_', '').replace('-', '')
                header_map[clean] = h

            def get_val(row, *variants):
                for v in variants:
                    clean_v = v.lower().replace(' ', '').replace('_', '').replace('-', '')
                    if clean_v in header_map:
                        return row.get(header_map[clean_v], '').strip()
                return ''

            created_count = 0
            errors = []

            for row in reader:
                username = get_val(row, 'username', 'name', 'user')
                email = get_val(row, 'email', 'mail', 'emailaddress')
                password = get_val(row, 'password', 'pass', 'pwd')
                student_id = get_val(row, 'studentid', 'id', 'studentnumber')

                if not all([username, email, password]):
                    missing = []
                    if not username: missing.append('username')
                    if not email: missing.append('email')
                    if not password: missing.append('password')
                    errors.append(f"Row skipped: Missing {', '.join(missing)}. Detected data in row: {list(row.values())}")
                    continue

                try:
                    existing_user = User.objects.filter(username=username).first()
                    if existing_user:
                        if hasattr(existing_user, 'profile'):
                            errors.append(f"Skipped {username}: Username already exists.")
                            continue
                        else:
                            # This is a lingering user left over from a previous incomplete deletion
                            # We delete it so we can create a fresh one with the new password/email
                            existing_user.delete()

                    if User.objects.filter(email=email).exists():
                        errors.append(f"Skipped {username}: Email already exists.")
                        continue

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    # Profile is auto-created by signal with a default ID
                    profile = user.profile
                    
                    # If CSV provides a student_id, try to use it
                    assigned_id = profile.student_id # Fallback to auto-gen
                    if student_id:
                        if StudentProfile.objects.filter(student_id=student_id).exclude(user=user).exists():
                            errors.append(f"User {username} created but Student ID {student_id} already exists. Using auto-generated ID: {assigned_id}")
                        else:
                            profile.student_id = student_id
                            assigned_id = student_id
                    
                    profile.is_approved = True
                    profile.save()
                    
                    created_count += 1
                except Exception as row_error:
                    errors.append(f"Error creating {username}: {str(row_error)}")

            return Response({
                "message": f"Successfully imported {created_count} students.",
                "errors": errors,
                "columns_detected": raw_headers
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Bulk import failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        """Deleting the profile should also delete the User account."""
        user = instance.user
        instance.delete()
        user.delete()

    @action(detail=False, methods=['get'])
    def admin_stats(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # 1. User Stats
        user_stats = {
            "total": StudentProfile.objects.filter(user__is_superuser=False).count(),
            "approved": StudentProfile.objects.filter(is_approved=True, user__is_superuser=False).count(),
            "pending": StudentProfile.objects.filter(is_approved=False, user__is_superuser=False).count()
        }

        # 2. Curriculum Stats
        curriculum_stats = {
            "listening": ListeningLesson.objects.count(),
            "reading": ReadingStory.objects.count(),
            "writing": WritingTask.objects.count(),
            "chapters": Chapter.objects.count()
        }

        # 3. Activity Aggregation Helper
        def get_trend(queryset, trunc_func, periods, date_field='timestamp'):
            trend = queryset.annotate(period=trunc_func(date_field)) \
                            .values('period') \
                            .annotate(count=Count('id')) \
                            .order_by('-period')[:periods]
            return list(trend)

        activity_stats = {
            "daily": get_trend(ActivityLog.objects.all(), TruncDay, 30),
            "weekly": get_trend(ActivityLog.objects.all(), TruncWeek, 12),
            "monthly": get_trend(ActivityLog.objects.all(), TruncMonth, 12),
            "yearly": get_trend(ActivityLog.objects.all(), TruncYear, 5),
        }

        return Response({
            "users": user_stats,
            "curriculum": curriculum_stats,
            "activity": activity_stats
        })

    @action(detail=True, methods=['get'])
    def student_report(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        profile = self.get_object()
        user = profile.user

        # 1. Section stats aggregation
        from django.db.models import Avg, Sum, Count
        logs = ActivityLog.objects.filter(student=user)
        section_summary = {}
        sections = ['LISTENING', 'SPEAKING', 'READING', 'WRITING', 'LEARNING']
        
        for section in sections:
            s_logs = logs.filter(activity_type=section)
            stats = s_logs.aggregate(
                avg_score=Avg('quiz_score'),
                total_duration=Sum('duration_minutes'),
                activity_count=Count('id')
            )
            section_summary[section.capitalize()] = {
                "avg_score": round(stats['avg_score'], 1) if stats['avg_score'] else 0,
                "total_time": round(stats['total_duration'], 1) if stats['total_duration'] else 0,
                "sessions": stats['activity_count']
            }

        # 2. Recent activity
        recent_logs = logs.order_by('-timestamp')[:50]
        log_data = ActivityLogSerializer(recent_logs, many=True).data

        # 3. 7-day wellbeing trend
        from django.db.models.functions import TruncDate
        last_7_days = timezone.now().date() - timedelta(days=6)
        trend = logs.filter(timestamp__date__gte=last_7_days) \
                    .annotate(day=TruncDate('timestamp')) \
                    .values('day') \
                    .annotate(total=Sum('duration_minutes')) \
                    .order_by('day')
        
        trend_data = {str(last_7_days + timedelta(days=i)): 0 for i in range(7)}
        for t in trend:
            trend_data[str(t['day'])] = round(t['total'], 1)

        return Response({
            "profile": StudentProfileSerializer(profile).data,
            "section_summary": section_summary,
            "recent_activity": log_data,
            "wellbeing_trend": trend_data
        })

    def get_queryset(self):
        if self.request.user.is_superuser:
            return StudentProfile.objects.filter(user__is_superuser=False)
        return StudentProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def log_activity(self, request):
        serializer = ActivityLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def update_photo(self, request):
        profile = request.user.profile
        if 'photo' in request.FILES:
            profile.profile_photo = request.FILES['photo']
            profile.save()
            return Response({
                "message": "Photo updated!", 
                "url": request.build_absolute_uri(profile.profile_photo.url)
            })
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
