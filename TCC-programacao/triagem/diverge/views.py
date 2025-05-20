from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import LoginForm, StudentRegistrationForm, CoordinatorRegistrationForm
from .models import User, QuizResult, Pergunta, Resposta, PerguntaNeurodivergencia, Neurodivergencia
import uuid
from .models import Escola
from .forms import EscolaForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from .forms import StudentRegistrationForm  # Ou o nome correto do formulári
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from .models import CoordenadorVerificacao
from .models import Coordenador
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, get_object_or_404, redirect
from .models import Aluno
from .forms import AlunoForm, UserForm
from django.contrib.auth import get_user_model

@login_required(login_url='login_escola')
@staff_member_required  # Certifica-se de que só administradores podem acessar
def superadmin_dashboard(request):
    escolas = Escola.objects.all()  # Supondo que você tenha um modelo de Escola
    users = User.objects.all()  # Supondo que você tenha o modelo de usuário
    return render(request, 'diverge/superadmin_dashboard.html', {
        'escolas': escolas,
        'users': users,
    })

def is_superadmin(user):
    return user.user_type == 'SUPERADMIN'

User = get_user_model()

@login_required(login_url='login_escola') 
@user_passes_test(is_superadmin)
def editar_escola(request, pk):
    escola = get_object_or_404(Escola, pk=pk)

    if request.method == 'POST':
        editar_escola = EscolaForm(request.POST, instance=escola)

        if editar_escola.is_valid():
            editar_escola.save()
            messages.success(request, f"Escola {escola.nome} atualizada com sucesso!")
            return redirect('superadmin_dashboard')
    else:
        editar_escola = EscolaForm(instance=escola)

    return render(request, 'diverge/editar_escola.html', {
        'form': editar_escola
    })

def cadastrar_escola(request):
    if request.method == 'POST':
        form = EscolaForm(request.POST)
        if form.is_valid():
            escola = form.save()

            # Criando o usuário da escola e associando com a instância da escola
            usuario = User.objects.create(
                nome=escola.nome,  # <-- aqui você preenche o campo que aparece na tabela User
                email=escola.email,
                user_type='ESCOLA',
                escola=escola
            )

            messages.success(request, f"Escola {escola.nome} cadastrada com sucesso!")
            return redirect('login_escola')
    else:
        form = EscolaForm()

    return render(request, 'diverge/cadastrar_escola.html', {'form': form})

