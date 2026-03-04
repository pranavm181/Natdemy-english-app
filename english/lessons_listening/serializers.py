from rest_framework import serializers
from .models import ListeningLesson, ListeningQuestion

class ListeningQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListeningQuestion
        fields = ['id', 'text', 'option_1', 'option_2', 'option_3', 'correct']

class ListeningLessonSerializer(serializers.ModelSerializer):
    questions = ListeningQuestionSerializer(many=True)

    class Meta:
        model = ListeningLesson
        fields = ['id', 'title', 'youtube_url', 'level', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        lesson = ListeningLesson.objects.create(**validated_data)
        for question_data in questions_data:
            ListeningQuestion.objects.create(lesson=lesson, **question_data)
        return lesson

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        # Update lesson fields
        instance.title = validated_data.get('title', instance.title)
        instance.youtube_url = validated_data.get('youtube_url', instance.youtube_url)
        instance.level = validated_data.get('level', instance.level)
        instance.save()

        # Simple nested update: clear and recreate
        # (For a more robust system, we would match by ID)
        instance.questions.all().delete()
        for question_data in questions_data:
            ListeningQuestion.objects.create(lesson=instance, **question_data)
        
        return instance
