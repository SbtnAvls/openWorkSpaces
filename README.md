# Windows 11 Workspace Manager

> 🚀 **Abre todas tus aplicaciones de trabajo automáticamente, organizadas y en su lugar correcto, con un solo clic.**

![Windows 11](https://img.shields.io/badge/Windows%2011-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**¿Cansado de abrir y organizar manualmente tus aplicaciones cada vez que empiezas a trabajar?**

Workspace Manager hace esto por ti automáticamente. Define una vez dónde quieres cada aplicación, y luego lánzalo todo con un clic.

---

## 📑 Índice

- [¿Qué hace este programa?](#qué-hace-este-programa)
- [Características Principales](#características-principales)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [🎯 Cómo Usar la Interfaz Gráfica (Tutorial Completo)](#-cómo-usar-la-interfaz-gráfica-gui)
- [Modo Avanzado - Línea de Comandos](#quick-start-modo-avanzado---línea-de-comandos)
- [Preguntas Frecuentes](#-preguntas-frecuentes-faq)
- [Solución de Problemas](#troubleshooting)
- [Para Desarrolladores](#building-and-releasing)

---

## ¿Qué hace este programa?

**Workspace Manager** es una herramienta que te permite **guardar y restaurar automáticamente tu configuración de trabajo** en Windows 11.

### ¿Para qué sirve?

¿Te ha pasado que cada vez que vas a trabajar o estudiar tienes que abrir manualmente varias aplicaciones y organizarlas en la pantalla? Este programa lo hace **automáticamente** por ti:

- **Abre múltiples aplicaciones** al mismo tiempo con un solo clic
- **Las coloca exactamente donde las necesitas** (posición y tamaño de ventanas)
- **Organiza tus aplicaciones en diferentes escritorios virtuales** de Windows 11
- **Guarda diferentes configuraciones** para distintos tipos de trabajo

### Ejemplos de uso:

**Para Programadores:**
- Un clic abre tu editor de código, terminal, navegador y herramientas de desarrollo, cada uno en su lugar correcto

**Para Estudiantes:**
- Un clic abre Word, PowerPoint, navegador con tus pestañas de investigación, y la carpeta de tu proyecto

**Para Diseñadores:**
- Un clic abre Photoshop, Illustrator, carpeta de recursos y navegador con referencias

## Características Principales

- ✅ **Interfaz Gráfica Intuitiva**: Fácil de usar, no requiere conocimientos técnicos
- ✅ **Gestión Visual de Ventanas**: Coloca tus ventanas arrastrando y redimensionando visualmente
- ✅ **Soporte para Escritorios Virtuales**: Organiza aplicaciones en diferentes escritorios de Windows 11
- ✅ **Explorador de Programas Instalados**: Busca y selecciona tus programas fácilmente
- ✅ **Importar/Exportar**: Comparte tus configuraciones entre computadoras
- ✅ **Captura de Configuración**: Guarda tu configuración actual de ventanas

## Requisitos del Sistema

- **Sistema Operativo**: Windows 11 (Windows 10 puede funcionar con limitaciones)
- **Python**: 3.10 o superior (solo si usas el código fuente)
- **Privilegios de Administrador**: No requeridos, pero recomendados para algunas funciones

## Instalación

### Para Usuarios (Recomendado)

Descarga la última versión desde la página de [Releases](https://github.com/yourusername/workspace-manager/releases):

**Opción 1: Instalador de Inno Setup** (⭐ Recomendado)
- Descarga `WorkspaceManager-v1.0.0-Setup.exe`
- Ejecuta el asistente de instalación
- Elige la ubicación de instalación y accesos directos
- Crea accesos directos en el Menú Inicio y en el escritorio
- **¡Listo para usar!** Solo busca "Workspace Manager" en tu menú inicio

**Opción 2: Versión Portátil (Sin instalación)**
- Descarga `WorkspaceManager-v1.0.0.zip`
- Extrae en cualquier carpeta
- Ejecuta `WorkspaceManager.exe`
- No necesita instalación
- Perfecto para usar desde una USB o llevar en tu laptop

### Para Desarrolladores

#### 1. Clone or Download

```bash
git clone https://github.com/yourusername/workspace-manager.git
cd workspace-manager
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Verify Installation

```bash
python main.py --help
```

---

## 🎯 Cómo Usar la Interfaz Gráfica (GUI)

> 💡 **RECOMENDADO PARA TODOS LOS USUARIOS**
>
> Esta es la forma más fácil de usar el programa. No necesitas conocimientos técnicos.
> Si eres usuario avanzado y prefieres la línea de comandos, puedes ver la sección [Modo Avanzado](#quick-start-modo-avanzado---línea-de-comandos) más abajo.

### Abrir el Programa

**Si instalaste con el instalador:**
- Busca "Workspace Manager" en el menú inicio de Windows
- O haz doble clic en el ícono del escritorio

**Si estás usando Python:**
```bash
python main.py
```
O simplemente:
```bash
python main.py gui
```

### 📚 Tutorial Paso a Paso

#### 1. Crear tu Primer Workspace

1. **Abre el programa** - Verás la pantalla principal con el botón **"+ Nuevo Workspace"**

2. **Haz clic en "+ Nuevo Workspace"**

3. **Completa la información básica:**
   - **Nombre**: Dale un nombre descriptivo (ej: "Desarrollo Web", "Estudios", "Diseño")
   - **Descripción**: (Opcional) Describe para qué usarás este workspace

4. **Agrega aplicaciones:**
   - Haz clic en **"+ Agregar Aplicación"**
   - Se abrirá un formulario para configurar la aplicación

#### 2. Configurar una Aplicación

Cuando agregues una aplicación, verás un formulario con estos campos:

##### **ID de la Aplicación**
- Un nombre único para identificar la app en este workspace
- Ejemplo: `chrome-principal`, `vscode-proyecto`, `word-tesis`

##### **Ejecutable**
Tienes dos opciones para seleccionar el programa:

- **Opción 1 - "Programas Instalados"** (⭐ Recomendado):
  - Haz clic en el botón verde **"Programas Instalados"**
  - Aparecerá una ventana con todos tus programas
  - Usa el cuadro de búsqueda para encontrar el programa
  - Haz clic en el programa que deseas
  - Clic en **"Seleccionar"**

- **Opción 2 - "Buscar Archivo..."**:
  - Navega manualmente hasta el archivo `.exe` del programa
  - Útil si el programa no aparece en la lista

##### **Carpeta de trabajo / Proyecto** (Opcional)
- Si quieres que el programa se abra en una carpeta específica
- Ejemplo: la carpeta de tu proyecto de programación
- Haz clic en **"Buscar..."** para seleccionar la carpeta

##### **Argumentos adicionales** (Opcional)
- Parámetros especiales para el programa
- Ejemplos:
  - Para abrir un archivo específico: `C:\Documentos\proyecto.txt`
  - Para Chrome con una URL: `https://google.com`
  - Para Visual Studio Code: `--new-window`

##### **Escritorio Virtual**
- En qué escritorio virtual de Windows 11 quieres que aparezca
- **0** = Primer escritorio (escritorio principal)
- **1** = Segundo escritorio
- **2** = Tercer escritorio, etc.

##### **Configuración de Ventana**

La parte más importante: **dónde y qué tamaño tendrá tu ventana**

**Método Visual (más fácil):**
1. Verás un rectángulo azul en una representación de tu pantalla
2. **Arrastra el rectángulo** para moverlo donde quieras que aparezca la ventana
3. **Arrastra las esquinas o bordes** del rectángulo para cambiar el tamaño
4. Los valores X, Y, Ancho y Alto se actualizarán automáticamente

**Método Manual:**
- O puedes escribir directamente los valores:
  - **X**: Posición horizontal (píxeles desde la izquierda)
  - **Y**: Posición vertical (píxeles desde arriba)
  - **Ancho**: Ancho de la ventana en píxeles
  - **Alto**: Alto de la ventana en píxeles

**💡 Tip:** Si agregas múltiples aplicaciones al mismo escritorio virtual, verás las otras ventanas como guías grises para ayudarte a posicionarlas sin que se superpongan.

5. **Guarda la aplicación** haciendo clic en **"Guardar"**

#### 3. Agregar Más Aplicaciones

Repite el paso anterior para cada aplicación que quieras en tu workspace. Puedes agregar tantas como necesites.

#### 4. Guardar el Workspace

Cuando hayas agregado todas tus aplicaciones, haz clic en **"Guardar Workspace"**.

¡Listo! Tu workspace ha sido creado.

#### 5. Lanzar un Workspace

En la pantalla principal verás todos tus workspaces guardados. Para lanzar uno:

1. **Encuentra tu workspace** en la lista
2. **Haz clic en el botón "Lanzar"** (botón azul)
3. El programa te preguntará si estás seguro
4. Confirma y ¡todas tus aplicaciones se abrirán automáticamente!

### 🔧 Otras Funciones de la Interfaz

#### Ver Detalles de un Workspace
- Haz clic en el **nombre del workspace** o en la **flecha (▶)** para expandir y ver todas las aplicaciones configuradas

#### Editar un Workspace
- Haz clic en el botón **"Editar"** del workspace que quieres modificar
- Puedes cambiar el nombre, descripción, agregar/eliminar aplicaciones, etc.

#### Eliminar un Workspace
- Haz clic en el botón **rojo con el ícono de papelera (🗑)**
- Confirma que deseas eliminarlo
- ⚠️ **Esta acción no se puede deshacer**

#### Actualizar la Lista
- Haz clic en **"⟳ Actualizar"** para recargar la lista de workspaces

### 💡 Consejos Prácticos

1. **Empieza Simple**: Crea un workspace con solo 2-3 aplicaciones para familiarizarte con el programa

2. **Nombres Descriptivos**: Usa nombres claros como "Trabajo Oficina", "Edición Video", "Estudio Python"

3. **Organiza por Actividad**: Crea un workspace diferente para cada tipo de actividad que realices

4. **Usa Escritorios Virtuales**: Si tienes muchas aplicaciones, distribúyelas en diferentes escritorios virtuales para mantener el orden

5. **Prueba Primero**: Después de crear un workspace, pruébalo inmediatamente para verificar que todo funciona como esperas

---

## Quick Start (Modo Avanzado - Línea de Comandos)

### Launch a Minimal Test Workspace

1. (Optional) Copy the example configuration to your Documents folder:
```bash
copy workspaces.example.json "%USERPROFILE%\Documents\WorkspaceManager\workspaces.json"
```

2. Launch the minimal test workspace:
```bash
python main.py launch minimal
```

This will open a simple Notepad window to verify everything is working.

**Note:** The configuration file will be created automatically in `Documents\WorkspaceManager\` when you create your first workspace using the GUI or CLI commands.

### Capture Your Current Setup

1. Arrange your windows as desired across virtual desktops
2. Run the capture command:
```bash
python main.py capture my_workspace
```
3. Follow the interactive prompts to select windows and configure the workspace

### Launch Your Workspace

```bash
python main.py launch my_workspace
```

## Usage

### Commands

#### `launch` - Launch a workspace
```bash
python main.py launch <workspace_name> [options]

Options:
  -d, --dry-run      Simulate launch without starting applications
  -s, --sequential   Launch apps one by one instead of in parallel
  -r, --retry-failed Retry failed applications
```

#### `capture` - Capture current window state
```bash
python main.py capture [workspace_name] [options]

Options:
  -i, --interactive  Interactive mode (default)
  -a, --all         Include all windows without prompting
  -o, --overwrite   Overwrite existing workspace
```

#### `list` - List all workspaces
```bash
python main.py list [options]

Options:
  -d, --detailed  Show detailed information
```

#### `show` - Show workspace details
```bash
python main.py show <workspace_name> [options]

Options:
  -j, --json  Output in JSON format
```

#### `remove` - Remove a workspace
```bash
python main.py remove <workspace_name> [options]

Options:
  -y, --yes  Skip confirmation
```

#### `export` - Export workspace to file
```bash
python main.py export <workspace_name> -o <output_file>
```

#### `import` - Import workspace from file
```bash
python main.py import <file> [options]

Options:
  -o, --overwrite  Overwrite existing workspace
```

#### `validate` - Validate workspace configuration
```bash
python main.py validate [workspace_name]
```

### Configuration File Format

The configuration is stored in `workspaces.json`, which is automatically saved in your Documents folder at:
`C:\Users\<YourUsername>\Documents\WorkspaceManager\workspaces.json`

The file will be created automatically when you create your first workspace.

```json
{
  "workspaces": [
    {
      "name": "development",
      "description": "My development environment",
      "apps": [
        {
          "id": "vscode",
          "exe": "C:\\Program Files\\VS Code\\Code.exe",
          "args": ["C:\\projects\\my-project"],
          "working_dir": "C:\\projects\\my-project",
          "virtual_desktop": 0,
          "window": {
            "x": 0,
            "y": 0,
            "width": 1920,
            "height": 1080
          }
        }
      ]
    }
  ]
}
```

### Field Descriptions

- **name**: Unique workspace identifier
- **description**: Optional description
- **apps**: List of applications to launch
  - **id**: Unique identifier within the workspace
  - **exe**: Path to executable (can be in PATH)
  - **args**: Command-line arguments (optional)
  - **working_dir**: Working directory (optional)
  - **virtual_desktop**: Target desktop index (0-based)
  - **window**: Window position and size
    - **x, y**: Top-left corner position
    - **width, height**: Window dimensions

## Examples

### Development Workspace

Create a development workspace with VS Code, terminals, and browser:

```json
{
  "name": "fullstack",
  "description": "Full stack development setup",
  "apps": [
    {
      "id": "editor",
      "exe": "code",
      "args": ["."],
      "working_dir": "C:\\projects\\myapp",
      "virtual_desktop": 0,
      "window": {"x": 0, "y": 0, "width": 1920, "height": 1080}
    },
    {
      "id": "backend_terminal",
      "exe": "wt.exe",
      "args": ["-d", "C:\\projects\\myapp\\backend"],
      "virtual_desktop": 1,
      "window": {"x": 0, "y": 0, "width": 960, "height": 1080}
    },
    {
      "id": "browser",
      "exe": "chrome.exe",
      "args": ["--new-window", "http://localhost:3000"],
      "virtual_desktop": 1,
      "window": {"x": 960, "y": 0, "width": 960, "height": 1080}
    }
  ]
}
```

### Productivity Workspace

Office applications setup:

```json
{
  "name": "office",
  "description": "Office productivity suite",
  "apps": [
    {
      "id": "outlook",
      "exe": "outlook.exe",
      "virtual_desktop": 0,
      "window": {"x": 0, "y": 0, "width": 960, "height": 1080}
    },
    {
      "id": "teams",
      "exe": "Teams.exe",
      "virtual_desktop": 0,
      "window": {"x": 960, "y": 0, "width": 960, "height": 1080}
    }
  ]
}
```

## Tips & Best Practices

### 1. Start Simple
Begin with a minimal workspace and gradually add complexity:
```bash
python main.py capture test_workspace
# Select just 2-3 windows
python main.py launch test_workspace
```

### 2. Use Capture for Complex Setups
Instead of manually writing JSON, arrange your windows and capture:
```bash
python main.py capture --interactive
```

### 3. Validate Before Launch
Always validate after manual edits:
```bash
python main.py validate my_workspace
```

### 4. Use Dry Run for Testing
Test without actually launching:
```bash
python main.py launch my_workspace --dry-run
```

### 5. Handle Path Variables
Use environment variables in paths by editing after capture:
- Replace `C:\\Users\\John` with `%USERPROFILE%`
- Replace absolute paths with relative ones where appropriate

## Known Limitations

### Virtual Desktop Limitations
- **Windows 11 API Restrictions**: Some virtual desktop operations may require additional permissions
- **Desktop Creation**: Creating desktops programmatically uses keyboard shortcuts (Win+Ctrl+D)
- **Window Movement**: Some applications resist being moved between desktops
- **UWP Apps**: Windows Store apps may not respond to window positioning

### Application Limitations
- **Startup Time**: Some applications take longer to create windows
- **Multiple Windows**: Apps that create multiple windows may not position correctly
- **Minimized Start**: Some apps start minimized and ignore positioning
- **Admin Apps**: Applications running as administrator may not be controllable

### Capture Limitations
- **Arguments**: Cannot always determine original command-line arguments
- **Working Directory**: May not detect the original working directory
- **Hidden Windows**: System and background windows are filtered out

## Troubleshooting

### Issue: "pyvda not available" Warning
**Solution**: Install pyvda:
```bash
pip install pyvda
```

### Issue: Windows Don't Move to Correct Desktop
**Causes**:
1. Application doesn't support virtual desktop moves
2. Not enough virtual desktops exist

**Solutions**:
- Ensure virtual desktops are created first
- Try running with administrator privileges
- Some apps work better with sequential launch mode:
```bash
python main.py launch workspace_name --sequential
```

### Issue: Window Positions Are Incorrect
**Causes**:
1. Multiple monitors with different resolutions
2. DPI scaling issues
3. Application overrides positioning

**Solutions**:
- Capture workspace with windows already positioned
- Adjust coordinates manually in JSON
- Use primary monitor for critical windows

### Issue: Applications Don't Launch
**Causes**:
1. Incorrect executable path
2. Missing dependencies
3. Permission issues

**Solutions**:
- Use full paths to executables
- Verify paths with: `where <program>`
- Check working directory exists
- Run as administrator if needed

### Issue: Capture Doesn't Find All Windows
**Causes**:
1. Windows are minimized
2. Windows are on other virtual desktops
3. System windows are filtered

**Solutions**:
- Restore all windows before capture
- Switch through all virtual desktops
- Use `--all` flag to include more windows

## Advanced Usage

### Programmatic Usage

```python
from workspace_manager.config import ConfigManager
from workspace_manager.launcher import WorkspaceLauncher

# Load and launch a workspace
config = ConfigManager()
workspace = config.get_workspace("development")

launcher = WorkspaceLauncher()
launcher.launch_workspace(workspace)
```

### Custom Window Filters

Edit `capture.py` to modify window filtering:

```python
def _filter_system_windows(self, windows):
    # Add your custom filtering logic
    custom_filter = ["myapp.exe", "special.exe"]
    return [w for w in windows if w.exe_path in custom_filter]
```

## Building and Releasing

### For Developers

To build standalone executables and installers:

```bash
# Build everything (EXE, ZIP, Inno Setup installer)
python release.py

# Or just EXE and ZIP (faster)
python build.py
```

**Output files** (in `dist/`):
- `WorkspaceManager.exe` - Standalone executable (~40 MB)
- `WorkspaceManager-v1.0.0.zip` - Portable package
- `installer/WorkspaceManager-v1.0.0-Setup.exe` - Inno Setup installer (if Inno Setup is installed)

**Documentation**:
- See `QUICK_START_RELEASE.md` for quick guide
- See `RELEASE.md` for detailed release process
- See `BUILD.md` for build customization options

### Creating a New Release

1. Update version in `workspace_manager/__version__.py`
2. Run `python release.py`
3. Test the generated installers
4. Create git tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. Upload to GitHub Releases

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ❓ Preguntas Frecuentes (FAQ)

### ¿Dónde se guardan mis workspaces?
Los workspaces se guardan en: `C:\Users\<TuUsuario>\Documents\WorkspaceManager\workspaces.json`

### ¿Puedo usar este programa en Windows 10?
El programa está diseñado para Windows 11. Puede funcionar en Windows 10 pero con limitaciones, especialmente en las funciones de escritorios virtuales.

### ¿Las aplicaciones se abrirán en el mismo estado en que las dejé?
El programa abre las aplicaciones y las posiciona, pero no guarda el estado interno de cada aplicación (archivos abiertos, pestañas del navegador, etc.). Para eso, puedes usar los "argumentos adicionales" para abrir archivos específicos.

### ¿Qué pasa si una aplicación no se abre correctamente?
Algunas aplicaciones pueden:
- Tardar más en abrir su ventana
- No respetar la posición establecida (especialmente apps de Windows Store)
- Requerir permisos de administrador

Si tienes problemas, revisa la sección de "Troubleshooting" más abajo.

### ¿Puedo compartir mis workspaces con otros?
Sí, puedes copiar el archivo `workspaces.json` a otra computadora, o usar las funciones de exportar/importar desde la línea de comandos.

### ¿Necesito conocimientos de programación para usar este programa?
No, la interfaz gráfica está diseñada para ser usada por cualquier persona. No necesitas conocimientos técnicos.

### ¿Cuántas aplicaciones puedo agregar a un workspace?
No hay límite, pero se recomienda un número razonable (5-10 aplicaciones) para evitar sobrecargar el sistema.

---

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Check the FAQ section
3. Review existing issues on GitHub
4. Create a new issue with details about your environment and problem

## Changelog

### Version 1.0.0
- Initial release
- Full workspace management capabilities
- Virtual desktop support
- Interactive capture mode
- Import/export functionality

---

**Note**: This tool is designed for Windows 11. Windows 10 users may experience limited functionality, especially regarding virtual desktop features.