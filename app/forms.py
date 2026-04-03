from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import password_validators_help_text_html


CATEGORY_CHOICES = [
    ("home", "Home"),
    ("national", "National"),
    ("international", "International"),
    ("sports", "Sports"),
    ("science", "Science"),
    ("health", "Health"),
]

SOURCE_CHOICES = [
    ("NDTV", "NDTV"),
    ("The Hindu", "The Hindu"),
    ("India Today", "India Today"),
    ("News18", "News18"),
]

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Please enter a valid email address.')
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text="Enter the same password again for verification.",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", css_class)
            placeholder = field.label or name.replace("_", " ").title()
            field.widget.attrs.setdefault("placeholder", placeholder)
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class UserPreferenceForm(forms.Form):
    preferred_categories = forms.MultipleChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    preferred_sources = forms.MultipleChoiceField(
        choices=SOURCE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    digest_enabled = forms.BooleanField(required=False)
    digest_frequency = forms.ChoiceField(
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["digest_frequency"].widget.attrs["class"] = "form-select"


class BookmarkUpdateForm(forms.Form):
    collection = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collection"].widget.attrs["class"] = "form-control"
        self.fields["notes"].widget.attrs["class"] = "form-control"
