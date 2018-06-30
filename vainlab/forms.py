
from django import forms


class NameForm(forms.Form):
    name = forms.CharField(label='', max_length=50, widget=forms.TextInput(
        attrs={'class': 'input-ign', 'placeholder': 'プレイヤー名を入力'}))
