"""
Prueba simple sin cerrar el servidor
"""
import httpx
import asyncio
import json

async def test_api():
    async with httpx.AsyncClient() as client:
        try:
            # Probar el endpoint básico
            response = await client.get("http://localhost:8000/docs")
            print(f"Docs endpoint: {response.status_code}")
            
            # Probar el chat
            test_data = {
                "message": "Tengo dolor de cabeza",
                "conversation_id": "test123"
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/chat/message",
                json=test_data,
                timeout=10.0
            )
            
            print(f"Chat endpoint: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Respuesta: {result['response'][:100]}...")
                print(f"🚨 Severidad: {result.get('severity_assessment')}")
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())