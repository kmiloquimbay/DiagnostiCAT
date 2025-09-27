"""
Servicio para integración con NVIDIA Nemotron
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class NemotronService:
    """Servicio para interactuar con NVIDIA Nemotron API"""
    
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.NEMOTRON_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        if not self.api_key:
            logger.warning("NVIDIA API Key no configurada")
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Genera una respuesta usando NVIDIA Nemotron
        
        Args:
            prompt: El prompt del usuario
            system_prompt: Prompt del sistema (opcional)
            temperature: Temperatura para la generación (opcional)
            max_tokens: Máximo número de tokens (opcional)
            
        Returns:
            Respuesta generada por el modelo
        """
        if not self.api_key:
            return "Error: NVIDIA API Key no configurada"
        
        try:
            # Preparar los mensajes
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Preparar payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": False
            }
            
            # Headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Realizar llamada HTTP
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Error de API NVIDIA: {response.status_code} - {response.text}")
                    return f"Error de API: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Error llamando a NVIDIA Nemotron: {str(e)}")
            return f"Error interno: {str(e)}"
    
    async def generate_medical_response(
        self, 
        patient_message: str, 
        agent_type: str = "medico_general",
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta médica específica
        
        Args:
            patient_message: Mensaje del paciente
            agent_type: Tipo de agente médico
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Respuesta médica estructurada
        """
        
        # System prompts por tipo de agente
        system_prompts = {
            "medico_general": """Eres un médico general con amplia experiencia. Tu objetivo es:
1. Analizar los síntomas del paciente de forma empática y profesional
2. Proporcionar orientación médica inicial basada en evidencia
3. Clasificar el nivel de urgencia (bajo/medio/alto)
4. Dar recomendaciones específicas
5. Indicar cuándo buscar atención médica presencial

IMPORTANTE: Siempre recuerda que eres un sistema de orientación, no reemplazas una consulta médica real.
Responde en español, de forma clara y empática.""",

            "triage": """Eres una enfermera especializada en triaje con experiencia en clasificación de urgencias. Tu rol es:
1. Evaluar rápidamente la gravedad de los síntomas
2. Clasificar la urgencia: ALTA (emergencia), MEDIA (consulta pronto), BAJA (cuidados básicos)
3. Determinar si requiere atención inmediata
4. Proporcionar primeros auxilios básicos si es necesario
5. Tranquilizar al paciente mientras das orientación clara

Responde de forma concisa pero completa, en español.""",

            "pediatra": """Eres un pediatra especializado en el cuidado de niños y bebés. Tu enfoque es:
1. Evaluar síntomas pediátricos con especial cuidado
2. Considerar las diferencias por edad (bebés, niños, adolescentes)
3. Orientar a los padres de forma comprensible
4. Ser extra cauteloso con signos de alarma en menores
5. Proporcionar recomendaciones apropiadas por edad

Responde con empatía especial hacia los padres preocupados, en español."""
        }
        
        system_prompt = system_prompts.get(agent_type, system_prompts["medico_general"])
        
        # Construir el prompt completo
        full_prompt = f"""
Paciente consulta: {patient_message}

Por favor proporciona:
1. Análisis de síntomas
2. Posibles causas (sin dar diagnósticos definitivos)
3. Nivel de urgencia (bajo/medio/alto)
4. Recomendaciones específicas
5. Cuándo buscar atención médica

Formato de respuesta JSON:
{{
    "response": "Tu respuesta médica empática y profesional",
    "urgency_level": "bajo/medio/alto",
    "recommendations": ["recomendación 1", "recomendación 2", "..."],
    "when_to_seek_help": "Indicaciones de cuándo buscar atención médica",
    "disclaimer": "Recordatorio de que esto es orientación, no diagnóstico"
}}
"""
        
        try:
            # Generar respuesta
            raw_response = await self.generate_response(
                prompt=full_prompt,
                system_prompt=system_prompt
            )
            
            # Intentar parsear como JSON
            try:
                structured_response = json.loads(raw_response)
                return structured_response
            except json.JSONDecodeError:
                # Si no es JSON válido, crear estructura básica
                return {
                    "response": raw_response,
                    "urgency_level": "medio",
                    "recommendations": ["Consultar con médico si los síntomas persisten"],
                    "when_to_seek_help": "Si los síntomas empeoran o no mejoran en 24-48 horas",
                    "disclaimer": "Esta es una orientación inicial. Para diagnóstico y tratamiento definitivo, consulte a un profesional médico."
                }
                
        except Exception as e:
            logger.error(f"Error generando respuesta médica: {str(e)}")
            return {
                "response": "Lo siento, no pude procesar tu consulta en este momento. Por favor, contacta a un profesional médico.",
                "urgency_level": "medio",
                "recommendations": ["Consultar con un médico"],
                "when_to_seek_help": "Lo antes posible si los síntomas son preocupantes",
                "disclaimer": "Sistema temporalmente no disponible. Busque atención médica si tiene síntomas preocupantes."
            }
    
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible"""
        return bool(self.api_key)


# Instancia global
nemotron_service = NemotronService()