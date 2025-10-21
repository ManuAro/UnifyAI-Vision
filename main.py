#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Visual Autónomo - Multi-Step
Captura pantalla, planifica tareas y ejecuta acciones usando GPT-4o-mini
Compatible con macOS
"""

import os
import time
import json
import re
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Librerías instaladas
import mss
import pyautogui
from PIL import Image
from openai import OpenAI

# Configuración
SCREENSHOT_PATH = "screen.png"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = "asst_sBhlxpvUiVpmpHkhgbqcuGdD"  # ID del asistente para análisis visual

# Inicializar cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Variable global para mantener el thread activo durante toda la sesión
current_thread_id = None

# Configuración de seguridad para PyAutoGUI
pyautogui.FAILSAFE = True  # Mover mouse a esquina superior izquierda cancela
pyautogui.PAUSE = 0.5  # Pausa entre acciones

# Configuración de cuadrícula
GRID_COLS = 32  # Número de columnas en la cuadrícula
GRID_ROWS = 18  # Número de filas en la cuadrícula (32x18 = 576 celdas)


def obtener_escala_pantalla():
    """
    Detecta el factor de escala de la pantalla en macOS (Retina)
    Retorna el ratio entre píxeles físicos y píxeles lógicos
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        # Obtener tamaño real de captura
        ancho_real = monitor["width"]
        alto_real = monitor["height"]

    # Obtener tamaño lógico (lo que reporta pyautogui)
    tamaño_logico = pyautogui.size()
    ancho_logico = tamaño_logico.width
    alto_logico = tamaño_logico.height

    # Calcular factor de escala
    escala_x = ancho_real / ancho_logico
    escala_y = alto_real / alto_logico

    return escala_x, escala_y


def capturar_pantalla():
    """Captura la pantalla completa y guarda como screen.png"""
    print("👁️  Capturando pantalla completa...")

    with mss.mss() as sct:
        # En macOS, el monitor principal es el índice 1
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        # Guardar como PNG
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(SCREENSHOT_PATH)

    print(f"✅ Captura guardada: {SCREENSHOT_PATH}")
    return SCREENSHOT_PATH


