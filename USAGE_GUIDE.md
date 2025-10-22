# 📘 Guía de Uso - UnifyVision Refactorizado

## 🚀 Inicio Rápido

### 1. Verificar Instalación

```bash
# Asegurarse de que todas las dependencias están instaladas
pip3 install -r requirements.txt

# Verificar que el código funciona
python3 verify_refactoring.py
```

### 2. Configurar API Key

```bash
# Configurar la API key de OpenAI
export OPENAI_API_KEY='tu-api-key-aqui'

# Para hacerlo permanente, agregar a ~/.zshrc o ~/.bashrc:
echo "export OPENAI_API_KEY='tu-api-key-aqui'" >> ~/.zshrc
source ~/.zshrc
```

### 3. Ejecutar la Aplicación

```bash
python3 main.py
```

## 💡 Ejemplos de Uso

### Ejemplo 1: Tarea Simple

```bash
$ python3 main.py

🎯 What task do you want to execute?: Click the settings button

# El agente generará un plan como:
# 1. Click on: settings button
# 2. Wait: 1s
```

### Ejemplo 2: Tarea Compleja

```bash
$ python3 main.py

🎯 What task do you want to execute?: Send an email to john@test.com with subject "Meeting"

# El agente generará un plan completo automáticamente
```

## 🛠️ Uso Programático

### Importar Módulos

```python
from src import (
    config,
    logger,
    Planner,
    ActionExecutor,
    PlanExecutor,
    ActionPlan
)
```

### Crear un Plan Manualmente

```python
from src import ActionPlan

# Definir pasos del plan
steps = [
    {"action": "click", "target": "search button"},
    {"action": "wait", "seconds": 1},
    {"action": "type", "text": "Python"},
    {"action": "press", "key": "enter"}
]

# Crear y validar el plan
plan = ActionPlan(steps)
print(f"Plan tiene {len(plan)} pasos")
```

### Ejecutar un Plan

```python
from src import PlanExecutor, ActionPlan

# Crear el plan
steps = [
    {"action": "wait", "seconds": 2},
    {"action": "click", "target": "button"}
]
plan = ActionPlan(steps)

# Ejecutar
executor = PlanExecutor()
success = executor.execute_plan(plan)

if success:
    print("¡Plan ejecutado exitosamente!")
```

### Generar un Plan Automáticamente

```python
from src import Planner

# Crear el planificador
planner = Planner()

# Generar plan desde instrucción en lenguaje natural
plan = planner.generate_plan("Search for Python on Google")

# El plan se genera y valida automáticamente
for i, step in enumerate(plan, 1):
    print(f"{i}. {step['action']}: {step.get('target', step.get('text', ''))}")
```

### Capturar Pantalla

```python
from src import ScreenCapture

# Crear instancia
capture = ScreenCapture()

# Capturar pantalla
screenshot_path = capture.capture_screen()
print(f"Captura guardada en: {screenshot_path}")

# Obtener escala de display
scale_x, scale_y = capture.get_display_scale()
print(f"Escala: {scale_x}x, {scale_y}x")
```

### Sistema de Grilla

```python
from src import GridSystem

# Crear instancia
grid = GridSystem()

# Dibujar grilla en imagen
grid_path, cell_w, cell_h = grid.draw_grid_on_image("screenshot.png")
print(f"Grilla guardada en: {grid_path}")
print(f"Tamaño de celda: {cell_w}x{cell_h}")
```

### Configuración Personalizada

```python
from src.config import Config

# Modificar configuración (antes de usarla)
Config.GRID_COLS = 40  # Más columnas para mayor precisión
Config.GRID_ROWS = 24
Config.PAUSE_BETWEEN_ACTIONS = 0.3  # Más rápido

# Validar configuración
try:
    Config.validate()
    print("Configuración válida")
except ValueError as e:
    print(f"Error de configuración: {e}")
```

### Logging Personalizado

```python
from src.logger import setup_logger, log_click, log_success
import logging

# Configurar logger con nivel DEBUG
logger = setup_logger(
    name="MiApp",
    level=logging.DEBUG,
    log_file="unifyvision.log"  # Opcional: guardar en archivo
)

# Usar funciones helper
log_click("Haciendo click en botón")
log_success("Operación completada")

# O usar directamente
logger.info("Mensaje informativo")
logger.error("Error encontrado")
```

### Manejo de Errores

```python
from src import (
    Planner,
    PlanExecutor,
    InvalidPlanError,
    ActionExecutionError,
    ElementNotFoundError
)

try:
    # Generar plan
    planner = Planner()
    plan = planner.generate_plan("Mi tarea")

    # Ejecutar
    executor = PlanExecutor()
    executor.execute_plan(plan)

except InvalidPlanError as e:
    print(f"Plan inválido: {e}")

except ElementNotFoundError as e:
    print(f"Elemento no encontrado: {e.element_description}")

except ActionExecutionError as e:
    print(f"Error ejecutando acción: {e}")
```

## 🎨 Personalización

### Agregar Nueva Acción

