from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import User, Neurodivergencia, Pergunta, PerguntaNeurodivergencia, Resposta, Escola
from .models import Aluno, Coordenador
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user_type='SUPERADMIN')

    def escola_nome(self, obj):
        if obj.escola:
            return obj.escola.nome
        return '—'
    escola_nome.short_description = 'Escola'

    list_display = ('id','nome', 'email', 'user_type', 'escola_nome', 'is_staff')
    list_filter = ('user_type',)
    ordering = ['email'] 

admin.site.register(User, CustomUserAdmin)

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'codigo', 'get_email')
    search_fields = ('nome', 'codigo')

    def get_email(self, obj):
        user = User.objects.filter(user_type='ESCOLA', escola=obj).first()
        return user.email if user else 'Sem email'
    get_email.short_description = 'Email da Escola'

class AlunoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_nome', 'escola', 'ra', 'get_email', 'get_coordenador')
    list_filter = ('escola',) 

    def get_nome(self, obj):
        return obj.user.nome
    get_nome.short_description = 'Nome'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_coordenador(self, obj):
        return obj.coordenador.user.nome if obj.coordenador else "Sem coordenador"
    get_coordenador.short_description = 'Coordenador'

class CoordenadorAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_nome', 'escola', 'get_email', 'get_user_type')
    list_filter = ('escola',)
    search_fields = ('user__nome', 'escola__nome',)

    def get_nome(self, obj):
        return obj.user.nome if obj.user else 'Sem usuário'
    get_nome.short_description = 'Nome'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_user_type(self, obj):
        return obj.user.get_user_type_display() if obj.user else 'Sem tipo'

admin.site.register(Aluno, AlunoAdmin)
admin.site.register(Coordenador, CoordenadorAdmin)

# Registro do modelo PerguntaNeurodivergencia (em linha)
class PerguntaNeurodivergenciaInline(admin.TabularInline):
    model = PerguntaNeurodivergencia
    extra = 1

# Registro do modelo Pergunta
class PerguntaAdmin(admin.ModelAdmin):
    inlines = [PerguntaNeurodivergenciaInline]  # Exibe as perguntas neurodivergentes dentro da Pergunta
    list_display = ('texto', 'ordem')  # Exibe os campos 'texto' e 'ordem'
    search_fields = ('texto',)  # Permite buscar por 'texto' no painel de administração

# Registro dos outros modelos
admin.site.register(Neurodivergencia)
admin.site.register(Pergunta, PerguntaAdmin)
admin.site.register(Resposta)