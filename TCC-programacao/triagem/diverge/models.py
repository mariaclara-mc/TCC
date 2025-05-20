from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('O email é obrigatório'))
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'SUPERADMIN')

        return self.create_user(email, password, **extra_fields)

# Modelo da Escola
class Escola(models.Model):
    nome = models.CharField(max_length=255)
    codigo = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nome.strip() if self.nome else "Nome não definido"
    
#Modelo do User
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('STUDENT', 'Estudante'),
        ('COORDINATOR', 'Coordenador'),
        ('ESCOLA', 'Escola'),
    )

    username = None
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    escola = models.ForeignKey('Escola', null=True, blank=True, on_delete=models.CASCADE)

    USERNAME_FIELD = 'email'  # O email é o campo de login
    REQUIRED_FIELDS = []  # Não precisamos de outros campos para a criação de superusuário

    objects = CustomUserManager()

    def __str__(self):
        if self.user_type == 'COORDINATOR' and hasattr(self, 'coordenador'):
            return f"{self.nome} ({self.email})"
        elif self.user_type == 'STUDENT' and hasattr(self, 'aluno'):
            return f"{self.nome} ({self.email})"
        elif self.user_type == 'ESCOLA' and self.escola:
            return f"{self.escola.nome} ({self.email})"
        return f"{self.nome} ({self.email})"

    def is_coordinator(self):
        return self.user_type == 'COORDINATOR'
    
    def is_student(self):
        return self.user_type == 'STUDENT'
    
    def is_superadmin(self):
        return self.is_staff and self.is_superuser
    
    class Meta:
        app_label = 'diverge'

# Modelo do Coordenador 
class Coordenador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Coordenador: {self.user.email} - Escola: {self.escola.nome}"

    class Meta:
        verbose_name = 'Coordenador'
        verbose_name_plural = 'Coordenadores'

# Modelo do Aluno
class Aluno(models.Model):
    ra = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coordenador = models.ForeignKey(Coordenador, on_delete=models.CASCADE, null=True, blank=True)
    escola = models.ForeignKey('Escola', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.nome

    def clean(self):
        if not self.coordenador:
            raise ValidationError("O aluno deve ter um coordenador associado.")

# Verificação de Coordenador
class CoordenadorVerificacao(models.Model):
    coordenador = models.OneToOneField(Coordenador, on_delete=models.CASCADE)
    codigo_verificacao = models.CharField(max_length=6)
    data_envio = models.DateTimeField(default=timezone.now)
    valido_ate = models.DateTimeField()

    def __str__(self):
        if self.coordenador and self.coordenador.user:
            return f"Verificação para {self.coordenador.user.nome} ({self.coordenador.user.email})"
        return "Verificação sem coordenador vinculado"

    def is_valid(self):
        return self.valido_ate > timezone.now()

# Neurodivergência
class Neurodivergencia(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()

    def __str__(self):
        return self.nome

# Perguntas
class Pergunta(models.Model):
    texto = models.TextField()
    neurodivergencias = models.ManyToManyField(Neurodivergencia, through='PerguntaNeurodivergencia')
    ordem = models.IntegerField(default=0)

    def __str__(self):
        return self.texto

class PerguntaNeurodivergencia(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    neurodivergencia = models.ForeignKey(Neurodivergencia, on_delete=models.CASCADE)
    peso = models.IntegerField(default=1)

    class Meta:
        unique_together = ('pergunta', 'neurodivergencia')

# Respostas
class Resposta(models.Model):
    OPCOES = [
        (0, 'Nunca'),
        (1, 'Raramente'),
        (2, 'Às vezes'),
        (3, 'Frequentemente'),
        (4, 'Sempre'),
    ]

    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    valor = models.IntegerField(choices=OPCOES)
    sessao = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

# Resultados de Quiz
class QuizResult(models.Model):
    student = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='quiz_results')
    quiz_name = models.CharField(max_length=200)
    score = models.IntegerField()
    max_score = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.nome} - {self.quiz_name} - {self.score}/{self.max_score}"