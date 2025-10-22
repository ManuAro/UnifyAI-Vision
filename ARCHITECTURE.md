# 🏗️ Arquitectura de UnifyVision

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                           main.py                                │
│                    (Punto de Entrada)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         src/config.py                            │
│                  (Configuración Centralizada)                    │
│  • OPENAI_API_KEY                                               │
│  • GRID_COLS / GRID_ROWS                                        │
│  • Timeouts, delays, etc.                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Capa de Planificación                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐         ┌─────────────────┐              │
│  │  src/planner.py  │────────▶│ OpenAI Client   │              │
│  │  • Planner       │         │ (Chat API)      │              │
│  │  • ActionPlan    │         └─────────────────┘              │
│  └──────────────────┘                                           │
│         │                                                        │
│         │ Genera                                                │
│         ▼                                                        │
│  ┌──────────────────────────────────────┐                      │
│  │ Plan JSON Validado                   │                      │
│  │ [                                    │                      │
│  │   {"action": "click", "target": ...} │                      │
│  │   {"action": "type", "text": ...}    │                      │
│  │ ]                                    │                      │
│  └──────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Plan
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Capa de Ejecución                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐                                           │
│  │ src/executor.py  │                                           │
│  │  • PlanExecutor  │                                           │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           │ Para cada paso                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │ src/actions.py   │                                           │
│  │ • ActionExecutor │                                           │
│  │   ├─ execute_click()                                        │
│  │   ├─ execute_type()                                         │
│  │   ├─ execute_press()                                        │
│  │   └─ execute_wait()                                         │
│  └────────┬─────────┘                                           │
└───────────┼─────────────────────────────────────────────────────┘
            │
            │ Para acciones click
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Capa de Visión (Click)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐                                         │
│  │ screen_capture.py  │                                         │
│  │ • ScreenCapture    │                                         │
│  │   ├─ capture_screen()                                       │
│  │   ├─ get_display_scale()                                    │
│  │   └─ encode_to_base64()                                     │
│  └────────┬───────────┘                                         │
│           │                                                      │
│           │ Imagen                                              │
│           ▼                                                      │
│  ┌────────────────────┐                                         │
│  │ grid_system.py     │                                         │
│  │ • GridSystem       │                                         │
│  │   ├─ draw_grid()                                            │
│  │   ├─ parse_response()                                       │
│  │   └─ calculate_coords()                                     │
│  └────────┬───────────┘                                         │
│           │                                                      │
│           │ Imagen con Grilla                                   │
│           ▼                                                      │
│  ┌────────────────────┐                                         │
│  │ openai_client.py   │                                         │
│  │ • OpenAIClient     │                                         │
│  │   └─ ask_with_image()                                       │
│  │       (Responses API)                                        │
│  └────────┬───────────┘                                         │
│           │                                                      │
│           │ Respuesta JSON                                      │
│           ▼                                                      │
│  {"found": true, "cells": [...], ...}                          │
│           │                                                      │
│           │ Coordenadas (x, y)                                  │
│           ▼                                                      │
│  ┌────────────────────┐                                         │
│  │    PyAutoGUI       │                                         │
│  │    • click()       │                                         │
│  │    • moveTo()      │                                         │
│  └────────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Capa de Infraestructura                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  logger.py       │    │  exceptions.py   │                  │
│  │  • setup_logger()│    │  • Custom        │                  │
│  │  • log_*()       │    │    Exceptions    │                  │
│  └──────────────────┘    └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Ejecución

### 1. Inicio de Aplicación

```
Usuario ejecuta: python3 main.py
         │
         ▼
  Validar config.OPENAI_API_KEY
         │
         ▼
  Mostrar banner e instrucciones
         │
         ▼
  Solicitar instrucción del usuario
```

### 2. Generación de Plan