def dibujar_grilla_en_imagen(ruta_imagen: str, output_path: str = "screen_grid.png") -> Tuple[str, int, int]:
    """
    Dibuja una grilla sobre la imagen y numera cada celda
    Retorna: (ruta_imagen_con_grilla, ancho_celda, alto_celda)
    """
    from PIL import ImageDraw, ImageFont

    # Abrir imagen
    img = Image.open(ruta_imagen)
    ancho_img, alto_img = img.size

    # Calcular tamaño de cada celda
    ancho_celda = ancho_img // GRID_COLS
    alto_celda = alto_img // GRID_ROWS

    # Crear capa de dibujo
    draw = ImageDraw.Draw(img)

    # Intentar cargar una fuente, o usar la default
    try:
        # Tamaño de fuente proporcional al tamaño de celda
        font_size = min(alto_celda, ancho_celda) // 3
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()

    # Dibujar grilla y números
    celda_num = 0
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # Calcular coordenadas de la celda
            x1 = col * ancho_celda
            y1 = row * alto_celda
            x2 = x1 + ancho_celda
            y2 = y1 + alto_celda

            # Dibujar borde de celda (línea delgada semi-transparente)
            draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 128), width=2)

            # Dibujar número de celda en el centro
            texto = str(celda_num)

            # Calcular posición centrada del texto
            try:
                bbox = draw.textbbox((0, 0), texto, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(texto) * 8
                text_height = 12

            text_x = x1 + (ancho_celda - text_width) // 2
            text_y = y1 + (alto_celda - text_height) // 2

            # Dibujar fondo semi-transparente para el número
            draw.rectangle(
                [text_x - 5, text_y - 2, text_x + text_width + 5, text_y + text_height + 2],
                fill=(255, 255, 255, 180)
            )

            # Dibujar número
            draw.text((text_x, text_y), texto, fill=(0, 0, 0), font=font)

            celda_num += 1

    # Guardar imagen con grilla
    img.save(output_path)
    print(f"  📊 Grilla dibujada: {GRID_COLS}x{GRID_ROWS} = {GRID_COLS * GRID_ROWS} celdas")
    print(f"  💾 Guardada en: {output_path}")

    return output_path, ancho_celda, alto_celda


def codificar_imagen_base64(ruta_imagen: str) -> str:
    """Convierte la imagen a base64 para enviarla a OpenAI"""
    with open(ruta_imagen, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def preguntar_al_asistente(prompt: str, ruta_imagen: str) -> str:
    """
    Envía una pregunta con imagen al asistente y espera la respuesta

    Args:
        prompt: El texto de la pregunta
        ruta_imagen: Ruta a la imagen a analizar

    Returns:
        La respuesta del asistente
    """
    global current_thread_id

    try:
        # Subir la imagen a OpenAI Files
        with open(ruta_imagen, "rb") as image_file:
            file_response = client.files.create(
                file=image_file,
                purpose="vision"
            )
        file_id = file_response.id
        print(f"  📤 Imagen subida: {file_id}")

        # Crear o reutilizar thread
        if current_thread_id is None:
            thread = client.beta.threads.create()
            current_thread_id = thread.id
            print(f"  🧵 Thread creado: {current_thread_id}")
        else:
            print(f"  🧵 Reutilizando thread: {current_thread_id}")

        # Crear mensaje con imagen
        message = client.beta.threads.messages.create(
            thread_id=current_thread_id,
            role="user",
            content=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_file",
                    "image_file": {"file_id": file_id}
                }
            ]
        )

        # Ejecutar el asistente
        run = client.beta.threads.runs.create(
            thread_id=current_thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Esperar a que complete
        print(f"  ⏳ Esperando respuesta del asistente...", end="", flush=True)
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=current_thread_id,
                run_id=run.id
            )
            print(".", end="", flush=True)
        print()

        if run.status == "completed":
            # Obtener mensajes
            messages = client.beta.threads.messages.list(
                thread_id=current_thread_id,
                order="desc",
                limit=1
            )

            # Extraer respuesta
            respuesta = messages.data[0].content[0].text.value

            # Limpiar archivo temporal
            try:
                client.files.delete(file_id)
            except:
                pass

            return respuesta
        else:
            print(f"  ❌ Run falló con estado: {run.status}")
            if hasattr(run, 'last_error') and run.last_error:
                print(f"  ❌ Error: {run.last_error}")
            return None

    except Exception as e:
        print(f"  ❌ Error al consultar asistente: {e}")
        import traceback
        traceback.print_exc()
        return None


def generar_plan_de_accion(instruccion_usuario: str) -> Optional[List[Dict]]:
    """
    Usa GPT-4o para generar un plan de pasos a partir de la instrucción del usuario
    """
    print(f"🧠 Generando plan de acción para: '{instruccion_usuario}'")

    prompt = f"""Sos un agente experto en automatización de interfaces gráficas. El usuario quiere realizar esta tarea:

"{instruccion_usuario}"

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Actualizado a gpt-4o-mini para planificación
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.2  # Menos temperatura para más precisión
        )

        respuesta = response.choices[0].message.content.strip()
        print(f"📋 Plan generado:\n{respuesta}\n")

        # Extraer JSON del texto
        match = re.search(r'\[.*\]', respuesta, re.DOTALL)
        if match:
            json_str = match.group(0)
            plan = json.loads(json_str)
            return plan
        else:
            print("⚠️  No se pudo extraer JSON del plan")
            return None

    except Exception as e:
        print(f"❌ Error al generar plan: {e}")
        return None


def buscar_elemento_con_grilla(ruta_imagen: str, descripcion_elemento: str) -> Optional[dict]:
    """
    Sistema de grilla mejorado: Identifica TODAS las celdas donde aparece el elemento
    y calcula un punto óptimo basado en el centroide ponderado por cobertura
    """
    print(f"  🔍 Buscando con sistema de grilla: '{descripcion_elemento}'")

    # Dibujar grilla en la imagen
    ruta_con_grilla, ancho_celda, alto_celda = dibujar_grilla_en_imagen(ruta_imagen)

    # Información de debug sobre la imagen
    img_debug = Image.open(ruta_con_grilla)
    print(f"  📐 Tamaño de imagen: {img_debug.size[0]}x{img_debug.size[1]} píxeles")
    print(f"  📐 Tamaño de celda: {ancho_celda}x{alto_celda} píxeles")
    print(f"  📐 Total de celdas: {GRID_COLS * GRID_ROWS}")

    # Prompt mejorado para identificar TODAS las celdas con el elemento
    prompt = f"""You are analyzing a screenshot with a NUMBERED GRID overlay (red grid with numbers).

