from django.shortcuts import render, redirect
from django.db.models import Count, Q
from ...forms import ProyectoForm
from ...models import Proyecto, Experto

def inicio_investigador(request):
    """Vista principal del investigador"""
    proyectos = Proyecto.objects.con_estadisticas()
    
    return render(request, 'investigadores/inicio.html', {
        'proyectos': proyectos
    })

def crear_proyecto(request):
    """Vista para crear un nuevo proyecto"""
    experto = Experto.objects.first()
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.investigador = experto
            proyecto.save()
            return redirect('app:inicio_investigador')
    else:
        form = ProyectoForm()

    return render(request, 'investigadores/crear_proyecto.html', {
        'form': form
    })