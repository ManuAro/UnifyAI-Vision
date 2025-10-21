# 🤖 Agente Visual Autónomo - Multi-Step

Un agente visual autónomo que entiende tareas en lenguaje natural, genera un plan de acción automáticamente y lo ejecuta paso a paso interactuando con tu pantalla.

## Características

**Planificación Automática:**
- GPT-4o-mini genera un plan de pasos completo a partir de tu instrucción
- Entiende tareas complejas como "enviar un correo", "buscar en Google", etc.
- No necesitas especificar cada paso, el agente lo deduce

**Ejecución Multi-Step:**
- Captura de pantalla por cada acción de click
- Análisis visual con GPT-4o-mini Vision API
- Acciones soportadas: `click`, `type` (con soporte de loop), `press`, `wait`
- Sistema de grilla para mayor precisión en la detección
- Manejo de errores con continuación del flujo

**Interfaz:**
- Logs con emojis para seguimiento visual del proceso
- Resumen de ejecución al finalizar
- Tecla ESC para cancelar en cualquier momento
- Limpieza automática de archivos temporales

## Requisitos

### Paquetes Requeridos
Los siguientes paquetes ya están instalados:
- `openai`
- `pyautogui`
- `pillow`
- `mss`
- `pyperclip` (para escribir caracteres especiales)

### Paquetes Opcionales
- `keyboard` - Permite cancelar con ESC durante la ejecución
  ```bash
  pip3 install keyboard
  ```
  **Nota**: Si no está instalado, el agente funcionará igualmente, pero solo podrás cancelar con Ctrl+C o el failsafe de PyAutoGUI

## Configuración

1. **⚠️ IMPORTANTE**: Configurar la API key de OpenAI como variable de entorno:

```bash
export OPENAI_API_KEY='tu-api-key-aqui'
```

**Nunca hardcodees tu API key en el código**. El código ahora solo acepta la API key desde variables de entorno por seguridad.

2. En macOS, otorgar permisos de accesibilidad:
   - Ir a **Preferencias del Sistema** → **Seguridad y Privacidad** → **Privacidad**
   - Seleccionar **Accesibilidad** en la lista izquierda
   - Agregar Terminal (o tu aplicación de terminal) a la lista de aplicaciones permitidas

## Uso

```bash
python main.py
```

El programa te pedirá que describas la tarea completa que quieres realizar:

```
🎯 ¿Qué tarea querés que ejecute?: Enviá un correo a juan@test.com con asunto "Reunión" y mensaje "Nos vemos mañana"
```

## Flujo del Programa

1. **🧠 Planificación** - GPT-4o-mini genera un plan de pasos en JSON
2. **📋 Revisión** - Muestra el plan generado para tu revisión
3. **🚀 Ejecución** - Ejecuta cada paso del plan:
   - Para `click`: Captura pantalla → Vision API → Click
   - Para `type`: Escribe el texto
   - Para `press`: Presiona la tecla
   - Para `wait`: Espera N segundos
4. **📊 Resumen** - Muestra estadísticas de ejecución
5. **🗑️ Limpieza** - Elimina archivos temporales

## Ejemplos de Tareas

**Correos:**
- `Enviá un correo a juan@test.com con asunto "Hola"`
- `Redactá un correo nuevo para maria@empresa.com`

**Navegación:**
- `Abrí una nueva pestaña y buscá Python en Google`
- `Clickeá en el botón de configuración`

**Tareas Simples:**
- `Hacé click en el botón Play`
- `Escribí "Hola mundo" en el campo de búsqueda`

**Tareas Complejas:**
El agente entiende secuencias completas y genera los pasos automáticamente. Por ejemplo, para "enviar un correo" entiende que debe:
1. Click en botón Redactar
2. Click en campo destinatario
3. Escribir email
4. Navegar al asunto
5. Escribir asunto
6. Etc.

## Controles

- **ESC**: Cancela la ejecución del plan en cualquier momento (requiere paquete `keyboard` instalado)
- **Ctrl+C**: Interrumpe el programa completamente
- **Mouse a esquina superior izquierda**: Failsafe de PyAutoGUI (cancela inmediatamente)

## Arquitectura

### Planificación (Planning Agent)
GPT-4o-mini recibe tu instrucción y genera un plan estructurado usando **patrones de flujo comunes**.

El agente conoce los flujos típicos de:
- **Enviar email**: Redactar → Destinatario → Asunto → Cuerpo → Enviar
- **Búsqueda web**: Click en barra → Escribir → Enter/Buscar
- **Formularios**: Rellenar campos → Submit

**Input:** "Enviá un correo a juan@test.com con asunto Hola"

