"""
Implementaciones específicas de agentes médicos con Nemotron.
"""

from typing import List, Dict, Any, Optional
import time

from app.agents.base_agent import BaseAgent
from app.models.medical_models import MessageModel, Severity
from app.models.agent_models import AgentType, AgentResponse
from app.services.nemotron_service import nemotron_service


class GeneralPractitionerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Dr. García - Médico General",
            agent_type=AgentType.GENERAL_PRACTITIONER,
            system_prompt="""Eres el Dr. García, un médico general experimentado y empático con 15 años de experiencia en atención primaria y medicina de urgencias.

Tu objetivo es:
1. Escuchar atentamente las preocupaciones del paciente
2. Evaluar la urgencia médica de la situación
3. Realizar una anamnesis estructurada mediante preguntas específicas
4. Proporcionar orientación médica inicial responsable
5. Identificar signos de alarma que requieran atención inmediata
6. Recomendar el nivel de atención apropiado (urgente, programada, autocuidado)

EVALUACIÓN DE URGENCIA:
- CRÍTICA: Riesgo de vida inmediato → Emergencias YA
- ALTA: Requiere atención urgente < 1 hora → Urgencias
- MEDIA: Puede esperar pero necesita atención < 24 horas → Consulta programada
- BAJA: Síntomas leves → Autocuidado y seguimiento

IMPORTANTE:
- Nunca des diagnósticos definitivos por chat
- Siempre recomienda evaluación presencial para síntomas serios
- Mantén un tono profesional, cálido y empático
- Haz preguntas específicas sobre síntomas: localización, duración, intensidad, factores que mejoran/empeoran
- Considera siempre el contexto del paciente (edad, antecedentes, medicamentos)
- Si detectas signos de alarma, sé directo sobre la necesidad de atención inmediata

Responde en español de manera clara y comprensible para cualquier paciente.""",
            specialties=["Medicina General", "Atención Primaria", "Medicina de Urgencias", "Evaluación Clínica"],
            temperature=0.7,
            max_tokens=800,
        )

    async def process_message(
        self,
        message: str,
        conversation_history: List[MessageModel],
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        start_time = time.time()
        
        # Preparar historial para LLM
        llm_history = []
        for msg in conversation_history[-5:]:  # Últimos 5 mensajes
            llm_history.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
        
        # Agregar contexto del paciente al prompt si existe
        enhanced_prompt = self.system_prompt
        if patient_context:
            context_info = []
            for key, value in patient_context.items():
                if value:
                    context_info.append(f"{key}: {value}")
            if context_info:
                enhanced_prompt += f"\n\nCONTEXTO DEL PACIENTE:\n" + "\n".join(context_info)
        
        # Llamar al servicio Nemotron
        llm_response = await nemotron_service.generate_medical_response(
            patient_message=message,
            agent_type="medico_general",
            conversation_history=llm_history
        )
        
        processing_time = time.time() - start_time
        confidence_score = self._calculate_confidence_score(
            llm_response["response"], len(message), bool(patient_context)
        )
        
        self.conversation_count += 1
        
        return AgentResponse(
            agent_id=self.id,
            agent_type=self.agent_type,
            response_text=llm_response["response"],
            confidence_score=confidence_score,
            processing_time=processing_time,
            tokens_used=llm_response.get("tokens_used", 0),
            urgency_level=llm_response.get("urgency_level", "medio"),
            recommendations=llm_response.get("recommendations", []),
        )


    async def assess_urgency(self, message: str, context: Dict[str, Any]) -> Severity:
        """Evalúa urgencia usando LLM en lugar de palabras clave"""
        
        urgency_prompt = """Eres un médico general con experiencia en evaluación de urgencias. Evalúa ÚNICAMENTE el nivel de urgencia médica basándote en los síntomas descritos.

NIVELES DE URGENCIA:
- CRITICAL: Riesgo de vida inmediato (paro cardíaco, dificultad respiratoria severa, pérdida de consciencia, sangrado masivo, shock)
- HIGH: Requiere atención urgente <1 hora (dolor torácico, dificultad respirar moderada, sangrado abundante, dolor abdominal severo, fiebre >40°C)
- MEDIUM: Puede esperar pero necesita atención <24 horas (fiebre alta, vómitos persistentes, dolor intenso pero estable)
- LOW: No urgente, puede programarse (síntomas leves, consultas rutinarias, seguimientos)

Considera la edad del paciente y antecedentes médicos. Ante cualquier duda, escala a mayor prioridad.

Responde SOLO con una palabra: CRITICAL, HIGH, MEDIUM o LOW.

No des explicaciones, no hagas preguntas, solo evalúa la urgencia."""

        context_info = ""
        if context:
            context_parts = []
            for key, value in context.items():
                if value:
                    context_parts.append(f"{key}: {value}")
            if context_parts:
                context_info = f"\nContexto del paciente: {', '.join(context_parts)}"

        full_message = f"Síntomas: {message}{context_info}"
        
        try:
            llm_response = await nemotron_service.generate_response(
                prompt=full_message,
                system_prompt=urgency_prompt
            )
            
            urgency_text = llm_response.strip().upper()
            
            # Mapear respuesta a enum
            if "CRITICAL" in urgency_text:
                return Severity.CRITICAL
            elif "HIGH" in urgency_text:
                return Severity.HIGH
            elif "MEDIUM" in urgency_text:
                return Severity.MEDIUM
            else:
                return Severity.LOW
                
        except Exception:
            # Solo en caso de error técnico, usar evaluación básica
            m = message.lower()
            if any(k in m for k in ["no puedo respirar", "dolor pecho severo", "perdí conocimiento"]):
                return Severity.HIGH
            elif any(k in m for k in ["dolor pecho", "fiebre alta", "sangrado"]):
                return Severity.MEDIUM
            else:
                return Severity.LOW


class TriageNurseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Enfermera Ana - Triaje",
            agent_type=AgentType.TRIAGE_NURSE,
            system_prompt="""Eres Ana, una enfermera especializada en triaje con 10 años de experiencia en servicios de urgencias.

Tu rol principal es:
1. Evaluar rápidamente la urgencia médica de cada consulta
2. Clasificar pacientes según prioridad de atención
3. Identificar emergencias que requieren atención inmediata
4. Proporcionar primeros auxilios básicos cuando sea apropiado
5. Tranquilizar a pacientes ansiosos mientras evalúas

SISTEMA DE TRIAJE:
🔴 URGENCIA CRÍTICA (Rojo): Riesgo de vida inmediato
- Dificultad respiratoria severa
- Dolor de pecho con síntomas cardíacos
- Pérdida de consciencia
- Hemorragias severas
- Síntomas de ACV

🟡 URGENCIA ALTA (Amarillo): Requiere atención urgente < 1 hora
- Dolor intenso
- Fiebre muy alta (>39°C)
- Vómitos persistentes
- Lesiones moderadas

🟢 URGENCIA MEDIA (Verde): Puede esperar < 4 horas
- Síntomas molestos pero estables
- Fiebres moderadas
- Dolores leves a moderados

⚪ URGENCIA BAJA (Blanco): No urgente, puede esperar
- Síntomas menores
- Consultas preventivas
- Molestias leves

IMPORTANTE:
- Sé eficiente pero empática
- Haz preguntas directas y específicas
- Si hay duda, siempre clasifica como más urgente
- Mantén la calma y transmite confianza
- Explica claramente los próximos pasos

Responde en español de forma clara y profesional.""",
            specialties=["Triaje", "Cuidados de Urgencia", "Primeros Auxilios", "Evaluación Rápida"],
            temperature=0.6,
            max_tokens=600,
        )

    async def process_message(
        self,
        message: str,
        conversation_history: List[MessageModel],
        patient_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        start_time = time.time()
        
        # Preparar historial limitado para triaje rápido
        llm_history = []
        for msg in conversation_history[-3:]:  # Solo últimos 3 mensajes para triaje rápido
            llm_history.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
        
        # Agregar contexto crítico del paciente
        enhanced_prompt = self.system_prompt
        if patient_context:
            critical_info = []
            for key, value in patient_context.items():
                if key in ["edad", "medicamentos", "alergias", "condiciones_preexistentes"] and value:
                    critical_info.append(f"{key}: {value}")
            if critical_info:
                enhanced_prompt += f"\n\nINFORMACIÓN CRÍTICA DEL PACIENTE:\n" + "\n".join(critical_info)
        
        # Llamar al servicio Nemotron con foco en triaje
        llm_response = await nemotron_service.generate_medical_response(
            patient_message=message,
            agent_type="triage",
            conversation_history=llm_history
        )
        
        processing_time = time.time() - start_time
        confidence_score = self._calculate_confidence_score(
            llm_response["response"], len(message), bool(patient_context)
        )
        
        self.conversation_count += 1
        
        return AgentResponse(
            agent_id=self.id,
            agent_type=self.agent_type,
            response_text=llm_response["response"],
            confidence_score=confidence_score,
            processing_time=processing_time,
            tokens_used=llm_response.get("tokens_used", 0),
            urgency_level=llm_response.get("urgency_level", "medio"),
            recommendations=llm_response.get("recommendations", []),
        )

    async def assess_urgency(self, message: str, context: Dict[str, Any]) -> Severity:
        """Evaluación de urgencia especializada para triaje"""
        urgency_prompt = """Eres una enfermera de triaje experta. Evalúa el nivel de urgencia basándote ÚNICAMENTE en los síntomas presentados.

CLASIFICACIÓN:
- CRITICAL: Riesgo de vida inmediato (dolor pecho + síntomas cardíacos, dificultad respiratoria severa, pérdida consciencia, hemorragia severa)
- HIGH: Urgente < 1 hora (dolor intenso, fiebre >39°C, vómitos persistentes, lesiones moderadas)
- MEDIUM: Puede esperar < 4 horas (síntomas molestos pero estables)
- LOW: No urgente (síntomas menores, molestias leves)

Responde SOLO con: CRITICAL, HIGH, MEDIUM o LOW"""

        context_info = ""
        if context:
            context_parts = []
            for key, value in context.items():
                if value and key in ["edad", "medicamentos", "alergias"]:  # Solo info crítica para triaje
                    context_parts.append(f"{key}: {value}")
            if context_parts:
                context_info = f"\nInfo crítica: {', '.join(context_parts)}"

        full_message = f"Síntomas: {message}{context_info}"
        
        try:
            llm_response = await nemotron_service.generate_response(
                prompt=full_message,
                system_prompt=urgency_prompt
            )
            
            urgency_text = llm_response.strip().upper()
            
            # Mapear respuesta a enum
            if "CRITICAL" in urgency_text or "CRÍTICO" in urgency_text:
                return Severity.CRITICAL
            elif "HIGH" in urgency_text or "ALTO" in urgency_text:
                return Severity.HIGH
            elif "MEDIUM" in urgency_text or "MEDIO" in urgency_text:
                return Severity.MEDIUM
            else:
                return Severity.LOW
                
        except Exception:
            # Evaluación de seguridad por palabras clave en caso de error
            m = message.lower()
            critical_keywords = ["no puedo respirar", "dolor pecho severo", "perdí conocimiento", 
                               "hemorragia", "convulsiones", "paro cardíaco"]
            high_keywords = ["dolor intenso", "fiebre alta", "vómito sangre", "desmayo"]
            
            if any(k in m for k in critical_keywords):
                return Severity.CRITICAL
            elif any(k in m for k in high_keywords):
                return Severity.HIGH
            elif any(k in m for k in ["dolor", "fiebre", "náuseas"]):
                return Severity.MEDIUM
            else:
                return Severity.LOW




