from django.shortcuts import render, get_object_or_404
from ...models import Experto

def dashboard_experto(request, experto_id):
    """Dashboard del experto. Toda la lógica está en el modelo."""
    experto = get_object_or_404(Experto, id=experto_id)
    
    contexto = experto.get_dashboard_data()
    
    return render(request, 'expertos/inicio_expertos.html', {
        'experto': experto,
        **contexto
    })