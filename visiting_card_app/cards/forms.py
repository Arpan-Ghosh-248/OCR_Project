from django import forms
from .models import VisitingCard

class CardUploadForm(forms.ModelForm):
    class Meta:
        model = VisitingCard
        fields = ['image']