def login_escola(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superadmin_dashboard')
        elif request.user.user_type == 'COORDINATOR':
            return redirect('escola_dashboard')
        elif request.user.user_type == 'STUDENT':
            return redirect('student_dashboard')
        else:
            return redirect('home')

    if request.method == 'POST':
        nome_escola = request.POST.get('nome', '').strip()
        codigo_escola = request.POST.get('codigo', '').strip()

        escola = Escola.objects.filter(nome__iexact=nome_escola, codigo=codigo_escola).first()

        if escola:
            # Guardar o ID da escola na sessão
            request.session['escola_id'] = escola.id
            messages.success(request, f"Bem-vindo à escola {escola.nome}!")

            # Redireciona para o próximo passo, por exemplo:
            return redirect('login')  # ou outra URL
        else:
            messages.error(request, "Nome da escola ou código inválidos.")

    return render(request, 'accounts/login_escola.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirecionar_usuario(request.user)

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirecionar_usuario(user)
            else:
                messages.error(request, "Email ou senha inválidos.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def redirecionar_usuario(user):
    if user.user_type == 'SUPERADMIN':
        return redirect('superadmin_dashboard')
    elif user.user_type == 'COORDINATOR':
        return redirect('escola_dashboard')
    elif user.user_type == 'STUDENT':
        return redirect('student_dashboard')
    else:
        return redirect('home')

def choose_registration(request):
    return render(request, 'diverge/choose_registration.html')

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Agora você pode fazer login.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()

    return render(request, 'diverge/register_student.html', {'form': form})

def enviar_email_verificacao(user, email_escola):
    codigo_verificacao = str(uuid.uuid4())[:6]  # Código de verificação gerado aleatoriamente

    # Assunto e corpo do e-mail
    subject = 'Verificação de Coordenador'
    message = f'O seu código de verificação é: {codigo_verificacao}'
    from_email = settings.DEFAULT_FROM_EMAIL  # Defina o e-mail de envio no settings

    try:
        send_mail(subject, message, from_email, [email_escola])  # Envia o e-mail
        return codigo_verificacao  # Retorna o código gerado (pode ser útil para armazenamento ou validação posterior)
    except Exception as e:
        return None  # Caso haja erro no envio, retorne None

def verificar_codigo(request, coordenador_id):
    coordenador = get_object_or_404(Coordenador, id=coordenador_id)

    if request.method == 'POST':
        codigo_digitado = request.POST.get('codigo')

        try:
            verificacao = CoordenadorVerificacao.objects.get(
                coordenador=coordenador,
                codigo_verificacao=codigo_digitado
            )

            if verificacao.valido_ate >= timezone.now():
                # Ativa o usuário associado ao coordenador
                coordenador.user.is_active = True
                coordenador.user.save()

                verificacao.delete()

                messages.success(request, "Coordenador registrado com sucesso! Agora você pode fazer login.")
                return redirect('login_escola')
            else:
                messages.error(request, "O código expirou. Solicite um novo registro.")
        except CoordenadorVerificacao.DoesNotExist:
            messages.error(request, "Código de verificação inválido.")

    return render(request, 'diverge/verificar_codigo.html', {'coordenador': coordenador})

def register_coordinator(request):
    if request.method == 'POST':
        form = CoordinatorRegistrationForm(request.POST)
        if form.is_valid():
            escola = form.cleaned_data['escola']

            # Verificação: só permitir 1 coordenador por escola
            if User.objects.filter(user_type='COORDINATOR', escola=escola).exists():
                messages.error(request, "Essa escola já possui um coordenador cadastrado.")
                return redirect('register_coordinator')

            try:
                coordenador = form.save()
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('register_coordinator')

            # Lógica para envio do código de verificação
            codigo_verificacao = enviar_email_verificacao(coordenador, form.cleaned_data['email_escola'])

            if codigo_verificacao:
                CoordenadorVerificacao.objects.create(
                    coordenador=coordenador,
                    codigo_verificacao=codigo_verificacao,
                    valido_ate=timezone.now() + timezone.timedelta(hours=1)
                )
                messages.success(request, "Um código foi enviado para o e-mail institucional da escola. Valide o código para ativar o coordenador.")
                return redirect('verificar_codigo', coordenador_id=coordenador.id)
            else:
                coordenador.user.delete()
                coordenador.delete()
                messages.error(request, "Erro ao enviar o código de verificação.")
                return redirect('register_coordinator')
    else:
        form = CoordinatorRegistrationForm()

    return render(request, 'diverge/register_coordinator.html', {'form': form})

@login_required(login_url='login_escola') 
def student_dashboard(request):
    if request.user.user_type != 'STUDENT':
        return redirect('escola_dashboard')

    escola_id = request.session.get('escola_id')
    if escola_id:
        escola = Escola.objects.get(id=escola_id)
        aluno = request.user.aluno  # ← Acesso correto ao modelo Aluno
        quiz_results = QuizResult.objects.filter(
            student=aluno,
            student__escola=escola
        ).order_by('-date_taken')
        return render(request, 'diverge/student_dashboard.html', {'quiz_results': quiz_results, 'escola': escola})
    else:
        return redirect('login')

from django.shortcuts import render, get_object_or_404
from .models import Escola, Aluno

def is_coordenador(user):
    return user.is_authenticated and user.user_type == 'COORDINATOR'

@login_required(login_url='login_escola')
@user_passes_test(is_coordenador)
def escola_dashboard(request):
    escola_id = request.session.get('escola_id')
    escola = get_object_or_404(Escola, id=escola_id)

    students = Aluno.objects.filter(
        escola=escola,
        user__escola=escola,
        user__user_type='STUDENT'
    )

    coordenador_da_escola = Coordenador.objects.filter(
        escola=escola,
        user__user_type='COORDINATOR'
    )

    return render(request, 'diverge/escola_dashboard.html', {
        'escola': escola,
        'students': students,
        'coordenador_da_escola': coordenador_da_escola,
    })

@login_required(login_url='login_escola')  
@user_passes_test(is_coordenador)
def editar_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    user = aluno.user  # obtém o User vinculado ao aluno

    if request.method == 'POST':
        aluno_form = AlunoForm(request.POST, instance=aluno)
        user_form = UserForm(request.POST, instance=user)

        if aluno_form.is_valid() and user_form.is_valid():
            user_form.save()
            aluno_form.save()
            messages.success(request, f"Aluno(a) {user.nome} atualizado com sucesso!")
            return redirect('escola_dashboard')
    else:
        aluno_form = AlunoForm(instance=aluno)
        user_form = UserForm(instance=user)

    return render(request, 'diverge/editar_aluno.html', {
        'form': aluno_form,
        'user_form': user_form
    })

@login_required(login_url='login_escola') 
@user_passes_test(is_coordenador)
def adicionar_aluno(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Aluno adicionado com sucesso!")
            return redirect('escola_dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'diverge/adicionar_aluno.html', {
        'form': form,
        'titulo': 'Adicionar Aluno'
    })

@login_required(login_url='login_escola') 
@user_passes_test(is_coordenador)
def excluir_aluno(request, aluno_id):
    aluno = get_object_or_404(User, id=aluno_id, user_type='STUDENT')  # Filtra por user_type='STUDENT'
    if request.method == 'POST':
        aluno.delete()
        return redirect('escola_dashboard')
    return render(request, 'diverge/excluir_aluno.html', {'aluno': aluno})

@login_required(login_url='login_escola') 
@user_passes_test(is_coordenador)
def editar_coordenador(request, pk):
    coordenador = get_object_or_404(Coordenador, pk=pk)
    user = coordenador.user  # acessa o User vinculado

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, f"Coordenador(a) {user.nome} atualizado com sucesso!")
            return redirect('escola_dashboard')
    else:
        user_form = UserForm(instance=user)

    return render(request, 'diverge/editar_coordenador.html', {
        'user_form': user_form
    })

@login_required(login_url='login_escola') 
@user_passes_test(is_coordenador)
def excluir_coordenador(request, coordenador_id):
    coordenador = get_object_or_404(Coordenador, id=coordenador_id)
    user = coordenador.user  # pega o User para exclusão e nome no template

    if request.method == 'POST':
        user.delete()  # deleta o usuário vinculado (e o coordenador em cascata, se estiver certo)
        messages.success(request, f"Coordenador(a) {user.nome_completo} excluído com sucesso!")
        return redirect('escola_dashboard')

    return render(request, 'diverge/excluir_coordenador.html', {'coordenador': coordenador})


def logout_view(request):
    logout(request)
    return redirect('login_escola')

@login_required(login_url='login_escola') 
def home(request):
    return render(request, 'diverge/home.html')

@login_required(login_url='login_escola') 
def sobre(request):
    return render(request, 'diverge/sobre.html')

@login_required(login_url='login_escola') 
def saiba_mais(request):
    return render(request, 'diverge/saiba_mais.html')

@login_required(login_url='login_escola') 
def iniciar_teste(request):
    # Gera um ID único para a sessão do teste
    sessao_id = str(uuid.uuid4())
    request.session['sessao_id'] = sessao_id
    request.session['pergunta_atual'] = 0
    return render(request, 'diverge/perguntas_intro.html')

@login_required(login_url='login_escola') 
def pergunta(request):
    perguntas = list(Pergunta.objects.all().order_by('ordem').values_list('id', 'texto'))
    
    pergunta_atual = request.session.get('pergunta_atual', 0)

    if request.method == 'POST':
        valor = request.POST.get('valor')
        pergunta_id = perguntas[pergunta_atual][0]
        sessao_id = request.session.get('sessao_id')
        acao = request.POST.get('acao') # você usou 'acao' mas ainda não tinha capturado ela, né?

        if valor:
            Resposta.objects.create(
                pergunta_id=pergunta_id,
                valor=int(valor),
                sessao=sessao_id
            )
            
            if acao == 'proxima':
                request.session['pergunta_atual'] = pergunta_atual + 1
            elif acao == 'voltar' and pergunta_atual > 0:
                request.session['pergunta_atual'] = pergunta_atual - 1
                
            if pergunta_atual + 1 >= len(perguntas) and acao == 'proxima':
                return redirect('resultado')
                
            return redirect('pergunta')
    
    if pergunta_atual < len(perguntas):
        progresso = int((pergunta_atual / len(perguntas)) * 100)
        return render(request, 'diverge/pergunta.html', {
            'pergunta': perguntas[pergunta_atual],
            'progresso': progresso,
            'total_perguntas': len(perguntas),
            'pergunta_atual': pergunta_atual + 1,
            'mostrar_voltar': pergunta_atual > 0,
        })
    
    return redirect('resultado')

def calcular_descricao(percentual, neurodivergencia):
    if percentual >= 75:
        return f"Fortes indícios de {neurodivergencia.nome}"
    elif percentual >= 50:
        return f"Alguns indícios de {neurodivergencia.nome}"
    else:
        return f"Poucos ou nenhum indício de {neurodivergencia.nome}"

def calcular_indicios(percentual):
    if percentual >= 75:
        return "Alto"
    elif percentual >= 50:
        return "Moderado"
    else:
        return "Baixo"
    
@login_required(login_url='login_escola') 
def resultado(request):
    sessao_id = request.session.get('sessao_id')
    respostas = Resposta.objects.filter(sessao=sessao_id)
    
    resultados = {}
    neurodivergencias = Neurodivergencia.objects.all()
    
    for nd in neurodivergencias:
        pontos = 0
        pontos_max = 0
        
        for resp in respostas:
            try:
                rel = PerguntaNeurodivergencia.objects.get(
                    pergunta=resp.pergunta,
                    neurodivergencia=nd
                )
                pontos += resp.valor * rel.peso
                pontos_max += 4 * rel.peso  # 4 é o valor máximo (Sempre)
            except PerguntaNeurodivergencia.DoesNotExist:
                continue
        
        if pontos_max > 0:
            percentual = (pontos / pontos_max) * 100
        else:
            percentual = 0
            
        resultados[nd.nome] = {
            'percentual': percentual,
            'descricao': calcular_descricao(percentual, nd),
            'indicios': calcular_indicios(percentual)
        }
    
    return render(request, 'diverge/resultado.html', {'resultados': resultados})

@login_required(login_url='login_escola') 
def faqs(request):
    return render(request, 'diverge/faqs.html')

@login_required(login_url='login_escola') 
def privacidade(request):
    return render(request, 'diverge/privacidade.html')

@login_required(login_url='login_escola') 
def contato(request):
    return render(request, 'diverge/contato.html')