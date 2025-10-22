#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI client module for UnifyVision
Handles all interactions with OpenAI API (Responses API and Chat Completions)
"""

from typing import Optional
from openai import OpenAI

from .config import config
from .exceptions import OpenAIClientError
from .logger import logger
from .screen_capture import ScreenCapture


class OpenAIClient:
    """Wrapper for OpenAI API interactions"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (defaults to config.OPENAI_API_KEY)

        Raises:
            OpenAIClientError: If API key is not provided
        """
        api_key = api_key or config.OPENAI_API_KEY
        if not api_key:
            raise OpenAIClientError(
                "OpenAI API key not provided. "
                "Set OPENAI_API_KEY environment variable."
            )

        self.client = OpenAI(api_key=api_key)
        self.screen_capture = ScreenCapture()

    def ask_with_image(
        self,
        prompt: str,
        image_path: str,
        prompt_id: str = None,
        prompt_version: str = None
    ) -> str:
        """
        Sends a question with image using Responses API

        Args:
            prompt: The question text
            image_path: Path to image to analyze
            prompt_id: Prompt ID (defaults to config.PROMPT_ID)
            prompt_version: Prompt version (defaults to config.PROMPT_VERSION)

        Returns:
            Response text from the model

        Raises:
            OpenAIClientError: If API call fails
        """
        prompt_id = prompt_id or config.PROMPT_ID
        prompt_version = prompt_version or config.PROMPT_VERSION

        try:
            # Encode image to base64
            image_base64 = self.screen_capture.encode_image_to_base64(image_path)

            logger.debug("Sending request to Responses API...")

            # Use Responses API with saved prompt
            response = self.client.responses.create(
                prompt={
                    "id": prompt_id,
                    "version": prompt_version
                },
                input=[
                    {"role": "user", "content": prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{image_base64}"
                            }
                        ]
                    }
                ]
            )

            # Extract response
            response_text = response.output_text
            logger.debug("Response received from Responses API")

            return response_text

        except Exception as e:
            raise OpenAIClientError(f"Responses API call failed: {e}")

    def generate_plan(
        self,
        user_instruction: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Generates an action plan using Chat Completions API

        Args:
            user_instruction: User's task instruction
            model: Model to use (defaults to config.MODEL)
            temperature: Temperature setting (defaults to config.PLANNING_TEMPERATURE)
            max_tokens: Max tokens (defaults to config.MAX_TOKENS_PLANNING)

        Returns:
            Raw response text containing the plan

        Raises:
            OpenAIClientError: If API call fails
        """
        model = model or config.MODEL
        temperature = temperature or config.PLANNING_TEMPERATURE
        max_tokens = max_tokens or config.MAX_TOKENS_PLANNING

        prompt = f"""Sos un agente experto en automatización de interfaces gráficas. El usuario quiere realizar esta tarea:

"{user_instruction}"

Generá un plan DETALLADO y PRECISO de pasos para completar esta tarea. Devolvé ÚNICAMENTE un array JSON con los pasos.

PATRONES DE FLUJO COMUNES (usá estos como guía, NO copies literalmente):

1. ENVIAR EMAIL:
   Flujo típico: Botón para iniciar redacción → Campo destinatario → Campo asunto → Área de cuerpo → Botón envío
   Consideraciones:
   - El botón de redacción puede decir "Redactar", "Compose", "Nuevo", tener un ícono de lápiz, etc.
   - El campo destinatario suele decir "Para", "To", "Destinatario" o ser el primer input visible
   - Navegá con "tab" entre campos si están cerca
   - Esperá 1-2 segundos después de abrir el compositor para que cargue

2. BÚSQUEDA EN WEB:
   Flujo típico: Click en barra de búsqueda → Escribir query → Enter o botón buscar
   Consideraciones:
   - Algunos sitios tienen la búsqueda siempre visible, otros en un ícono de lupa

3. FORMULARIOS:
   Flujo típico: Rellenar campos en orden visual (arriba → abajo) → Botón submit al final
   Consideraciones:
   - Usá "tab" para avanzar entre campos
   - Los botones de envío suelen decir "Enviar", "Submit", "Guardar", "Continuar"

ACCIONES DISPONIBLES:
- click: hacer clic en un elemento (requiere "target" con descripción visual del elemento)
- type: escribir texto (requiere "text" con el contenido)
  - Parámetros opcionales:
    - "loop": true/false - escribir repetidamente
    - "loop_duration": segundos de duración del loop (default 5)
    - "delay_between": delay entre repeticiones (default 0.3)
- press: presionar una tecla (requiere "key" como "enter", "tab", "escape")
- wait: esperar N segundos (requiere "seconds")

FORMATO DE RESPUESTA (SOLO JSON, sin texto adicional):
[
  {{"action": "click", "target": "descripción visual del elemento"}},
  {{"action": "wait", "seconds": 1}},
  {{"action": "type", "text": "contenido"}},
  {{"action": "press", "key": "tab"}}
]

REGLAS IMPORTANTES:
- NO uses nombres exactos de botones, usá descripciones visuales genéricas ("botón para redactar email", "campo de texto para destinatario")
- Seguí el FLUJO LÓGICO del patrón correspondiente (no inventes pasos fuera de orden)
- Incluí "wait" después de acciones que pueden tardar (abrir modales, cargar formularios)
- Si necesitás escribir mucho texto, usá el parámetro "loop"

Generá el plan ahora siguiendo el patrón correspondiente:"""

        try:
            logger.debug(f"Generating plan with {model}...")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            response_text = response.choices[0].message.content.strip()
            logger.debug("Plan generated successfully")

            return response_text

        except Exception as e:
            raise OpenAIClientError(f"Plan generation failed: {e}")
