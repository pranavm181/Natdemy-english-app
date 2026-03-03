from django.contrib import admin
from django.utils.html import format_html
from .models import (
    StudentProfile, ActivityLog, ListeningLesson, 
    Chapter, GrammarExample, GrammarQuiz, ReadingStory,
    WritingTask, CallLog
)
from .forms import ListeningLessonForm, ReadingStoryForm

admin.site.site_header = "Natdemy Management System"
admin.site.site_title = "Natdemy Admin Portal"
admin.site.index_title = "Welcome to the English Training Dashboard"

# 1. Student Management
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'is_approved', 'display_level', 'total_xp', 'current_streak', 'unlocked_chapter', 'display_photo', 'created_at')
    list_filter = ('is_approved', 'unlocked_chapter')
    list_editable = ('is_approved',) 
    search_fields = ('user__username', 'student_id')
    readonly_fields = ('created_at', 'display_photo', 'listening_xp', 'speaking_xp', 'reading_xp', 'writing_xp', 'learning_xp')

    def display_level(self, obj):
        return obj.current_level
    display_level.short_description = "Level"

    def display_photo(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />', obj.profile_photo.url)
        return "No Photo"
    display_photo.short_description = "Profile Photo"

# 2. Grammar Curriculum (Chapter -> Examples & Quizzes)
class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 5 

class GrammarQuizInline(admin.TabularInline):
    model = GrammarQuiz
    extra = 3 

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('order', 'title')
    ordering = ('order',)
    inlines = [GrammarExampleInline, GrammarQuizInline]

# 3. Reading Stories
@admin.register(ReadingStory)
class ReadingStoryAdmin(admin.ModelAdmin):
    form = ReadingStoryForm
    list_display = ('title', 'level')
    list_filter = ('level',)
    fieldsets = (
        ('Story Content', {
            'fields': ('title', 'level', 'story_content', 'background_image_url')
        }),
        ('Question 1', {
            'fields': ('q1_text', 'q1_opt1', 'q1_opt2', 'q1_opt3', 'q1_correct_choice')
        }),
        ('Question 2', {
            'fields': ('q2_text', 'q2_opt1', 'q2_opt2', 'q2_opt3', 'q2_correct_choice')
        }),
        ('Question 3 (Optional)', {
            'fields': ('q3_text', 'q3_opt1', 'q3_opt2', 'q3_opt3', 'q3_correct_choice')
        }),
    )

# 4. Listening Lessons
@admin.register(ListeningLesson)
class ListeningLessonAdmin(admin.ModelAdmin):
    form = ListeningLessonForm
    list_display = ('title', 'level')
    list_filter = ('level',)
    fieldsets = (
        ('Lesson Details', {
            'fields': ('title', 'youtube_url', 'level')
        }),
        ('Question 1', {
            'fields': ('q1_text', 'q1_opt1', 'q1_opt2', 'q1_opt3', 'q1_correct_choice')
        }),
        ('Question 2', {
            'fields': ('q2_text', 'q2_opt1', 'q2_opt2', 'q2_opt3', 'q2_correct_choice')
        }),
        ('Question 3 (Optional)', {
            'fields': ('q3_text', 'q3_opt1', 'q3_opt2', 'q3_opt3', 'q3_correct_choice')
        }),
    )

# 5. Activity Logs (Read-only for safety)
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity_type', 'duration_minutes', 'quiz_score', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    readonly_fields = ('student', 'activity_type', 'duration_minutes', 'quiz_score', 'timestamp')

# 6. Writing Tasks
@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ('malayalam_meaning', 'level')
    list_filter = ('level',)

# 7. Speaking / Call Logs (Merged Class)
@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'contact_name', 'call_type', 'duration_seconds', 'play_audio', 'timestamp')
    list_filter = ('call_type', 'timestamp')
    readonly_fields = ('recording_file', 'timestamp')
    
    def play_audio(self, obj):
        if obj.recording_file:
            return format_html('<audio controls src="{}" style="height: 30px;"></audio>', obj.recording_file.url)
        return "No Recording"
    
    play_audio.short_description = "Preview Audio"