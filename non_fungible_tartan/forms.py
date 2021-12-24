from django import forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from non_fungible_tartan.models import *
from django.utils import timezone
from datetime import datetime


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Username"}
        ),
    )
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Password"}
        ),
    )

    def clean_password(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username/password")

        return password


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )
    email = forms.CharField(
        max_length=100,
        widget=forms.EmailInput(attrs={"class": "form-control form-control-lg"}),
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg"}),
    )
    password = forms.CharField(
        max_length=200,
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
    )
    confirm_password = forms.CharField(
        max_length=200,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"}),
    )

    def clean_confirm_password(self):
        password1 = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("confirm_password")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__exact=email):
            raise forms.ValidationError("Email is already used.")

        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        return username


class BuyingPowerForm(forms.Form):
    name_on_card = forms.CharField(max_length=50)
    card_number = forms.CharField(max_length=20)
    expiration_date = forms.DateTimeField(input_formats=["%m/%Y"])
    cvc = forms.CharField(max_length=4)
    address = forms.CharField()
    city = forms.CharField()
    state = forms.CharField()
    zipcode = forms.CharField()
    amount = forms.IntegerField()

    def clean_card_number(self):
        card_number = self.cleaned_data.get("card_number")
        card_numbers = card_number.split("-")
        return "".join(card_numbers)

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get("expiration_date")
        now = timezone.localtime(timezone.now())
        if expiration_date < now:
            raise forms.ValidationError("Your card has been expired")

        return expiration_date

    def clean_cvc(self):
        cvc = self.cleaned_data.get("cvc")
        if len(cvc) != 3 and len(cvc) != 4:
            raise forms.ValidationError("Please check your CVC number")
        return cvc

    def clean_zipcode(self):
        zipcode = self.cleaned_data.get("zipcode")
        if len(zipcode) != 5:
            raise forms.ValidationError("Please provide correct zip code")
        return zipcode


class CreateNFTForm(forms.ModelForm):
    auctiontime = forms.DateTimeField(required=False)

    class Meta:
        model = NFT
        exclude = {
            "create_time",
            "current_owner",
            "original_owner",
            "previous_owners",
        }


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = {"create_time"}
        widgets = {
            "user": forms.HiddenInput(),
        }
