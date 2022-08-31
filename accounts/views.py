from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views import generic
from . forms import RegisterForm, EditProfileForm

def index(request):
    return render(request, 'registration/login.html')
# Create your views here.

class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('catalogue:text_view')
    template_name = 'accounts/change_password.html'

class RegisterView(generic.CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/register.html'

class UserEditView(generic.UpdateView):
    form_class = EditProfileForm
    success_url = reverse_lazy('accounts:edit_profile')
    template_name = 'accounts/edit_profile.html'

    def get_object(self):
        return self.request.user