YOUR TASK: Find the UI element "{descripcion_elemento}" and identify which GRID CELLS contain it.

GRID INFORMATION:
- Grid size: {GRID_COLS} columns × {GRID_ROWS} rows = {GRID_COLS * GRID_ROWS} cells total
- Cell numbering: 0 (top-left) to {GRID_COLS * GRID_ROWS - 1} (bottom-right)
- Each cell has a NUMBER written in it - READ THESE NUMBERS carefully

STEP 1: Briefly describe what you see in the screenshot (1-2 sentences)

STEP 2: Locate "{descripcion_elemento}" visually

STEP 3: Look at the RED NUMBERED GRID and identify:
   - Which cell numbers contain this element
   - What percentage of the element appears in each cell
   - Which cell has the CENTER/most important part of the element

RESPONSE FORMAT (JSON only):
{{
  "description": "Brief description of the screenshot",
  "found": true,
  "cells": [
    {{"cell_number": N, "coverage_percent": XX, "description": "center of button"}},
    {{"cell_number": M, "coverage_percent": YY, "description": "right edge of button"}}
  ],
  "primary_cell": N,
  "confidence": "high/medium/low",
  "reasoning": "The button is located in cells N, M, ... with the center in cell N"
}}

If NOT found:
{{
  "description": "Brief description of the screenshot",
  "found": false,
  "reasoning": "Why you couldn't find it"
}}

