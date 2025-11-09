# Guía de Instalación y Uso de Inno Setup

Inno Setup es una herramienta gratuita para crear instaladores profesionales de Windows. Es superior a MSI en muchos aspectos y funciona perfectamente con Python 3.13.

## ¿Por Qué Inno Setup?

✅ **Ventajas sobre MSI**:
- Wizard de instalación más profesional y personalizable
- Soporte multiidioma incluido (inglés, español, y más)
- Opciones de instalación más flexibles
- Atajos de escritorio opcionales
- Actualización automática integrada
- Completamente gratis y de código abierto
- Instaladores más pequeños y rápidos

## Instalación de Inno Setup

### Paso 1: Descargar

1. Ve a: **https://jrsoftware.org/isdl.php**
2. Descarga la última versión estable (actualmente Inno Setup 6.x)
3. El archivo será algo como: `innosetup-6.x.x.exe`

### Paso 2: Instalar

1. Ejecuta el instalador descargado
2. Acepta la licencia (es gratis)
3. Instala en la ubicación por defecto: `C:\Program Files (x86)\Inno Setup 6\`
4. Marca la opción "Install Inno Setup Preprocessor" (recomendado)
5. Completa la instalación

### Paso 3: Verificar Instalación

```bash
# Debería existir este archivo
ls "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

## Compilar el Instalador

### Opción 1: Usando release.py (Automático) ⭐

```bash
python release.py
```

Este script:
1. Construye el EXE con PyInstaller
2. Crea el ZIP portable
3. Detecta automáticamente Inno Setup
4. Compila el instalador si Inno Setup está instalado
5. Genera: `dist/installer/WorkspaceManager-v1.0.0-Setup.exe`

### Opción 2: Manual con GUI de Inno Setup

1. Abre Inno Setup (menú Start)
2. File → Open → Selecciona `installer.iss`
3. Build → Compile
4. El instalador se generará en `dist/installer/`

### Opción 3: Manual con Línea de Comandos

```bash
# Windows
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# Si está en PATH
ISCC installer.iss
```

## Personalizar el Instalador

El archivo `installer.iss` contiene toda la configuración. Puedes personalizar:

### Información de la Aplicación

```ini
#define MyAppName "Windows 11 Workspace Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tu Nombre"
#define MyAppURL "https://github.com/tu-usuario/workspace-manager"
```

### Iconos

```ini
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
```

### Idiomas

```ini
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
; Agregar más idiomas según necesites
```

### Tareas Opcionales

```ini
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}";
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}";
```

### Archivos a Incluir

```ini
[Files]
Source: "dist\WorkspaceManager.exe"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"
Source: "LICENSE"; DestDir: "{app}"
; Agregar más archivos según necesites
```

## Resultado Final

Al compilar, obtendrás:

```
dist/installer/WorkspaceManager-v1.0.0-Setup.exe (~40 MB)
```

Este instalador:
- ✅ Muestra wizard profesional de instalación
- ✅ Permite elegir carpeta de instalación
- ✅ Crea atajos en Start Menu
- ✅ Opcionalmente crea icono de escritorio
- ✅ Registra en Programas instalados de Windows
- ✅ Permite desinstalar fácilmente
- ✅ Soporta actualización automática

## Proceso de Actualización

Cuando generes una nueva versión:

1. **Actualiza la versión** en `workspace_manager/__version__.py`:
   ```python
   __version__ = "1.1.0"
   ```

2. **Actualiza el instalador** (opcional, se toma automáticamente):
   ```ini
   #define MyAppVersion "1.1.0"  ; en installer.iss
   ```

3. **Ejecuta el release**:
   ```bash
   python release.py
   ```

4. **El instalador detectará versiones anteriores** y ofrecerá actualizar

## Troubleshooting

### Error: "ISCC.exe not found"

**Causa**: Inno Setup no está instalado o no está en la ruta esperada.

**Solución**:
1. Instala Inno Setup desde https://jrsoftware.org/isdl.php
2. Asegúrate de instalarlo en la ubicación por defecto
3. Reinicia la terminal/IDE

### Error: "Cannot find source file"

**Causa**: El ejecutable no existe en la ruta especificada.

**Solución**:
1. Ejecuta primero `python build.py` para generar el EXE
2. Verifica que `dist/WorkspaceManager.exe` existe
3. Luego compila el instalador

### El instalador es muy grande

**Normal**:
- El instalador incluye Python runtime + todas las dependencias
- Tamaño típico: ~35-45 MB
- Es comparable a otros instaladores de aplicaciones Python

**Para reducir** (si realmente necesitas):
- Edita `workspace_manager.spec` y excluye módulos no utilizados
- Usa compresión más agresiva en `installer.iss`:
  ```ini
  Compression=lzma2/ultra64
  ```

### El antivirus bloquea el instalador

**Causa**: Instaladores nuevos sin firma digital pueden ser marcados como sospechosos.

**Solución**:
1. **Para uso personal**: Agregar excepción en el antivirus
2. **Para distribución pública**: Firma el instalador digitalmente
   - Obtén certificado de firma de código
   - Usa `SignTool.exe` de Windows SDK

## Firma Digital (Opcional, para Distribución)

Para evitar advertencias de seguridad:

1. **Obtén un certificado**:
   - Compra certificado de firma de código (~$100-300/año)
   - O usa certificados de prueba para desarrollo

2. **Configura en installer.iss**:
   ```ini
   SignTool=signtool sign /f "path\to\certificate.pfx" /p password /t http://timestamp.server.com $f
   ```

3. **Recompila el instalador**

## Recursos Adicionales

- **Documentación oficial**: https://jrsoftware.org/ishelp/
- **Ejemplos**: `C:\Program Files (x86)\Inno Setup 6\Examples\`
- **Comunidad**: https://stackoverflow.com/questions/tagged/inno-setup
- **Wizard de Scripts**: Inno Setup → Tools → Script Wizard

## Comparación con Otros Métodos

| Método | Tamaño | Instalación | Actualización | Desinstalación |
|--------|--------|-------------|---------------|----------------|
| **Inno Setup** | ~40 MB | Wizard profesional | Automática | Panel de Control |
| ZIP Portable | ~40 MB | Manual | Manual | Borrar carpeta |
| EXE Standalone | ~40 MB | Ninguna | Manual | Borrar archivo |
| MSI | N/A | Windows Installer | Automática | Panel de Control |

**Recomendación**: Usa **Inno Setup** para distribución profesional y **ZIP** para portabilidad.

---

**¿Necesitas ayuda?** Revisa los ejemplos incluidos con Inno Setup o consulta la documentación oficial.