```
Instrucción: "Send email to john@test.com"
         │
         ▼
  Planner.generate_plan()
         │
         ├─▶ OpenAIClient.generate_plan()
         │        │
         │        └─▶ Chat Completions API
         │                  │
         │                  ▼
         │           Prompt con patrones
         │                  │
         │                  ▼
         │        Respuesta JSON con pasos
         │
         ▼
  ActionPlan (validado)
  [
    {"action": "click", "target": "compose button"},
    {"action": "wait", "seconds": 1},
    {"action": "type", "text": "john@test.com"},
    ...
  ]
```

### 3. Ejecución de Plan

```
Para cada paso en el plan:
         │
         ▼
  ¿Qué acción?
         │
    ┌────┴────┬────────┬─────────┐
    │         │        │         │
    ▼         ▼        ▼         ▼
  CLICK     TYPE     PRESS     WAIT
    │         │        │         │
    │         │        │         │
    ▼         │        │         │
(Ver flujo)  │        │         │
             ▼        ▼         ▼
        PyAutoGUI  PyAutoGUI  time.sleep()
         .write()   .press()
```

### 4. Flujo de CLICK (Detallado)

```
execute_click(target="compose button")
         │
         ▼
  ScreenCapture.capture_screen()
         │
         ▼
  GridSystem.draw_grid_on_image()
         │
         ├─▶ Verificar cache
         │   (evitar redibujar)
         │
         ▼
  Imagen con grilla numerada (0-575)
         │
         ▼
  Crear prompt de visión:
  "Find 'compose button' in grid cells..."
         │
         ▼
  OpenAIClient.ask_with_image()
         │
         └─▶ Responses API (GPT-4o Vision)
                  │
                  ▼
           Analiza imagen con grilla
                  │
                  ▼
           Retorna JSON:
           {
             "found": true,
             "cells": [
               {"cell_number": 42, "coverage_percent": 80},
               {"cell_number": 43, "coverage_percent": 20}
             ],
             "confidence": "high"
           }
         │
         ▼
  GridSystem.calculate_coordinates_from_cells()
         │
         ├─▶ Centroide ponderado por cobertura
         │
         ▼
  Coordenadas (x_img, y_img)
         │
         ▼
  ScreenCapture.get_display_scale()
         │
         ├─▶ Para pantallas Retina
         │
         ▼
  Coordenadas lógicas (x_log, y_log)
         │
         ▼
  _execute_multi_click_pattern()
         │
         ├─▶ Captura pantalla ANTES
         ├─▶ Click en centro
         ├─▶ Captura pantalla DESPUÉS
         ├─▶ Detectar cambios
         │   │
         │   └─▶ ¿Cambió?
         │          │
         │       ┌──┴──┐
         │       │     │
         │       Sí    No
         │       │     │
         │       ✓     └─▶ Probar siguiente posición
         │               (arriba/abajo/izq/der)
         ▼
  Retorna True/False
```

## 🧩 Responsabilidades de Módulos

### Core

**config.py**
- ✅ Almacenar todas las constantes
- ✅ Validar variables de entorno
- ✅ Proveer configuración única

**exceptions.py**
- ✅ Definir jerarquía de errores
- ✅ Mensajes descriptivos
- ✅ Facilitar debugging

**logger.py**
- ✅ Logging estructurado
- ✅ Niveles de log
- ✅ Emojis para UX

### Vision & Screen

**screen_capture.py**
- ✅ Capturar pantalla
- ✅ Manejar escalado Retina
- ✅ Codificar para API
- ✅ Detectar cambios

**grid_system.py**
- ✅ Dibujar grilla numerada
- ✅ Cachear grillas
- ✅ Calcular coordenadas
- ✅ Parsear respuestas

### AI Integration

**openai_client.py**
- ✅ Wrapper de OpenAI API
- ✅ Responses API (visión)
- ✅ Chat Completions (planning)
- ✅ Manejo de errores

### Planning

**planner.py**
- ✅ Generar planes
- ✅ Validar estructura
- ✅ Parsear JSON
- ✅ Logging de planes

### Execution

