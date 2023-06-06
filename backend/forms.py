from django import forms

class UploadFileForm():
    title = forms.CharField(max_length=50)
    file = forms.FileField()