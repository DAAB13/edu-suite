import os
from groq import Groq
from dotenv import load_dotenv
from src.core.config_loader import BASE_DIR

# Cargamos las variables de entorno (.env)
load_dotenv(BASE_DIR / ".env")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def redactar_resumen_semanal(df_reporte, kpis):
    """
    Usa IA para redactar un mensaje ejecutivo basado en las métricas e incidencias.
    """
    # Filtramos solo las filas que tienen una reprogramación anotada
    repros = df_reporte[df_reporte['DETALLE'] != ""].to_dict(orient='records')
    
    # Preparamos el contexto para la IA
    prompt = f"""
    Eres un Consultor Senior en Operaciones Académicas. Redacta un mensaje para William Cruzado.
    
    RESUMEN DE LA SEMANA:
    - Total de clases dictadas: {kpis['dictadas']}
    - Total de reprogramaciones: {kpis['reprogramadas']}
    
    DETALLE DE REPROGRAMACIONES:
    {repros}
    
    REGLAS:
    1. Empieza con "Estimado William,".
    2. Sé extremadamente breve y directo (máximo 4 líneas).
    3. Usa los números absolutos de las métricas.
    4. Si hay reprogramaciones, menciona el curso y el motivo brevemente.
    5. NO incluyas firmas ni despedidas.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3 # Mayor precisión, menos "creatividad"
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ No se pudo generar el texto de IA: {e}"