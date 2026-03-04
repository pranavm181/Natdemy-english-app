from django.contrib import admin
from .models import Chapter, GrammarExample, GrammarQuiz

class GrammarExampleInline(admin.TabularInline):
    model = GrammarExample
    extra = 1

class GrammarQuizInline(admin.TabularInline):
    model = GrammarQuiz
    extra = 1

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('order', 'title')
    inlines = [GrammarExampleInline, GrammarQuizInline]
