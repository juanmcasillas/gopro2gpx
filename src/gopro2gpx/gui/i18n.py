import locale
import os

_TEXTS = {
    "en": {
        "title": "GoPro2gpx - Graphical User Interface",
        "descriptor_tab": "Descriptor",
        "main_tab": "Main",
        "paths": "Paths",
        "video_dir": "Video Directory:",
        "output_dir": "Output Directory:",
        "browse": "Browse",
        "options": "Options",
        "verbose": "Verbose Mode (show detailed log)",
        "binary": "Read data from binary file",
        "skip": "Skip erroneous points (GPSFIX==0)",
        "skip_dop": "Skip points with high precision (GPSP > limit)",
        "dop_limit": "GPSP Limit:",
        "output_format": "Output Format",
        "select_format": "Select output format:",
        "camera": "Camera Type",
        "select_camera": "Select camera type:",
        "camera_old": "GoPRO Hero 10 or earlier",
        "camera_new": "GoPRO Hero 11 or 13",
        "process": "Process",
        "progress": "Progress",
        "verbose_output": "Verbose Output",
        "error": "Error",
        "missing_video": "Please select the video directory.",
        "missing_output": "Please select the output directory.",
        "no_videos": "No video files were found in the selected directory.",
        "completed_title": "Process Completed",
        "completed_msg": "File processing has successfully finished.",
        "select_video": "Select Video Directory",
        "select_output": "Select Output Directory",
        "about_html": """
<h3>Application Overview</h3>
<p>
This application extracts GPS data from videos recorded with GoPro cameras and
creates GPX, CSV, or KML files.
</p>
<h3>About GoPro2gpx</h3>
<ul>
  <li>Main code developed by <a href='https://github.com/juanmcasillas'>juanmcasillas</a> and contributors.</li>
  <li>Original Windows GUI created by <a href='https://github.com/germancruzram'>germancruzram</a>.</li>
</ul>
<p><b>Version 1.0 - 2025</b></p>
""",
    },
    "es": {
        "title": "GoPro2gpx - Interfaz grafica",
        "descriptor_tab": "Descriptor",
        "main_tab": "Principal",
        "paths": "Rutas",
        "video_dir": "Directorio de videos:",
        "output_dir": "Directorio de salida:",
        "browse": "Seleccionar",
        "options": "Opciones",
        "verbose": "Modo Verbose (incrementa detalles en la consola)",
        "binary": "Leer datos desde fichero binario",
        "skip": "Omitir puntos erroneos (GPSFIX==0)",
        "skip_dop": "Omitir puntos con alta precision (GPSP > limite)",
        "dop_limit": "Limite de GPSP:",
        "output_format": "Formato de salida",
        "select_format": "Selecciona el formato a crear:",
        "camera": "Tipo de camara",
        "select_camera": "Selecciona el tipo de camara:",
        "camera_old": "GoPRO Hero 10 o anterior",
        "camera_new": "GoPRO Hero 11 o 13",
        "process": "Procesar",
        "progress": "Progreso",
        "verbose_output": "Salida Verbose",
        "error": "Error",
        "missing_video": "Debes seleccionar el directorio de videos.",
        "missing_output": "Debes seleccionar el directorio de salida.",
        "no_videos": "No se han encontrado archivos de video en el directorio seleccionado.",
        "completed_title": "Proceso completado",
        "completed_msg": "El procesamiento de archivos ha finalizado exitosamente.",
        "select_video": "Seleccionar directorio de videos",
        "select_output": "Seleccionar directorio de salida",
        "about_html": """
<h3>Resena de la aplicacion</h3>
<p>
Esta aplicacion extrae datos GPS de videos grabados con camaras GoPro y genera
archivos GPX, CSV o KML.
</p>
<h3>Sobre GoPro2gpx</h3>
<ul>
  <li>Codigo principal desarrollado por <a href='https://github.com/juanmcasillas'>juanmcasillas</a> y colaboradores.</li>
  <li>Interfaz original para Windows creada por <a href='https://github.com/germancruzram'>germancruzram</a>.</li>
</ul>
<p><b>Version 1.0 - 2025</b></p>
""",
    },
}


def load_texts(language: str | None = None) -> dict[str, str]:
    """Return UI strings for explicit language code or current system locale."""
    if language:
        key = language.lower()[:2]
    else:
        system_locale = locale.getlocale()[0] or os.environ.get("LANG", "")
        key = (system_locale or "en")[:2].lower()
    return _TEXTS.get(key, _TEXTS["en"])