**Output (JSON generado):**
```json
[
  {"action": "click", "target": "botón para redactar email"},
  {"action": "wait", "seconds": 1},
  {"action": "click", "target": "campo de texto para destinatario"},
  {"action": "type", "text": "juan@test.com"},
  {"action": "press", "key": "tab"},
  {"action": "type", "text": "Hola"},
  {"action": "click", "target": "área de cuerpo del mensaje"},
  {"action": "type", "text": "Contenido ", "loop": true, "loop_duration": 3},
  {"action": "click", "target": "botón de envío"}
]
```

**Nota**: El modelo NO usa nombres exactos de botones (evita hardcodear "Redactar", "Compose", etc.), sino descripciones visuales genéricas que funcionan en múltiples interfaces.

### Acción Type con Loop

La acción `type` ahora soporta escribir repetidamente:

```json
{
  "action": "type",
  "text": "Texto a repetir ",
  "loop": true,
  "loop_duration": 5,
  "delay_between": 0.3
}
```

**Parámetros:**
- `text`: Texto a escribir
- `loop`: `true` para activar modo repetición (opcional, default: `false`)
- `loop_duration`: Duración en segundos (opcional, default: 5)
- `delay_between`: Delay entre repeticiones en segundos (opcional, default: 0.3)

**Ejemplo de uso**: Llenar un campo de texto con mucho contenido repetidamente.

### Ejecución (Execution Loop)
Cada paso del plan se ejecuta secuencialmente:
- **Click**: Screenshot → GPT-4o-mini Vision → Coordenadas → PyAutoGUI click
- **Type**: PyAutoGUI escribe el texto caracter por caracter
- **Press**: PyAutoGUI presiona la tecla especificada
- **Wait**: Sleep por N segundos

## Ventajas de Este Enfoque

- **Sin Fine-Tuning**: Todo funciona con prompting inteligente
- **Contexto Nativo**: GPT-4o ya sabe cómo funcionan apps comunes
- **Flexible**: Funciona con cualquier aplicación (Gmail, Slack, navegadores, etc.)
- **Auto-Correctivo**: Continúa ejecutando aunque falle un paso
- **Transparente**: Ves el plan antes de que se ejecute

## Notas Técnicas

- El archivo `screen.png` se crea/elimina por cada acción de click
- `pyautogui.FAILSAFE = True`: Mover mouse a esquina cancela
- `pyautogui.PAUSE = 0.5s`: Pausa de seguridad entre acciones
- Hay pausa de 0.5s entre cada paso del plan
- El agente continúa ejecutando aunque falle algún paso

## Solución de Problemas

### "No se encontró OPENAI_API_KEY"
```bash
export OPENAI_API_KEY='sk-...'
```

### "Permission denied" en macOS
Otorgar permisos de accesibilidad a Terminal en Preferencias del Sistema.

### El plan se genera mal
- **Problema**: El modelo hardcodea nombres exactos ("botón Redactar") que no existen
  - **Solución**: El nuevo sistema usa patrones de flujo. Si sigue pasando, revisá PROMPT_ENGINEERING.md
- **Problema**: Pasos fuera de orden o faltan pasos
  - **Solución**: Sé más explícito en tu instrucción. En vez de "enviá un email", decí "redactá y enviá un email a X con asunto Y"
- **Problema**: El modelo genera JSON inválido
  - **Solución**: Esto es raro con el prompt actual. Revisá los logs y reportá el caso

### Pasos fallan
- Asegurate de que la app esté visible en pantalla
- Algunos elementos tardan en cargar, agregá `wait` en tu instrucción
- Revisa los logs para ver qué coordenadas detectó

## Limitaciones Actuales

- Solo funciona con elementos visibles en pantalla
- No maneja múltiples monitores (usa el principal)
- El planning depende de la calidad del prompt de GPT-4o-mini

## Mejoras Implementadas

✅ **Eliminado numpy** - Ya no es necesario, reduciendo dependencias
✅ **Seguridad de API key** - Solo acepta keys desde variables de entorno
✅ **Type con loop** - Capacidad de escribir repetidamente con control de duración
✅ **Código limpio** - Funciones de búsqueda refactorizadas, eliminando duplicación
✅ **Mejor limpieza** - Todos los archivos temporales se eliminan correctamente
✅ **Sin numpy en verificación** - Usa solo PIL para comparar capturas
✅ **Cancelación con ESC** - Opción de cancelar la ejecución presionando ESC (opcional, requiere `keyboard`)
✅ **Input siempre requerido** - El usuario siempre debe especificar la tarea a ejecutar
