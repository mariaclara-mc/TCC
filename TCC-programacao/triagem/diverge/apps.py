from django.apps import AppConfig

class DivergeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diverge'

    def ready(self):
        import diverge.signals  # substitua pelo nome do arquivo onde está o post_save