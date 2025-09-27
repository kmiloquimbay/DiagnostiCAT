"""
Prueba directa de NVIDIA Nemotron para DiagnostiCAT
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(__file__))

async def test_nemotron_connection():
    """Prueba la conexión con NVIDIA Nemotron"""
    print("🧪 Probando conexión con NVIDIA Nemotron...")
    
    try:
        from app.services.nemotron_service import nemotron_service
        from app.core.config import settings
        
        print(f"🔑 API Key configurada: {'✅' if settings.NVIDIA_API_KEY else '❌'}")
        print(f"🌐 Base URL: {settings.NVIDIA_BASE_URL}")
        print(f"🤖 Modelo: {settings.NEMOTRON_MODEL}")
        
        if not nemotron_service.is_available():
            print("❌ Servicio no disponible - verificar API Key")
            return False
        
        # Prueba básica
        response = await nemotron_service.generate_response(
            prompt="Hola, ¿cómo estás?",
            system_prompt="Eres un asistente médico amigable. Responde brevemente."
        )
        print("✅ Conexión exitosa!")
        print(f"📝 Respuesta de prueba: {response[:100]}...")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

async def test_medical_consultation():
    """Prueba una consulta médica completa"""
    print("\n🏥 Probando consulta médica...")
    
    from app.services.nemotron_service import nemotron_service
    
    test_cases = [
        {
            "message": "Tengo dolor de cabeza fuerte y fiebre desde hace 2 días",
            "agent_type": "medico_general",
            "description": "Síntomas gripales"
        },
        {
            "message": "Mi bebé de 6 meses tiene fiebre alta y no quiere comer",
            "agent_type": "triage", 
            "description": "Emergencia pediátrica"
        },
        {
            "message": "Siento dolor en el pecho cuando camino",
            "agent_type": "triage",
            "description": "Posible problema cardíaco"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔬 CASO {i}: {case['description']}")
        print(f"💬 Consulta: {case['message']}")
        
        try:
            response = await nemotron_service.generate_medical_response(
                patient_message=case['message'],
                agent_type=case['agent_type']
            )
            
            print("✅ Respuesta recibida:")
            print(f"🤖 Diagnóstico: {response['response'][:200]}...")
            print(f"🚨 Urgencia: {response.get('urgency_level', 'N/A')}")
            print(f"📋 Recomendaciones: {len(response.get('recommendations', []))} encontradas")
            
            if response.get('recommendations'):
                for j, rec in enumerate(response['recommendations'][:2], 1):
                    print(f"   {j}. {rec}")
            
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
        
        print("-" * 60)

async def main():
    """Función principal de pruebas"""
    print("🚀 PRUEBAS DE NVIDIA NEMOTRON PARA DIAGNOSTICAT")
    print("=" * 60)
    
    # Prueba de conexión
    connection_ok = await test_nemotron_connection()
    
    if connection_ok:
        # Pruebas de consultas médicas
        await test_medical_consultation()
        
        print("\n🎉 ¡Todas las pruebas completadas!")
        print("\n💡 El sistema está listo para usar NVIDIA Nemotron")
        print("🏥 Puedes iniciar DiagnostiCAT con: python main.py")
    else:
        print("\n⚠️  Configuración necesaria:")
        print("1. Verificar NVIDIA_API_KEY en el archivo .env")
        print("2. Comprobar conexión a internet")
        print("3. Validar que la API Key sea correcta")

if __name__ == "__main__":
    asyncio.run(main())