from django import forms

TOPIC_CHOICES = [
    ('general', 'General Inquiry'),
    ('data', 'Data Correction / Feedback'),
    ('collaboration', 'Research Collaboration'),
    ('technical', 'Technical Issue'),
    ('other', 'Other'),
]


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Your name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'})
    )
    topic = forms.ChoiceField(
        choices=TOPIC_CHOICES,
        label='Subject'
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'How can we help?'})
    )