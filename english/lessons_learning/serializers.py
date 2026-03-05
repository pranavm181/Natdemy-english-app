from rest_framework import serializers
from .models import Chapter, GrammarExample, GrammarQuiz

class GrammarExampleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = GrammarExample
        fields = ['id', 'english_text', 'malayalam_explanation', 'is_backup']

class GrammarQuizSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = GrammarQuiz
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']

class ChapterSerializer(serializers.ModelSerializer):
    examples = GrammarExampleSerializer(many=True, required=False)
    quizzes = GrammarQuizSerializer(many=True, required=False)

    class Meta:
        model = Chapter
        fields = '__all__'

    def create(self, validated_data):
        examples_data = validated_data.pop('examples', [])
        quizzes_data = validated_data.pop('quizzes', [])
        chapter = Chapter.objects.create(**validated_data)
        
        for example_data in examples_data:
            GrammarExample.objects.create(chapter=chapter, **example_data)
        for quiz_data in quizzes_data:
            GrammarQuiz.objects.create(chapter=chapter, **quiz_data)
            
        return chapter

    def update(self, instance, validated_data):
        examples_data = validated_data.pop('examples', [])
        quizzes_data = validated_data.pop('quizzes', [])

        # Update Chapter fields
        instance.order = validated_data.get('order', instance.order)
        instance.title = validated_data.get('title', instance.title)
        instance.grammar_rule_malayalam = validated_data.get('grammar_rule_malayalam', instance.grammar_rule_malayalam)
        instance.xp_reward = validated_data.get('xp_reward', instance.xp_reward)
        instance.save()

        # Handle Examples
        keep_examples = []
        for example_data in examples_data:
            if 'id' in example_data:
                example_instance = GrammarExample.objects.get(id=example_data['id'], chapter=instance)
                for attr, value in example_data.items():
                    setattr(example_instance, attr, value)
                example_instance.save()
                keep_examples.append(example_instance.id)
            else:
                new_example = GrammarExample.objects.create(chapter=instance, **example_data)
                keep_examples.append(new_example.id)
        
        # Optional: Delete examples not in the request
        # instance.examples.exclude(id__in=keep_examples).delete()

        # Handle Quizzes
        keep_quizzes = []
        for quiz_data in quizzes_data:
            if 'id' in quiz_data:
                quiz_instance = GrammarQuiz.objects.get(id=quiz_data['id'], chapter=instance)
                for attr, value in quiz_data.items():
                    setattr(quiz_instance, attr, value)
                quiz_instance.save()
                keep_quizzes.append(quiz_instance.id)
            else:
                new_quiz = GrammarQuiz.objects.create(chapter=instance, **quiz_data)
                keep_quizzes.append(new_quiz.id)
        
        # Optional: Delete quizzes not in the request
        # instance.quizzes.exclude(id__in=keep_quizzes).delete()

        return instance