CRITICAL:
- READ the cell numbers from the grid overlay (don't estimate positions)
- List ALL cells where the element appears
- Identify which cell contains the clickable center of the element
- The system will calculate pixel coordinates from your cell numbers

Find "{descripcion_elemento}" now:"""

    try:
        # Usar el asistente para analizar la imagen
        respuesta = preguntar_al_asistente(prompt, ruta_con_grilla)

        if not respuesta:
            print("  ⚠️  No se obtuvo respuesta del asistente")
            return None

        print(f"  💬 Respuesta completa del asistente:")
        print(f"  {respuesta}")
        print()

        # Parsear JSON
        import json as json_lib
        match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if not match:
            print("  ⚠️  No se encontró JSON en la respuesta")
            return None

        datos = json_lib.loads(match.group(0))

        # Mostrar lo que el modelo vio
        if "description" in datos:
            print(f"  👁️  El modelo ve: {datos['description']}")

        if not datos.get("found", False):
            print(f"  ⚠️  Elemento no encontrado por el modelo")
            if "reasoning" in datos:
                print(f"  📝 Razón: {datos['reasoning']}")
            return None

        # Mostrar razonamiento si está disponible
        if "reasoning" in datos:
            print(f"  🧠 Razonamiento del modelo: {datos['reasoning']}")

        cells = datos.get("cells", [])
        if not cells:
            # Fallback al formato anterior (single cell)
            cell_number = datos.get("primary_cell") or datos.get("cell_number")
            if cell_number is None:
                print("  ⚠️  No se especificaron celdas")
                return None
            cells = [{"cell_number": cell_number, "coverage_percent": 100}]

        print(f"  📊 Celdas detectadas: {len(cells)}")
        for cell_info in cells:
            cell_num = cell_info.get("cell_number")
            coverage = cell_info.get("coverage_percent", "?")
            desc = cell_info.get("description", "")
            print(f"     • Celda {cell_num}: {coverage}% - {desc}")

        # Calcular centroide ponderado por cobertura
        total_weight = 0
        x_weighted = 0
        y_weighted = 0

        for cell_info in cells:
            cell_number = cell_info.get("cell_number")
            coverage = cell_info.get("coverage_percent", 50)  # Default 50%

            # Calcular coordenadas del centro de esta celda
            row = cell_number // GRID_COLS
            col = cell_number % GRID_COLS
            x_centro = (col * ancho_celda) + (ancho_celda // 2)
            y_centro = (row * alto_celda) + (alto_celda // 2)

            # Acumular con peso de cobertura
            weight = coverage / 100.0
            x_weighted += x_centro * weight
            y_weighted += y_centro * weight
            total_weight += weight

        # Calcular coordenadas finales ponderadas
        if total_weight > 0:
            x_final = int(x_weighted / total_weight)
            y_final = int(y_weighted / total_weight)
        else:
            # Fallback: usar la celda principal
            primary_cell = cells[0].get("cell_number")
            row = primary_cell // GRID_COLS
            col = primary_cell % GRID_COLS
            x_final = (col * ancho_celda) + (ancho_celda // 2)
            y_final = (row * alto_celda) + (alto_celda // 2)

        print(f"  ✅ Punto óptimo calculado (centroide ponderado): ({x_final}, {y_final})")
        print(f"  🎯 Confianza: {datos.get('confidence', 'N/A')}")

        # Retornar en formato compatible
        resultado = {
            "encontrado": True,
            "coordenadas_response": json_lib.dumps({"x": x_final, "y": y_final}),
            "x_directo": x_final,
            "y_directo": y_final,
            "cells": cells,
            "confidence": datos.get("confidence")
        }

        # Limpiar archivo temporal de grilla
        try:
            if os.path.exists(ruta_con_grilla):
                os.remove(ruta_con_grilla)
        except:
            pass

        return resultado

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        # Limpiar archivo temporal de grilla incluso si hay error
        try:
            if os.path.exists(ruta_con_grilla):
                os.remove(ruta_con_grilla)
        except:
            pass

        return None


def verificar_cambio_pantalla(ruta_antes: str, ruta_despues: str) -> bool:
    """
    Compara dos capturas de pantalla para verificar si hubo cambios significativos
    Retorna True si hay cambios (el clic tuvo efecto)
    """
    try:
        from PIL import ImageChops, ImageStat

        img_antes = Image.open(ruta_antes)
        img_despues = Image.open(ruta_despues)

        # Redimensionar si es necesario
        if img_antes.size != img_despues.size:
            img_despues = img_despues.resize(img_antes.size)

        # Calcular diferencia
        diff = ImageChops.difference(img_antes, img_despues)

        # Usar ImageStat para calcular la suma de diferencias
        stat = ImageStat.Stat(diff)
        suma_diff = sum(stat.sum)  # Suma de todos los canales RGB
        total_posible = img_antes.size[0] * img_antes.size[1] * 255 * 3  # width * height * max_value * channels

        porcentaje_cambio = (suma_diff / total_posible) * 100

        print(f"  📊 Cambio detectado: {porcentaje_cambio:.2f}%")

        # Considerar que hubo cambio si más del 0.1% de diferencia
        return porcentaje_cambio > 0.1

    except Exception as e:
        print(f"  ⚠️  No se pudo verificar cambios: {e}")
        return True  # Asumir que funcionó si no podemos verificar


def intentar_clicks_multiples(x_final: int, y_final: int, radio: int = 20) -> bool:
    """
    Intenta hacer clic en múltiples puntos alrededor de las coordenadas objetivo
    Patrón: centro primero, luego celdas adyacentes en todas direcciones

    El radio debe ser aproximadamente el tamaño de una celda para probar celdas vecinas
    """
    # Patrón de búsqueda: centro, luego 8 direcciones (celdas adyacentes)
    puntos = [
        (x_final, y_final, "centro (celda identificada)"),
        # Celdas adyacentes directas
        (x_final, y_final - radio, "celda superior"),
        (x_final, y_final + radio, "celda inferior"),
        (x_final - radio, y_final, "celda izquierda"),
        (x_final + radio, y_final, "celda derecha"),
        # Celdas diagonales
        (x_final - radio, y_final - radio, "celda superior-izquierda"),
        (x_final + radio, y_final - radio, "celda superior-derecha"),
        (x_final - radio, y_final + radio, "celda inferior-izquierda"),
        (x_final + radio, y_final + radio, "celda inferior-derecha"),
    ]

    print(f"  🎯 Patrón de clics: probando celda principal y celdas adyacentes")

    for i, (x, y, posicion) in enumerate(puntos):
        try:
            # Capturar pantalla ANTES del clic
            ruta_antes = f"before_click_{i}.png"
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img.save(ruta_antes)

            print(f"     {i+1}/9. Probando {posicion}: ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)
            pyautogui.doubleClick()  # Doble clic en lugar de clic simple
            time.sleep(0.7)  # Esperar a que se procese el clic

            # Capturar pantalla DESPUÉS del clic
            ruta_despues = f"after_click_{i}.png"
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img.save(ruta_despues)

            # Verificar si hubo cambios
            if verificar_cambio_pantalla(ruta_antes, ruta_despues):
                print(f"  ✅ ¡Clic exitoso en {posicion}!")
                # Limpiar archivos temporales
                try:
                    os.remove(ruta_antes)
                    os.remove(ruta_despues)
                except:
                    pass
                return True
            else:
                print(f"     ⚠️  Sin cambios en {posicion}, continuando...")

            # Limpiar archivos temporales
            try:
                os.remove(ruta_antes)
                os.remove(ruta_despues)
            except:
                pass

        except Exception as e:
            print(f"     ❌ Error en {posicion}: {e}")
            continue

    print(f"  ❌ No se detectaron cambios en ninguna celda (principal + 8 adyacentes)")
    return False


def ejecutar_accion_click(target: str) -> bool:
    """
    Ejecuta una acción de click: captura pantalla, busca elemento con cuadrícula, hace click
    Si falla, prueba celdas adyacentes automáticamente
    """
    print(f"🖱️  Acción CLICK")

    # Capturar pantalla actual
    ruta_captura = capturar_pantalla()

    # Obtener tamaño de imagen para calcular tamaño de celda
    img = Image.open(ruta_captura)
    ancho_img, alto_img = img.size
    ancho_celda = ancho_img // GRID_COLS
    alto_celda = alto_img // GRID_ROWS

    x_imagen = None
    y_imagen = None

    # Sistema de grilla ÚNICO
    print("  📊 Usando sistema de cuadrícula...")
    datos = buscar_elemento_con_grilla(ruta_captura, target)

    if datos:
        # Extraer coordenadas directas
        x_imagen = datos.get('x_directo')
        y_imagen = datos.get('y_directo')

    # Si el sistema de grilla falló, NO hay fallback - el sistema debe mejorar
    if x_imagen is None or y_imagen is None:
        print(f"  ❌ No se pudo encontrar: {target} en la cuadrícula")
        return False

    # Obtener factor de escala de la pantalla
    escala_x, escala_y = obtener_escala_pantalla()

    # Convertir coordenadas de imagen a coordenadas lógicas de pantalla
    x_final = int(x_imagen / escala_x)
    y_final = int(y_imagen / escala_y)

    print(f"  📐 Coordenadas imagen: ({x_imagen}, {y_imagen})")
    print(f"  📐 Factor escala: ({escala_x:.2f}x, {escala_y:.2f}x)")
    print(f"  📐 Coordenadas finales: ({x_final}, {y_final})")

    # Calcular radio basado en el tamaño de celda (usar el tamaño de celda lógica)
    radio = int((ancho_celda / escala_x + alto_celda / escala_y) / 2)
    print(f"  📐 Radio de búsqueda (tamaño de celda): {radio}px")

    # Intentar patrón de clics en la celda y celdas adyacentes
    try:
        exito = intentar_clicks_multiples(x_final, y_final, radio=radio)
        return exito
    except Exception as e:
        print(f"  ❌ Error al hacer click: {e}")
        return False


def ejecutar_accion_type(text: str, loop: bool = False, loop_duration: float = 5.0, delay_between: float = 0.3) -> bool:
    """
    Ejecuta una acción de escritura usando el portapapeles
    (Más confiable que pyautogui.write para caracteres especiales)

    Args:
        text: Texto a escribir
        loop: Si es True, escribe el texto repetidamente
        loop_duration: Duración en segundos del loop (default 5s)
        delay_between: Delay entre repeticiones en segundos (default 0.3s)
    """
    if loop:
        print(f"⌨️  Acción TYPE (LOOP): '{text}' durante {loop_duration}s")
    else:
        print(f"⌨️  Acción TYPE: '{text}'")

    try:
        import pyperclip

        def escribir_una_vez():
            # Copiar texto al portapapeles
            pyperclip.copy(text)
            # Pegar con Cmd+V
            pyautogui.hotkey('command', 'v')
            time.sleep(0.1)

        if loop:
            # Escribir en loop durante el tiempo especificado
            tiempo_inicio = time.time()
            repeticiones = 0

            while (time.time() - tiempo_inicio) < loop_duration:
                escribir_una_vez()
                repeticiones += 1
                time.sleep(delay_between)

            print(f"  ✅ Texto escrito {repeticiones} veces en {loop_duration}s")
        else:
            # Escribir una sola vez
            escribir_una_vez()
            print(f"  ✅ Texto pegado desde portapapeles")

        return True

    except ImportError:
        # Fallback si pyperclip no está disponible
        print("  ⚠️  pyperclip no disponible, usando método alternativo...")
        try:
            def escribir_char_por_char():
                for char in text:
                    pyautogui.press(char)
                    time.sleep(0.05)

            if loop:
                tiempo_inicio = time.time()
                repeticiones = 0

                while (time.time() - tiempo_inicio) < loop_duration:
                    escribir_char_por_char()
                    repeticiones += 1
                    time.sleep(delay_between)

                print(f"  ✅ Texto escrito {repeticiones} veces en {loop_duration}s")
            else:
                escribir_char_por_char()
                print(f"  ✅ Texto escrito carácter por carácter")

            return True
        except Exception as e:
            print(f"  ❌ Error al escribir: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Error al pegar texto: {e}")
        return False


def ejecutar_accion_press(key: str) -> bool:
    """
    Ejecuta una acción de presionar tecla
    """
    print(f"⌨️  Acción PRESS: '{key}'")

    try:
        pyautogui.press(key)
        print(f"  ✅ Tecla presionada")
        return True
    except Exception as e:
        print(f"  ❌ Error al presionar tecla: {e}")
        return False


def ejecutar_accion_wait(seconds: float) -> bool:
    """
    Ejecuta una acción de espera
    """
    print(f"⏳ Acción WAIT: {seconds}s")
    time.sleep(seconds)
    print(f"  ✅ Espera completada")
    return True


def ejecutar_plan(plan: List[Dict]) -> bool:
    """
    Ejecuta el plan de acción paso a paso
    Presiona Cmd+C en la terminal para cancelar la ejecución
    """
    print("\n" + "="*60)
    print(f"🚀 Ejecutando plan con {len(plan)} pasos")
    print("⚠️  Presiona Cmd+C en la terminal para cancelar")
    print("="*60 + "\n")

    pasos_exitosos = 0
    pasos_fallidos = 0

    for i, paso in enumerate(plan, 1):
        print(f"\n--- Paso {i}/{len(plan)} ---")

        action = paso.get("action")

        try:
            if action == "click":
                target = paso.get("target")
                if not target:
                    print("  ⚠️  Paso sin target, saltando...")
                    pasos_fallidos += 1
                    continue

                exito = ejecutar_accion_click(target)

            elif action == "type":
                text = paso.get("text")
                if not text:
                    print("  ⚠️  Paso sin text, saltando...")
                    pasos_fallidos += 1
                    continue

                # Extraer parámetros opcionales para loop
                loop = paso.get("loop", False)
                loop_duration = paso.get("loop_duration", 5.0)
                delay_between = paso.get("delay_between", 0.3)

                exito = ejecutar_accion_type(text, loop=loop, loop_duration=loop_duration, delay_between=delay_between)

            elif action == "press":
                key = paso.get("key")
                if not key:
                    print("  ⚠️  Paso sin key, saltando...")
                    pasos_fallidos += 1
                    continue

                exito = ejecutar_accion_press(key)

            elif action == "wait":
                seconds = paso.get("seconds", 1)
                exito = ejecutar_accion_wait(seconds)

            else:
                print(f"  ⚠️  Acción desconocida: {action}")
                pasos_fallidos += 1
                continue

            if exito:
                pasos_exitosos += 1
            else:
                pasos_fallidos += 1
                print(f"  ⚠️  Paso {i} falló, pero continuando...")

            # Pequeña pausa entre pasos
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error en paso {i}: {e}")
            pasos_fallidos += 1

    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE EJECUCIÓN")
    print("="*60)
    print(f"✅ Pasos exitosos: {pasos_exitosos}/{len(plan)}")
    print(f"❌ Pasos fallidos: {pasos_fallidos}/{len(plan)}")

    return pasos_fallidos == 0


def limpiar_thread():
    """
    Elimina el thread del asistente si existe
    """
    global current_thread_id

    if current_thread_id:
        try:
            client.beta.threads.delete(current_thread_id)
            print(f"🗑️  Thread {current_thread_id} eliminado")
            current_thread_id = None
        except Exception as e:
            print(f"⚠️  No se pudo eliminar thread: {e}")


def limpiar_archivos_temporales():
    """
    Elimina todos los archivos temporales creados durante la ejecución
    """
    archivos_temporales = [
        SCREENSHOT_PATH,
        "screen_grid.png",
        "before_final_click.png",
        "after_final_click.png",
    ]

    # Buscar archivos before_click_* y after_click_*
    import glob
    archivos_temporales.extend(glob.glob("before_click_*.png"))
    archivos_temporales.extend(glob.glob("after_click_*.png"))
    archivos_temporales.extend(glob.glob("cursor_iter_*.png"))

    archivos_eliminados = 0
    for archivo in archivos_temporales:
        try:
            if os.path.exists(archivo):
                os.remove(archivo)
                archivos_eliminados += 1
        except Exception as e:
            print(f"⚠️  No se pudo eliminar {archivo}: {e}")

    if archivos_eliminados > 0:
        print(f"🗑️  {archivos_eliminados} archivo(s) temporal(es) eliminado(s)")


def main():
    """
    Función principal del agente visual autónomo
    """
    print("\n" + "="*60)
    print("🤖 AGENTE VISUAL AUTÓNOMO - Multi-Step")
    print(f"   Powered by Assistant {ASSISTANT_ID} + PyAutoGUI")
    print("="*60)

    # Verificar API key
    if not OPENAI_API_KEY:
        print("❌ ERROR: No se encontró OPENAI_API_KEY en las variables de entorno")
        print("💡 Ejecutá: export OPENAI_API_KEY='tu-api-key'")
        return

    print("\n💡 Este agente puede ejecutar tareas completas automáticamente")
    print("   Ejemplos:")
    print("   - 'Enviá un correo a juan@test.com con asunto Hola'")
    print("   - 'Abrí una nueva pestaña y buscá Python en Google'")
    print("   - 'Clickeá en el botón de configuración'")
    print("\n💡 Formas de cancelar:")
    print("   - Presiona Cmd+C en la terminal para detener")
    print("   - Mové el mouse a la esquina superior izquierda (PyAutoGUI failsafe)\n")

    # Input del usuario
    try:
        instruccion = input("🎯 ¿Qué tarea querés que ejecute?: ").strip()

        if not instruccion:
            print("⚠️  No ingresaste ninguna instrucción. Saliendo...")
            return

        print("\n" + "-"*60)

        # Paso 1: Generar plan de acción
        plan = generar_plan_de_accion(instruccion)

        if not plan:
            print("❌ No se pudo generar un plan de acción")
            return

        if not isinstance(plan, list) or len(plan) == 0:
            print("❌ El plan generado está vacío o es inválido")
            return

        # Mostrar plan al usuario
        print("📋 Plan generado:")
        for i, paso in enumerate(plan, 1):
            action = paso.get("action", "?")
            if action == "click":
                print(f"   {i}. Click en: {paso.get('target')}")
            elif action == "type":
                print(f"   {i}. Escribir: {paso.get('text')}")
            elif action == "press":
                print(f"   {i}. Presionar: {paso.get('key')}")
            elif action == "wait":
                print(f"   {i}. Esperar: {paso.get('seconds')}s")

        # Confirmación
        print("\n⏳ Iniciando ejecución en 3 segundos...")
        time.sleep(3)

        # Espera de 5 segundos antes del primer screenshot
        print("\n⏳ Esperando 5 segundos antes de capturar la pantalla...")
        print("   (Prepará la pantalla con la aplicación/sitio correspondiente)")
        time.sleep(5)

        # Paso 2: Ejecutar plan
        exito = ejecutar_plan(plan)

        # Resultado final
        print("\n" + "-"*60)
        if exito:
            print("🎉 Tarea completada exitosamente")
        else:
            print("⚠️  La tarea finalizó con algunos errores")

    except KeyboardInterrupt:
        print("\n\n⏹️  Proceso interrumpido por el usuario")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Limpiar archivos temporales y thread
        time.sleep(0.5)
        limpiar_archivos_temporales()
        limpiar_thread()
        print("\n👋 Agente visual finalizado\n")


if __name__ == "__main__":
    main()
