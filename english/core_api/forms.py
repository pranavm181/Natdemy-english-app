from django import forms
from .models import ListeningLesson, ReadingStory

class BaseQuizForm(forms.ModelForm):
    q1_opt1 = forms.CharField(label="Option 1", required=True)
    q1_opt2 = forms.CharField(label="Option 2", required=True)
    q1_opt3 = forms.CharField(label="Option 3", required=True)
    q1_correct_choice = forms.ChoiceField(
        label="Correct Option",
        choices=[('0', "Option 1 (First)"), ('1', "Option 2 (Second)"), ('2', "Option 3 (Third)")],
        widget=forms.RadioSelect, required=True
    )

    q2_opt1 = forms.CharField(label="Option 1", required=True)
    q2_opt2 = forms.CharField(label="Option 2", required=True)
    q2_opt3 = forms.CharField(label="Option 3", required=True)
    q2_correct_choice = forms.ChoiceField(
        label="Correct Option",
        choices=[('0', "Option 1 (First)"), ('1', "Option 2 (Second)"), ('2', "Option 3 (Third)")],
        widget=forms.RadioSelect, required=True
    )

    q3_opt1 = forms.CharField(label="Option 1", required=False)
    q3_opt2 = forms.CharField(label="Option 2", required=False)
    q3_opt3 = forms.CharField(label="Option 3", required=False)
    q3_correct_choice = forms.ChoiceField(
        label="Correct Option",
        choices=[('0', "Option 1 (First)"), ('1', "Option 2 (Second)"), ('2', "Option 3 (Third)")],
        widget=forms.RadioSelect, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            for i in range(1, 4):
                options = getattr(self.instance, f'q{i}_options', None)
                correct = getattr(self.instance, f'q{i}_correct', None)
                
                if isinstance(options, str):
                    import json
                    try:
                        options = json.loads(options)
                    except:
                        options = []
                        
                if options and isinstance(options, list):
                    if len(options) > 0: self.fields[f'q{i}_opt1'].initial = options[0]
                    if len(options) > 1: self.fields[f'q{i}_opt2'].initial = options[1]
                    if len(options) > 2: self.fields[f'q{i}_opt3'].initial = options[2]
                
                if correct is not None:
                    self.fields[f'q{i}_correct_choice'].initial = str(correct)

    def clean(self):
        cleaned_data = super().clean()
        
        for i in range(1, 4):
            opt1 = cleaned_data.get(f'q{i}_opt1')
            opt2 = cleaned_data.get(f'q{i}_opt2')
            opt3 = cleaned_data.get(f'q{i}_opt3')
            choice = cleaned_data.get(f'q{i}_correct_choice')
            
            if opt1 or opt2 or opt3:
                cleaned_data[f'q{i}_options'] = [opt1 or "", opt2 or "", opt3 or ""]
                cleaned_data[f'q{i}_correct'] = int(choice) if choice is not None else 0
            else:
                cleaned_data[f'q{i}_options'] = None if i == 3 else ["", "", ""]
                cleaned_data[f'q{i}_correct'] = None if i == 3 else 0

        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        for i in range(1, 4):
            if f'q{i}_options' in self.cleaned_data:
                setattr(instance, f'q{i}_options', self.cleaned_data[f'q{i}_options'])
            if f'q{i}_correct' in self.cleaned_data:
                setattr(instance, f'q{i}_correct', self.cleaned_data[f'q{i}_correct'])
        if commit:
            instance.save()
        return instance

class ListeningLessonForm(BaseQuizForm):
    class Meta:
        model = ListeningLesson
        fields = ['title', 'youtube_url', 'level', 'q1_text', 'q2_text', 'q3_text']

class ReadingStoryForm(BaseQuizForm):
    class Meta:
        model = ReadingStory
        fields = ['title', 'level', 'story_content', 'background_image_url', 'q1_text', 'q2_text', 'q3_text']