**actions.py**
- ✅ Ejecutar acciones individuales
- ✅ Multi-click pattern
- ✅ Typing con clipboard
- ✅ Verificar efectos

**executor.py**
- ✅ Ejecutar planes completos
- ✅ Manejo de errores por paso
- ✅ Estadísticas
- ✅ Cleanup

## 🔐 Principios de Diseño

### 1. Separación de Concerns
Cada módulo tiene una responsabilidad única y bien definida.

### 2. Dependency Injection
Los módulos reciben sus dependencias, facilitando testing y flexibilidad.

```python
# Ejemplo: ActionExecutor recibe dependencias
executor = ActionExecutor(
    screen_capture=my_capture,
    grid_system=my_grid,
    openai_client=my_client
)
```

### 3. Fail Fast
Validaciones tempranas para detectar errores rápidamente.

```python
# Config.validate() al inicio
# ActionPlan valida en constructor
```

### 4. Single Responsibility
Una función, un propósito.

```python
# ❌ Malo
def capture_and_analyze():
    # Hace dos cosas

# ✅ Bueno
def capture_screen():
    # Solo captura

def analyze_image():
    # Solo analiza
```

### 5. Open/Closed
Abierto para extensión, cerrado para modificación.

```python
# Agregar nueva acción sin modificar código existente
# Solo agregar método en ActionExecutor
```

## 📊 Métricas de Código

### Complejidad por Módulo

| Módulo | Líneas | Complejidad | Responsabilidad |
|--------|--------|-------------|-----------------|
| config.py | 73 | Baja | Configuración |
| exceptions.py | 65 | Baja | Excepciones |
| logger.py | 135 | Media | Logging |
| screen_capture.py | 170 | Media | Captura |
| grid_system.py | 263 | Alta | Grilla |
| openai_client.py | 164 | Media | API |
| planner.py | 164 | Media | Planificación |
| actions.py | 330 | Alta | Ejecución |
| executor.py | 150 | Media | Orquestación |
| main.py | 120 | Baja | Entry point |

### Acoplamiento

```
main.py
  ├─ config (bajo)
  ├─ logger (bajo)
  ├─ Planner (medio)
  └─ PlanExecutor (medio)

Planner
  └─ OpenAIClient (bajo)

PlanExecutor
  └─ ActionExecutor (medio)

ActionExecutor
  ├─ ScreenCapture (medio)
  ├─ GridSystem (medio)
  └─ OpenAIClient (medio)
```

### Cohesión

- **Alta cohesión** en todos los módulos
- Funciones relacionadas agrupadas
- Responsabilidades claras

## 🚀 Extensibilidad

### Agregar Nueva Funcionalidad

1. **Nueva acción**: Modificar `planner.py`, `actions.py`, `executor.py`
2. **Nuevo modelo AI**: Modificar `openai_client.py`, `config.py`
3. **Nueva validación**: Modificar `planner.py`
4. **Nuevo tipo de captura**: Extender `screen_capture.py`

### Puntos de Extensión

- ✅ Acciones personalizadas
- ✅ Validadores de plan
- ✅ Estrategias de click
- ✅ Backends de logging
- ✅ Proveedores de AI

## 🧪 Testabilidad

Todos los módulos son fácilmente testables gracias a:

1. **Dependency Injection**
2. **Interfaces claras**
3. **Sin estado global** (excepto config)
4. **Excepciones específicas**

```python
# Ejemplo: Mockeando OpenAI en tests
class MockOpenAIClient:
    def ask_with_image(self, prompt, image):
        return '{"found": true, "cells": [...]}'

# Inyectar en tests
executor = ActionExecutor(
    openai_client=MockOpenAIClient()
)
```

## 📈 Escalabilidad

La arquitectura permite:

- ✅ Procesamiento paralelo (futuro)
- ✅ Múltiples backends de AI
- ✅ Caching a diferentes niveles
- ✅ Distribución de carga
- ✅ Plugins y extensiones

---

Esta arquitectura proporciona una base sólida, mantenible y extensible para UnifyVision.
