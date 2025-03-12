# Script Launcher

Este es un ejemplo de proyecto similar a los que puedo desarrollar en mi puesto de trabajo. No es igual a ningún proyecto real, pero puede servir como punto de partida para entender el desarrollo de aplicaciones similares.

## Descripción General

Script Launcher es una aplicación de escritorio desarrollada en Python usando Tkinter para una interfaz gráfica que facilita la ejecución de scripts de procesamiento de datos. La aplicación está diseñada con una interfaz moderna y proporciona una forma sencilla y visual de acceder a diferentes scripts de procesamiento de datos organizados por categorías.

## Características Principales

- **Organización por categorías** de scripts (Aftermarket y Tarifas)
- **Acceso directo a la documentación** de cada script
- **Ejecución simplificada** de scripts mediante botones intuitivos
- **Diseño responsive** que se adapta al tamaño de la ventana

## Estructura del Proyecto

```
Script-Launcher/
├── documentation/                # Documentación de los scripts
├── images/                       # Imágenes utilizadas por cualquier aplicación o script que lo requiera
├── Scripts-formateo-datos/       # Scripts de procesamiento de datos
│   ├── Scripts-AFT/              # Categoría para Aftermarket
│   └── Scripts-tarifas/          # Categoría para Tarifas
├── Scripts-generales/            # Scripts de uso general (aquí se planea añadir scripts reutilizables en el futuro)
├── Tariffs_Report/               # Directorio que contiene una app web en Flask para servir informe actualizado de tarifas
├── script_launcher.py            # Código fuente principal
├── script_launcher.exe           # Ejecutable compilado de la aplicación
└── update_all_scripts.py         # Script para actualizar todos los scripts de Aftermarket y Tarifas de una sola vez
```

## Categorías de Scripts

### Scripts de Aftermarket

- **Dividir ficheros** - Permite dividir archivos CSV grandes en archivos más pequeños
- **Unir ficheros** - Permite unir múltiples archivos CSV en uno solo

### Scripts de Tarifas

- **Mercedes** - Procesamiento específico para datos de Mercedes
- **Turquía** - Procesamiento específico para datos de Turquía
- **PSA** - Procesamiento específico para datos de PSA
- **Informe Tarifas** - Generación de informes de tarifas (genera un Excel con los datos relevantes por país y marca)
- **Generar Enviados Traducciones** - Generación de archivos XLSX para traducciones
- **Generar XML Traducciones** - Generación de archivos XML para traducciones
- **Generar CSV Accounting** - Conversión de datos a formato CSV desde distintos XLSX para contabilidad

## Requisitos

- Python 3.6 o superior
- Bibliotecas de Python:
  - tkinter
  - os, subprocess, shutil (bibliotecas estándar)

## Instalación

### Opción 1: Ejecutar desde el código fuente

1. Tener Python instalado en el sistema
2. Clonar este repositorio
3. Ejecutar `script_launcher.py`

```bash
python script_launcher.py
```

### Opción 2: Usar el ejecutable compilado

Simplemente ejecutar `script_launcher.exe` que se encuentra en la carpeta raíz del proyecto.

## Uso

1. Al iniciar la aplicación, se mostrará un menú principal con dos opciones: "Scripts de Aftermarket" y "Scripts de Tarifas"
2. Seleccionar la categoría deseada para ver los scripts disponibles
3. Para cada script, tiene las siguientes opciones:
   - **Descargar Documentación**: Descarga el archivo de documentación correspondiente a la carpeta de Descargas del usuario
   - **Ejecutar**: Inicia la ejecución del script seleccionado
4. Utilizar el botón "Volver" para regresar al menú principal

## Documentación

Cada script cuenta con su propia documentación detallada que explica:
- El propósito del script
- Los formatos de entrada requeridos
- Las rutas donde deben estar los archivos a procesar
- Las rutas donde se generarán los archivos procesados
- Instrucciones específicas de uso

Para acceder a la documentación, utilizar el botón "Descargar Documentación" disponible para cada script en la interfaz.

## Desarrollo

### Estructura del Código

- `DarkModeStyle`: Clase que define los estilos visuales de la aplicación
- `ScriptLauncherApp`: Clase principal que implementa la interfaz gráfica y la lógica de la aplicación
  - `show_main_menu()`: Muestra el menú principal
  - `show_aftermarket_scripts()`: Muestra los scripts de Aftermarket
  - `show_tarifas_scripts()`: Muestra los scripts de Tarifas
  - `show_scripts_menu()`: Función genérica para mostrar scripts en una cuadrícula
  - `download_documentation()`: Descarga la documentación seleccionada
  - `run_script()`: Ejecuta el script seleccionado


## Mantenimiento y actualizaciones

El script `update_all_scripts.py` puede utilizarse para actualizar todos los scripts del proyecto.

## Licencia

Este proyecto es una aplicación de prueba que emula una pequeña parte de un proyecto que he realizado en mi puesto de trabajo.
No es un proyecto oficial ni está asociado a ninguna empresa.
No se permite su distribución ni su uso comercial.