1. **Agregar validación en `planner.py`**:
```python
# En ActionPlan.VALID_ACTIONS
VALID_ACTIONS = {"click", "type", "press", "wait", "scroll"}  # Nueva acción

# En ActionPlan._validate()
if action == "scroll" and not step.get("direction"):
    raise InvalidPlanError(
        f"Step {i+1}: 'scroll' action requires 'direction'"
    )
```

2. **Implementar acción en `actions.py`**:
```python
def execute_scroll(self, direction: str, amount: int = 100) -> bool:
    """
    Ejecuta una acción de scroll

    Args:
        direction: "up" o "down"
        amount: Cantidad a scrollear

    Returns:
        True si fue exitoso
    """
    try:
        if direction == "up":
            pyautogui.scroll(amount)
        else:
            pyautogui.scroll(-amount)
        log_success(f"Scroll {direction} completado")
        return True
    except Exception as e:
        raise ActionExecutionError(f"Scroll execution failed: {e}")
```

3. **Agregar al executor en `executor.py`**:
```python
elif action == "scroll":
    direction = step.get("direction", "down")
    amount = step.get("amount", 100)
    return self.action_executor.execute_scroll(direction, amount)
```

### Cambiar Modelo de OpenAI

```python
from src.config import Config

# Cambiar a GPT-4
Config.MODEL = "gpt-4"

# O pasar directamente al generar plan
from src import OpenAIClient

client = OpenAIClient()
response = client.generate_plan(
    "Mi tarea",
    model="gpt-4",
    temperature=0.1
)
```

## 🔧 Debugging

### Activar Logging Detallado

```python
from src.logger import setup_logger
import logging

# Nivel DEBUG para ver todo
logger = setup_logger(level=logging.DEBUG)

# Ahora verás todos los detalles de ejecución
```

### Guardar Logs en Archivo

```python
from src.logger import setup_logger

logger = setup_logger(
    log_file="debug.log"
)

# Los logs se guardan en debug.log
```

### Inspeccionar Plan Generado

```python
from src import Planner
import json

planner = Planner()
plan = planner.generate_plan("Mi tarea")

# Ver el plan en formato legible
for i, step in enumerate(plan, 1):
    print(f"Paso {i}: {json.dumps(step, indent=2)}")
```

## 📊 Mejores Prácticas

### 1. Siempre Validar Configuración

```python
from src.config import config

# Al inicio de tu script
try:
    config.validate()
except ValueError as e:
    print(f"Configuración inválida: {e}")
    exit(1)
```

### 2. Usar Context Managers para Cleanup

```python
from src import PlanExecutor

executor = PlanExecutor()
try:
    success = executor.execute_plan(plan)
finally:
    # Siempre limpiar archivos temporales
    PlanExecutor.cleanup_temporary_files()
```

### 3. Manejar Interrupciones de Usuario

```python
try:
    executor.execute_plan(plan)
except KeyboardInterrupt:
    print("\n⏹️  Ejecución cancelada por el usuario")
    PlanExecutor.cleanup_temporary_files()
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python3 -m unittest discover tests -v

# Test específico
python3 -m unittest tests.test_config -v
python3 -m unittest tests.test_planner -v
```

### Crear Nuevos Tests

```python
# tests/test_mi_modulo.py
import unittest
from src import MiClase

class TestMiClase(unittest.TestCase):

    def test_funcionalidad(self):
        """Test que la funcionalidad funciona"""
        obj = MiClase()
        result = obj.mi_metodo()
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
```

## 💻 Desarrollo

### Estructura Recomendada de Nuevo Código

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descripción del módulo
"""

from typing import Optional, List
from src import logger
from src.exceptions import UnifyVisionError

class MiClase:
    """Descripción de la clase"""

    def __init__(self, param: str):
        """
        Inicializa la clase

        Args:
            param: Descripción del parámetro
        """
        self.param = param
        logger.info(f"MiClase inicializada con: {param}")

    def mi_metodo(self, arg: int) -> bool:
        """
        Descripción del método

        Args:
            arg: Descripción del argumento

        Returns:
            True si fue exitoso

        Raises:
            UnifyVisionError: Si algo falla
        """
        try:
            # Implementación
            logger.debug(f"Ejecutando mi_metodo con arg={arg}")
            result = True
            return result
        except Exception as e:
            raise UnifyVisionError(f"Error en mi_metodo: {e}")
```

## 📚 Recursos Adicionales

- **README.md**: Documentación general del proyecto
- **REFACTORING_SUMMARY.md**: Detalles de la refactorización
- **src/**: Código fuente de todos los módulos
- **tests/**: Tests unitarios

## ❓ Preguntas Frecuentes

**P: ¿Cómo cambio el tamaño de la grilla?**
R: Modifica `Config.GRID_COLS` y `Config.GRID_ROWS` en `src/config.py`

**P: ¿Cómo agrego soporte para un nuevo tipo de acción?**
R: Sigue los pasos en la sección "Agregar Nueva Acción"

**P: ¿Los archivos temporales se eliminan automáticamente?**
R: Sí, se limpian automáticamente al finalizar la ejecución

**P: ¿Puedo usar esto en otro proyecto?**
R: Sí, solo importa los módulos necesarios desde `src`

---

Para más información, consulta el [README.md](README.md) o el código fuente en [src/](src/).
