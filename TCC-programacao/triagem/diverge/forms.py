# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Coordenador, User
from diverge.models import Escola
from django.contrib.auth.hashers import make_password  # Adicionei esta importação
from django.core.exceptions import ValidationError
import uuid
from django.contrib.auth import authenticate
from .models import Aluno
from django.contrib.auth import get_user_model
import re

class EscolaForm(forms.ModelForm):
    class Meta:
        model = Escola
        fields = ['nome', 'codigo', 'email']
        labels = {
            'email': 'Email institucional da escola',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if Escola.objects.filter(codigo=codigo).exists():
            raise forms.ValidationError("Este código de escola já está em uso.")
        return codigo

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Escola.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este e-mail já está em uso para outra escola.")
        return email

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['ra']

    def clean_ra(self):
        ra = self.cleaned_data.get('ra')
        if Aluno.objects.filter(ra=ra).exists():
            raise forms.ValidationError("Este RA já está em uso por outro aluno.")
        return ra
    
User = get_user_model()

# Para editar nome e email do aluno (usuário)
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nome', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outro aluno.")
        return email

class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )

    def clean_email(self):
        # Converte o e-mail para minúsculas antes de qualquer validação
        return self.cleaned_data['email'].lower()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Email ou senha inválidos.")
            self.user = user

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

# Formulário de Registro de Aluno com Associação à Escola
class StudentRegistrationForm(UserCreationForm):
    escola = forms.ModelChoiceField(queryset=Escola.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    ra = forms.CharField(required=True, label="RA")

    class Meta:
        model = User
        fields = ('nome', 'email', 'password1', 'password2', 'escola')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nome completo'})
        self.fields['ra'].widget.attrs.update({'class': 'form-control', 'placeholder': 'RA'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email institucional'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar senha'})
        self.fields['escola'].widget.attrs.update({'class': 'form-control'})

    def clean_password1(self):
        password = self.cleaned_data.get('password1')

        # Validar senha com critérios específicos
        if len(password) < 8:
            raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("A senha deve conter pelo menos um número.")
        if not re.search(r'[\W_]', password):
            raise ValidationError("A senha deve conter pelo menos um caractere especial.")
        
        return password

    def clean_ra(self):
        ra = self.cleaned_data.get('ra')
        if Aluno.objects.filter(ra=ra).exists():
            raise forms.ValidationError("Este RA já está em uso por outro aluno.")
        return ra

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outro aluno.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'STUDENT'
        user.is_staff = False
        user.is_superuser = False
        user.escola = self.cleaned_data['escola']

        escola = self.cleaned_data['escola']
        coordenador = escola.coordenador_set.first()  # Atribui o primeiro coordenador da escola
        ra = self.cleaned_data['ra']  # ← PEGANDO O RA

        if commit:
            user.save()

        # ← CRIANDO o aluno com RA
        aluno = Aluno.objects.create(user=user, escola=escola, coordenador=coordenador, ra=ra)

        return user


class CoordinatorRegistrationForm(UserCreationForm):
    email_escola = forms.EmailField(label='Email da Escola (para verificação)')
    email_coordenador = forms.EmailField(label='Email pessoal institucional')
    escola = forms.ModelChoiceField(queryset=Escola.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('nome', 'email_coordenador', 'password1', 'password2', 'escola')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nome completo'})
        self.fields['email_escola'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email da escola'})
        self.fields['email_coordenador'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email institucional pessoal'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar senha'})
        self.fields['escola'].widget.attrs.update({'class': 'form-control'})

    def clean_email_coordenador(self):
        email = self.cleaned_data.get('email_coordenador')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outro usuário.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')

        # Validação da senha
        if len(password) < 8:
            raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("A senha deve conter pelo menos um número.")
        if not re.search(r'[\W_]', password):
            raise ValidationError("A senha deve conter pelo menos um caractere especial.")

        return password

    def save(self, commit=True): 
        user = super().save(commit=False)
        user.user_type = 'COORDINATOR'  # Aqui você define o tipo de usuário como COORDINATOR
        user.email = self.cleaned_data['email_coordenador']
        
        if commit:
            user.save()  # Salvando o usuário primeiro

        # Após salvar o usuário, agora associamos ele ao modelo Coordenador
        coordenador = Coordenador.objects.create(user=user, escola=self.cleaned_data['escola'])

        
        return coordenador  # Retorna o coordenador que foi criado

    
class VerificacaoCodigoForm(forms.Form):
    codigo = forms.CharField(max_length=6, required=True, label="Código de Verificação")