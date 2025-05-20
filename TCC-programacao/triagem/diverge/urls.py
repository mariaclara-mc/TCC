from django.urls import path
from django.shortcuts import redirect
from . import views
  

urlpatterns = [
    path('dashboard/superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('cadastrar-escola/', views.cadastrar_escola, name='cadastrar_escola'),
    path('escola/editar/<int:pk>/', views.editar_escola, name='editar_escola'),
    path('login/escola/', views.login_escola, name='login_escola'),
    path('', lambda request: redirect('login_escola')),  # Redireciona corretamente para o login da escola
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registrar/', views.choose_registration, name='choose_registration'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/coordinator/', views.register_coordinator, name='register_coordinator'),
    path('verify_code/<int:coordenador_id>/', views.verificar_codigo, name='verificar_codigo'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('escola/dashboard/', views.escola_dashboard, name='escola_dashboard'),
    path('aluno/editar/<int:pk>/', views.editar_aluno, name='editar_aluno'),
    path('adicionar-aluno/', views.adicionar_aluno, name='adicionar_aluno'),
    path('excluir-aluno/<int:aluno_id>/', views.excluir_aluno, name='excluir_aluno'),
    path('editar_coordenador/<int:pk>/', views.editar_coordenador, name='editar_coordenador'),
    path('excluir_coordenador/<int:coordenador_id>/', views.excluir_coordenador, name='excluir_coordenador'),
    path('home/', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('saiba-mais/', views.saiba_mais, name='saiba_mais'),
    path('perguntas/', views.iniciar_teste, name='iniciar_teste'),
    path('pergunta/', views.pergunta, name='pergunta'),
    path('resultado/', views.resultado, name='resultado'),
    path('faqs/', views.faqs, name='faqs'),
    path('privacidade/', views.privacidade, name='privacidade'),
    path('contato/', views.contato, name='contato'),
]
