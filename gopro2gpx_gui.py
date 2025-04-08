
# German Ahmed Cruz Ramírez <germancruzram@gmail.com>
# https://github.com/germancruzram  /  https://www.linkedin.com/in/german-cruz-ram-in24/

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import argparse
import sys
import time
import csv
import re
import subprocess
import tempfile
import webbrowser
import configparser

# Función para obtener la ruta absoluta a un recurso, considerando el modo frozen (onefile)
def resource_path(relative_path):
    """
    Devuelve la ruta absoluta al recurso dado 'relative_path', utilizando sys._MEIPASS en modo frozen.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Importar la función main_core desde el módulo correspondiente
try:
    from gopro2gpx.gopro2gpx import main_core
except ImportError:
    try:
        import gopro2gpx.gopro2gpx
        main_core = gopro2gpx.gopro2gpx.main_core
    except ImportError:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from gopro2gpx.gopro2gpx import main_core

class GoPro2GPXGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Extractor GPS de video GoPro")
        # Establecer tamaño inicial según la pestaña activa (Descriptor será más pequeño)
        self.geometry("800x400")
        
        # Configuración persistente: Leer configuración de config.ini.
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.config_parser = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config_parser.read(self.config_path)
        else:
            self.config_parser['Paths'] = {}
        
        # Si no hay último directorio guardado, se inicializa en "C:\\"
        self.last_video_dir = self.config_parser['Paths'].get('last_video_dir', "C:\\")
        self.last_output_dir = self.config_parser['Paths'].get('last_output_dir', "C:\\")
        
        # Variables para almacenar rutas y opciones
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Opciones por defecto: Modo Verbose y Omitir puntos erróneos activados.
        self.verbose_var = tk.IntVar(value=1)
        self.skip_var = tk.BooleanVar(value=True)
        self.binary_var = tk.BooleanVar(value=False)
        self.skip_dop_var = tk.BooleanVar(value=False)
        self.dop_limit_var = tk.IntVar(value=2000)
        
        # Variables para la barra de progreso
        self.total_files = 0
        self.processed_files = 0

        # Configurar el widget Notebook con las pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Crear pestaña Descriptor y Principal; Descriptor aparece primero según requerimiento
        self.descriptor_frame = ttk.Frame(self.notebook)
        self.principal_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.descriptor_frame, text="Descriptor")
        self.notebook.add(self.principal_frame, text="Principal")
        
        # Enlazar el evento de cambio de pestaña para ajustar la geometría
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # Crear widgets para las pestañas
        self.create_descriptor_widgets()
        self.create_principal_widgets()

        # Al iniciar la aplicación, seleccionar la pestaña Descriptor
        self.notebook.select(self.descriptor_frame)

    def on_tab_change(self, event):
        # Detectar la pestaña actual y ajustar la geometría
        selected = self.notebook.select()
        if selected == str(self.descriptor_frame):
            # Tamaño menor para Descriptor
            self.geometry("650x300")
        elif selected == str(self.principal_frame):
            # Tamaño para la pestaña Principal
            self.geometry("700x550")

    def create_principal_widgets(self):
        # --- Principal Tab: Rutas ---
        routes_frame = tk.LabelFrame(self.principal_frame, text="Rutas")
        routes_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(routes_frame, text="Directorio de videos:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(routes_frame, textvariable=self.input_dir, width=50).grid(row=0, column=1, padx=5, pady=2)
        tk.Button(routes_frame, text="Seleccionar", command=self.select_input_dir).grid(row=0, column=2, padx=5, pady=2)
        tk.Label(routes_frame, text="Directorio de salida:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(routes_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, padx=5, pady=2)
        tk.Button(routes_frame, text="Seleccionar", command=self.select_output_dir).grid(row=1, column=2, padx=5, pady=2)

        # --- Principal Tab: Opciones adicionales ---
        options_frame = tk.LabelFrame(self.principal_frame, text="Opciones")
        options_frame.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(options_frame, text="Modo Verbose (incrementa detalles en la consola)", variable=self.verbose_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Leer datos desde fichero binario", variable=self.binary_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Omitir puntos erróneos (GPSFIX==0)", variable=self.skip_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Omitir puntos con alta precisión (GPSP > límite)", variable=self.skip_dop_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Label(options_frame, text="Límite de GPSP:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(options_frame, textvariable=self.dop_limit_var, width=10).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        # --- Principal Tab: Opciones de salida y cámara ---
        output_type_frame = tk.LabelFrame(self.principal_frame, text="Formato de salida")
        output_type_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(output_type_frame, text="Selecciona el formato a crear:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.out_format_var = tk.StringVar()
        self.out_format_combobox = ttk.Combobox(output_type_frame, textvariable=self.out_format_var, state="readonly", width=10)
        self.out_format_combobox['values'] = ("GPX", "CSV", "KML")
        self.out_format_combobox.current(0)
        self.out_format_combobox.grid(row=0, column=1, padx=5, pady=2)

        camera_frame = tk.LabelFrame(self.principal_frame, text="Tipo de cámara")
        camera_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(camera_frame, text="Selecciona el tipo de cámara:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.camera_var = tk.StringVar()
        self.camera_combobox = ttk.Combobox(camera_frame, textvariable=self.camera_var, state="readonly", width=25)
        self.camera_combobox['values'] = ("GoPRO Hero 10 o anterior", "GoPRO Hero 11 o 13")
        self.camera_combobox.current(0)
        self.camera_combobox.grid(row=0, column=1, padx=5, pady=2)

        # Botón para iniciar el procesamiento
        tk.Button(self.principal_frame, text="Procesar", command=self.on_process).pack(pady=10)

        # Barra de progreso en lugar del área de Log/Salida
        progress_frame = tk.LabelFrame(self.principal_frame, text="Progreso")
        progress_frame.pack(fill="x", padx=10, pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill="x", padx=5, pady=5)

    def create_descriptor_widgets(self):
        # Se usa un widget Text para mejorar el formato (tamaño de fuente mayor, negritas y enlaces)
        self.text_descriptor = tk.Text(self.descriptor_frame, wrap="word", padx=10, pady=10, relief="flat")
        self.text_descriptor.pack(fill="both", expand=True)
        # Configuración de la fuente
        default_font = ("Helvetica", 12)
        bold_font = ("Helvetica", 12, "bold")
        self.text_descriptor.configure(font=default_font)
        
        # Configurar etiquetas para negrita y enlaces
        self.text_descriptor.tag_configure("bold", font=bold_font)
        self.text_descriptor.tag_configure("hyperlink", foreground="blue", underline=1)
        
        # Función para manejar clic en enlace
        def click_link(url):
            webbrowser.open_new(url)
        
        # Insertar contenido enriquecido en la pestaña Descriptor
        self.text_descriptor.insert("end", "Reseña de la aplicación:\n", "bold")
        self.text_descriptor.insert("end", "\nEsta aplicación extrae datos GPS de videos grabados con cámaras GoPro y genera archivos en formatos GPX, CSV o KML. El procesamiento se realiza en segundo plano y cuenta con una interfaz intuitiva que muestra el progreso del procesamiento.\n\n")
        
        self.text_descriptor.insert("end", "Agradecimientos:\n", "bold")
        self.text_descriptor.insert("end", "\n• Código principal desarrollado por ")
        # Insertar hipervínculo para el primer repositorio
        self.text_descriptor.insert("end", "https://github.com/juanmcasillas", "hyperlink")
        self.text_descriptor.tag_bind("hyperlink", "<Button-1>", lambda e, url='https://github.com/juanmcasillas': click_link(url))
        self.text_descriptor.insert("end", " y colaboradores.\n")
        self.text_descriptor.insert("end", "• Interfaz para Windows creada por German Cruz R ")
        self.text_descriptor.insert("end", "https://github.com/germancruzram", "hyperlink_secondary")
        self.text_descriptor.tag_configure("hyperlink_secondary", foreground="blue", underline=1)
        self.text_descriptor.tag_bind("hyperlink_secondary", "<Button-1>", lambda e, url='https://github.com/germancruzram': click_link(url))
        self.text_descriptor.insert("end", ".\n\n")
        
        self.text_descriptor.insert("end", "version 1.0 - 2025", "bold")
        # Hacer el widget de solo lectura
        self.text_descriptor.configure(state="disabled")

    def select_input_dir(self):
        # Si ya se ha seleccionado una carpeta anteriormente, se usará esa como directorio inicial.
        # De lo contrario, se inicia en el último directorio guardado en la configuración,
        # cuyo valor por defecto es "C:\".
        initial_dir = self.input_dir.get() if self.input_dir.get() else self.last_video_dir
        directory = filedialog.askdirectory(title="Seleccionar directorio de videos", initialdir=initial_dir)
        if directory:
            self.input_dir.set(directory)
            self.last_video_dir = directory
            self.config_parser['Paths']['last_video_dir'] = directory
            with open(self.config_path, 'w') as configfile:
                self.config_parser.write(configfile)

    def select_output_dir(self):
        # Si ya se ha seleccionado una carpeta anteriormente para salida, se usará esa como directorio inicial.
        # De lo contrario, se inicia en el último directorio guardado en la configuración,
        # cuyo valor por defecto es "C:\".
        initial_dir = self.output_dir.get() if self.output_dir.get() else self.last_output_dir
        directory = filedialog.askdirectory(title="Seleccionar directorio de salida", initialdir=initial_dir)
        if directory:
            self.output_dir.set(directory)
            self.last_output_dir = directory
            self.config_parser['Paths']['last_output_dir'] = directory
            with open(self.config_path, 'w') as configfile:
                self.config_parser.write(configfile)

    def on_process(self):
        # Validar rutas
        if not self.input_dir.get():
            messagebox.showerror("Error", "Debes seleccionar el directorio de videos.")
            return
        if not self.output_dir.get():
            messagebox.showerror("Error", "Debes seleccionar el directorio de salida.")
            return

        # Buscar archivos de video en el directorio de entrada.
        video_files = []
        for file in os.listdir(self.input_dir.get()):
            if file.lower().endswith((".mp4", ".mov", ".avi")):
                video_files.append(os.path.join(self.input_dir.get(), file))
        if not video_files:
            messagebox.showerror("Error", "No se han encontrado archivos de video en el directorio seleccionado.")
            return

        # Configurar progreso según el número de archivos encontrados
        self.total_files = len(video_files)
        self.processed_files = 0
        self.progress.config(maximum=self.total_files, value=0)

        # Obtener formato de salida y tipo de cámara
        selected_format = self.out_format_var.get()  # "GPX", "CSV" o "KML"
        selected_camera = self.camera_var.get()      # "GoPRO Hero 10 o anterior" o "GoPRO Hero 11 o 13"

        # Procesar cada video en su propio hilo
        for video_file in video_files:
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            output_file = os.path.join(self.output_dir.get(), base_name)
            args = argparse.Namespace()
            args.verbose = self.verbose_var.get()
            args.binary = self.binary_var.get()
            args.skip = self.skip_var.get()
            args.skip_dop = self.skip_dop_var.get()
            args.dop_limit = self.dop_limit_var.get()
            # Configurar la salida según el formato seleccionado
            if selected_format == "GPX":
                args.gpx = True; args.kml = False; args.csv = False
            elif selected_format == "CSV":
                args.gpx = False; args.kml = False; args.csv = True
            elif selected_format == "KML":
                args.gpx = False; args.kml = True; args.csv = False
            args.files = [video_file]
            args.outputfile = output_file
            # Asignar el atributo gui y el tipo de cámara
            args.gui = True
            args.camera = selected_camera

            # Iniciar el procesamiento en un hilo separado
            threading.Thread(target=self.run_processing, args=(args, selected_format)).start()
            time.sleep(0.1)  # Pequeña pausa opcional

    def run_processing(self, args, selected_format):
        try:
            # Guardar los descriptores originales
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            # Redefinir sys.exit para evitar cierre en GUI
            old_exit = sys.exit
            sys.exit = lambda code=0: None

            # Llamada a la función central de procesamiento
            main_core(args)

            # Post-procesamiento según cámara y formato
            if args.camera == "GoPRO Hero 11 o 13":
                if selected_format == "CSV":
                    self.post_process_csv(args.outputfile + ".csv")
                elif selected_format == "GPX":
                    self.post_process_gpx(args.outputfile + ".gpx")
                elif selected_format == "KML":
                    self.post_process_kml(args.outputfile + ".kml")
        except SystemExit:
            pass
        except Exception as e:
            # Se podría manejar el error de forma interna o registrar en un log externo
            pass
        finally:
            # Restaurar stdout/stderr y sys.exit
            sys.exit = old_exit
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            # Incrementar el contador de archivos procesados y actualizar la barra de progreso
            self.increment_progress()

    def increment_progress(self):
        self.processed_files += 1
        self.progress["value"] = self.processed_files
        if self.processed_files >= self.total_files:
            # Todos los archivos han sido procesados, iniciar animación hasta el 100%
            self.after(100, self.complete_progress)

    def complete_progress(self):
        current_value = self.progress["value"]
        maximum = self.progress["maximum"]
        if current_value < maximum:
            self.progress["value"] = current_value + 1
            self.after(50, self.complete_progress)
        else:
            # Una vez completado, mostrar aviso de finalización
            messagebox.showinfo("Proceso completado", "El procesamiento de archivos ha finalizado exitosamente.")



if __name__ == "__main__":
    old_exit = sys.exit
    sys.exit = lambda code=0: None
    try:
        app = GoPro2GPXGUI()
        app.mainloop()
    except Exception as e:
        print(f"Error crítico en la aplicación: {e}")
    finally:
        sys.exit = old_exit