from src.etl.dim_docentes import dimension_docentes
from src.etl.dim_programas import dimension_programas
from src.etl.fact_programacion import fact_programacion

def ejecutar_todo():
    print("--- 🏁 INICIANDO PROCESO DE ACTUALIZACIÓN UPN ---")
    
    try:
        dimension_docentes()
        
        dimension_programas()

        fact_programacion()

        print("\n--- ✅ PROCESO COMPLETADO EXITOSAMENTE ---")
    except Exception as e:
        print(f"\n--- ❌ ERROR CRÍTICO EN EL PROCESO: {e} ---")

if __name__ == "__main__":
    ejecutar_todo()