# Quick Start Guide - Building and Releasing

## Para Actualizar y Crear un Nuevo Release

### 1️⃣ Actualizar Versión

Edita **solo este archivo**: `workspace_manager/__version__.py`

```python
__version__ = "1.1.0"  # ← Cambia esto
```

### 2️⃣ Generar TODOS los Instaladores

Un solo comando genera todo:

```bash
python release.py
```

Esto crea automáticamente:
- ✅ `WorkspaceManager.exe` - Ejecutable standalone
- ✅ `WorkspaceManager-v1.1.0.zip` - Paquete portable
- ✅ `WorkspaceManager-v1.1.0-Setup.exe` - Instalador Inno Setup (si está instalado)

**Nota sobre MSI**: cx_Freeze no soporta MSI en Python 3.13 todavía. Usa Inno Setup en su lugar (es mejor).

### 3️⃣ Probar

```bash
# Probar el ejecutable
dist/WorkspaceManager.exe --help

# Probar MSI (instala en máquina de prueba)
# msiexec /i dist/WorkspaceManager-v1.1.0.msi
```

### 4️⃣ Git Tag

```bash
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### 5️⃣ Subir a GitHub Releases

1. Ve a GitHub → Releases → "New release"
2. Sube los archivos de `dist/`:
   - `*.zip`
   - `*.msi`
   - `*-Setup.exe` (si existe)

---

## Comandos Alternativos

### Solo EXE + ZIP (más rápido)

```bash
python build.py
```

### Solo MSI

```bash
python setup_msi.py bdist_msi
```

---

## Archivos Generados

```
dist/
├── WorkspaceManager.exe                    # Ejecutable standalone (~40MB)
├── WorkspaceManager-v1.0.0.zip            # Portable package (~40MB)
├── installer/
│   └── WorkspaceManager-v1.0.0-Setup.exe  # Inno installer (~40MB, si Inno Setup está instalado)
└── RELEASE_SUMMARY.md                      # Documentación de release
```

**Nota**: MSI no está disponible en Python 3.13. Usa Inno Setup para instalador profesional.

---

## Requisitos

### Python Packages (ya instalados)
```bash
pip install -r requirements.txt
```

### Inno Setup (opcional, para Setup.exe)
Descarga de: https://jrsoftware.org/isdl.php

Si no lo tienes, `release.py` simplemente lo omitirá (generará los demás).

---

## Troubleshooting

**❌ Error: "The process cannot access the file because it is being used"**

Esto ocurre cuando tienes archivos de build anteriores abiertos. **Solución**:

```bash
# Opción 1: Usar el script automático
clean_and_release.bat

# Opción 2: Limpiar manualmente
1. Cierra TODAS las ventanas del Explorador de Windows
2. Cierra cualquier WorkspaceManager.exe que esté corriendo
3. Ejecuta: clean_build.bat
4. Luego ejecuta: python release.py
```

**❌ Error al construir MSI**
```bash
pip install --upgrade cx-Freeze
```

**❌ "Inno Setup not found"**
- Es opcional, el resto se generará de todas formas
- O instala desde: https://jrsoftware.org/isdl.php

**❌ Ejecutable muy grande**
- Es normal (~35MB incluye Python runtime + GUI + dependencias)
- Para reducir: edita `workspace_manager.spec` y excluye módulos

---

## ¿Qué hace cada script?

| Script | Qué genera | Tiempo |
|--------|------------|--------|
| `build.py` | EXE + ZIP | ~30-60s |
| `setup_msi.py` | MSI | ~60-90s |
| `release.py` | **TODO** (EXE + ZIP + MSI + Setup) | ~2-3min |

---

**Recomendación**: Usa `python release.py` para releases oficiales. Es automático y genera todo lo necesario.

Para versión de desarrollo rápido, usa `python build.py`.
