def calcular_coeficiente_k(encuesta):
    """Calcula el coeficiente de experticidad"""
    # Fórmula simplificada
    pesos = {
        'analisis_teoricos': 0.20,
        'experiencia': 0.15,
        'autores_nacionales': 0.10,
        'autores_extranjeros': 0.15,
        'conocimiento_extranjero': 0.20,
        'intuicion': 0.10,
        'conocimiento_materia': 0.10
    }
    
    try:
        # Convertir letras a valores numéricos (A=10, M=7, B=4)
        valor_influencia = {
            'A': 3.0,  # Alto
            'M': 2.0,  # Medio
            'B': 1.0   # Bajo
        }
        
        total = 0
        
        # Sumar influencias
        total += valor_influencia.get(encuesta.influencia_analisis_teoricos, 2) * pesos['analisis_teoricos']
        total += valor_influencia.get(encuesta.influencia_experiencia, 2) * pesos['experiencia']
        total += valor_influencia.get(encuesta.influencia_autores_nacionales, 2) * pesos['autores_nacionales']
        total += valor_influencia.get(encuesta.influencia_autores_extranjeros, 2) * pesos['autores_extranjeros']
        total += valor_influencia.get(encuesta.influencia_conocimiento_extranjero, 2) * pesos['conocimiento_extranjero']
        total += valor_influencia.get(encuesta.influencia_intuicion, 2) * pesos['intuicion']
        
        # Conocimiento de materia (0-10)
        total += (encuesta.conocimiento_materia / 10) * pesos['conocimiento_materia']
        
        # Normalizar a 0-100
        encuesta.coeficiente_k = round(total * 100 / 3, 2)
        
    except:
        encuesta.coeficiente_k = 0.00
    
    return encuesta