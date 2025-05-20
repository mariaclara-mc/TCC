from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import Coordenador

@receiver(post_save, sender=Coordenador)
def criar_usuario_para_coordenador(sender, instance, created, **kwargs):
    if created and instance.user is None:  # Só cria um usuário se não existir
        # O usuário já foi criado e a senha foi definida no formulário de cadastro
        user = User.objects.create_user(
            email=instance.user.email,  # O email vem do coordenador já registrado
            password=instance.user.password  # A senha já foi definida pelo coordenador
        )

        instance.user = user  # Associa o usuário ao coordenador
        instance.save()

