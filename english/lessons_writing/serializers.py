from rest_framework import serializers
from .models import WritingTask

class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = '__all__'
