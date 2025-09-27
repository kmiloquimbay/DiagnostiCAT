"""
Verificar modelos disponibles en NVIDIA API
"""
import httpx
import asyncio
import json
from app.core.config import settings

async def list_nvidia_models():
    """Lista los modelos disponibles en NVIDIA API"""
    print("🔍 Consultando modelos disponibles en NVIDIA API...")
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.NVIDIA_BASE_URL}/models",
                headers=headers
            )
            
            if response.status_code == 200:
                models = response.json()
                print("✅ Modelos disponibles:")
                for model in models.get("data", []):
                    print(f"   📦 {model.get('id', 'N/A')}")
                    if model.get("description"):
                        print(f"      {model['description'][:100]}...")
                return models
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error consultando modelos: {e}")
        return None

async def test_specific_model(model_id: str):
    """Prueba un modelo específico"""
    print(f"\n🧪 Probando modelo: {model_id}")
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": "Hola, responde brevemente"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NVIDIA_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"   ✅ Respuesta: {content[:100]}...")
                return True
            else:
                print(f"   ❌ Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    """Función principal"""
    print("🔧 NVIDIA API - VERIFICACIÓN DE MODELOS")
    print("=" * 50)
    
    # Listar modelos disponibles
    models = await list_nvidia_models()
    
    if models:
        # Probar algunos modelos comunes
        common_models = [
            "nvidia/nemotron-4-340b-instruct",
            "meta/llama-3.1-8b-instruct",
            "microsoft/phi-3-mini-4k-instruct",
            "mistralai/mixtral-8x7b-instruct-v0.1"
        ]
        
        print(f"\n🧪 Probando modelos comunes...")
        for model in common_models:
            working = await test_specific_model(model)
            if working:
                print(f"\n✅ MODELO FUNCIONAL ENCONTRADO: {model}")
                print(f"💡 Actualiza NEMOTRON_MODEL={model} en .env")
                break
    
    print("\n🔍 Si ningún modelo funciona, verifica:")
    print("1. La API Key es válida")
    print("2. Tienes acceso a los modelos")
    print("3. La URL base es correcta")

if __name__ == "__main__":
    asyncio.run(main())