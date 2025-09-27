"""
Prueba rápida de la API con el error corregido
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_medical_chat():
    """Prueba el endpoint de chat médico"""
    print("🧪 Probando chat médico con error corregido...")
    
    # Caso de prueba
    test_data = {
        "message": "Tengo dolor de cabeza fuerte y fiebre desde hace 2 días",
        "conversation_id": "test_conversation",
        "patient_context": {
            "age": 30,
            "gender": "masculino"
        }
    }
    
    try:
        print(f"📤 Enviando consulta: {test_data['message']}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message", 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ ¡Chat médico funcionando correctamente!")
            print(f"🤖 Respuesta: {result['response'][:150]}...")
            print(f"🚨 Severidad: {result.get('severity_assessment', 'N/A')}")
            print(f"📊 Confianza: {result.get('confidence_score', 'N/A')}")
            
            if result.get('suggestions'):
                print(f"💡 Sugerencias: {len(result['suggestions'])} encontradas")
                
            return True
        else:
            print(f"❌ Error {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_server_health():
    """Verifica que el servidor esté respondiendo"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor respondiendo correctamente")
            return True
        else:
            print(f"⚠️ Servidor responde con código {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN RÁPIDA - ERROR CORREGIDO")
    print("=" * 50)
    
    # Verificar servidor
    if not test_server_health():
        print("\n💡 Inicia el servidor con: python main.py")
        return
    
    print("\n🔧 Esperando 2 segundos para que el servidor esté listo...")
    time.sleep(2)
    
    # Probar chat médico
    success = test_medical_chat()
    
    if success:
        print("\n🎉 ¡TODO FUNCIONA CORRECTAMENTE!")
        print("\n💡 Ahora puedes:")
        print("   🌐 Usar la interfaz web: http://localhost:8000/docs")
        print("   📱 Probar diferentes casos médicos")
        print("   🤖 Ver respuestas de IA médica inteligente")
    else:
        print("\n❌ Aún hay problemas. Revisa los logs del servidor.")

if __name__ == "__main__":
    main()