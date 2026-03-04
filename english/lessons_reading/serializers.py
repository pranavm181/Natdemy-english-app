from rest_framework import serializers
from .models import ReadingStory, ReadingQuestion

class ReadingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        fields = ['id', 'text', 'option_1', 'option_2', 'option_3', 'correct']

class ReadingStorySerializer(serializers.ModelSerializer):
    questions = ReadingQuestionSerializer(many=True)

    class Meta:
        model = ReadingStory
        fields = ['id', 'title', 'level', 'story_content', 'background_image_url', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        story = ReadingStory.objects.create(**validated_data)
        for question_data in questions_data:
            ReadingQuestion.objects.create(story=story, **question_data)
        return story

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        # Update story fields
        instance.title = validated_data.get('title', instance.title)
        instance.level = validated_data.get('level', instance.level)
        instance.story_content = validated_data.get('story_content', instance.story_content)
        instance.background_image_url = validated_data.get('background_image_url', instance.background_image_url)
        instance.save()

        # Simple nested update: clear and recreate
        instance.questions.all().delete()
        for question_data in questions_data:
            ReadingQuestion.objects.create(story=instance, **question_data)
        
        return instance
