import tkinter as tk
from tkinter import messagebox
import os
import subprocess

# --- Configuración general de estilos y colores en modo oscuro ---
class DarkModeStyle:
    FONT_FAMILY = "Arial"
    BG_COLOR = "#202124"  # Fondo oscuro
    BUTTON_COLOR = "#4285F4"  # Azul Google
    BUTTON_HOVER_COLOR = "#357AE8"  # Azul más oscuro
    BUTTON_TEXT_COLOR = "#ffffff"  # Texto blanco
    LABEL_COLOR = "#e8eaed"  # Texto claro
    BACK_BUTTON_COLOR = "#6c757d"  # Color gris para el botón "Volver"
    BUTTON_RADIUS = 20  # Redondeo del botón
    BUTTON_PADDING = {"padx": 20, "pady": 10}  # Ajuste de padding

# --- Aplicación principal ---
class ScriptLauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Script Launcher")
        self.configure(bg=DarkModeStyle.BG_COLOR)
        self.center_window(800, 600)  # Centrar ventana
        self.state('zoomed')  # Iniciar en pantalla completa

        # Crear el contenedor de la página principal
        self.container = tk.Frame(self, bg=DarkModeStyle.BG_COLOR)
        self.container.grid(sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Mostrar la página de selección inicial
        self.show_main_menu()

        # Asegurar que la aplicación sea responsive al redimensionar la ventana
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def center_window(self, width, height):
        """Centrar la ventana en la pantalla"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int(screen_height / 2 - height / 2)
        position_right = int(screen_width / 2 - width / 2)
        self.geometry(f'{width}x{height}+{position_right}+{position_top}')

    def show_main_menu(self):
        """Mostrar el menú principal para seleccionar scripts de Aftermarket o Tarifas"""
        for widget in self.container.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.container, bg=DarkModeStyle.BG_COLOR)
        frame.grid(sticky="nsew")

        label = tk.Label(frame, text="Seleccione el tipo de scripts", font=(DarkModeStyle.FONT_FAMILY, 24), fg=DarkModeStyle.LABEL_COLOR, bg=DarkModeStyle.BG_COLOR)
        label.pack(pady=40)

        # Frame para botones alineados horizontalmente
        button_frame = tk.Frame(frame, bg=DarkModeStyle.BG_COLOR)
        button_frame.pack(pady=20)

        # Botón para scripts de Aftermarket
        aft_button = self.create_rounded_button(button_frame, "Scripts de Aftermarket", self.show_aftermarket_scripts)
        aft_button.pack(side=tk.LEFT, padx=20, pady=10)

        # Botón para scripts de Tarifas
        tarifas_button = self.create_rounded_button(button_frame, "Scripts de Tarifas", self.show_tarifas_scripts)
        tarifas_button.pack(side=tk.LEFT, padx=20, pady=10)

    def create_rounded_button(self, parent, text, command, color=DarkModeStyle.BUTTON_COLOR):
        """Crear un botón redondeado con efecto hover"""
        button = tk.Button(parent, text=text, font=(DarkModeStyle.FONT_FAMILY, 16), bg=color, fg=DarkModeStyle.BUTTON_TEXT_COLOR, 
                           activebackground=DarkModeStyle.BUTTON_HOVER_COLOR if color == DarkModeStyle.BUTTON_COLOR else color, 
                           activeforeground=DarkModeStyle.BUTTON_TEXT_COLOR, relief="flat", command=command, cursor="hand2", borderwidth=0)
        button.bind("<Enter>", lambda e: button.config(bg=DarkModeStyle.BUTTON_HOVER_COLOR if color == DarkModeStyle.BUTTON_COLOR else color))
        button.bind("<Leave>", lambda e: button.config(bg=color))
        return button

    def show_aftermarket_scripts(self):
        """Mostrar los scripts disponibles en la carpeta Scripts-AFT con título, descripción y botón de ejecución"""
        scripts_info = [
            {"title": "Dividir ficheros", "description": "El script descomprime archivos CSV desde //s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS/FICHERO_ORIGINAL, "
                                                         "divide cada CSV en 4 partes y guarda las partes en //s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS.",
             "script": "split_csv.py"},
            {"title": "Unir ficheros", "description": "El script une las partes de archivos CSV ubicados en //s02-ean/DataAcquisition/AFTERMARKET/_DIVIDIR_FICHEROS y genera un "
                                                      "archivo combinado con el prefijo joined_ en la misma carpeta.", "script": "join_csv.py"}
        ]
        self.show_scripts_menu("C:/Users/Saul/Desktop/s02-ean/DataAcquisition/Script-Launcher/Scripts-formateo-datos/Scripts-AFT", scripts_info)

    def show_tarifas_scripts(self):
        """Mostrar los scripts disponibles en la carpeta Scripts-tarifas con título, descripción y botón de ejecución"""
        scripts_info = [
            {"title": "Mercedes", "description": "El script descomprime archivos desde \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESCARGAS\MERCEDES, "
                                                 "procesa XML y genera un CSV y TXT en \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\MB1, \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES"
                                                 "\SM1, y \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA\Pendientes.", "script": "mercedes_script.py"},
            {"title": "Turquía", "description": "El script se conecta a un servidor FTP, descarga archivos TXT, los procesa generando archivos CSV en formato 1-2-3-4 "
                                                 "y los guarda en \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\[brand_code]\TUR y \\s02-ean\DataAcquisition\TARIFAS_ORIGINALES\_DESATENDIDA"
                                                 "\Pendientes.", "script": "script_turquia.py"}
        ]
        self.show_scripts_menu("C:/Users/Saul/Desktop/s02-ean/DataAcquisition/Script-Launcher/Scripts-formateo-datos/Scripts-tarifas", scripts_info)

    def show_scripts_menu(self, folder_path, scripts_info):
        """Mostrar los scripts disponibles en una carpeta con título, descripción y botón de ejecución"""
        for widget in self.container.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.container, bg=DarkModeStyle.BG_COLOR)
        frame.grid(sticky="nsew")

        label = tk.Label(frame, text="Seleccione un script para ejecutar", font=(DarkModeStyle.FONT_FAMILY, 24), fg=DarkModeStyle.LABEL_COLOR, bg=DarkModeStyle.BG_COLOR)
        label.pack(pady=40)

        # Mostrar cada script con título, descripción y botón de ejecutar
        for script_info in scripts_info:
            script_frame = tk.Frame(frame, bg=DarkModeStyle.BG_COLOR)
            script_frame.pack(pady=20, padx=50, fill="x")  # Añadido padding horizontal para centrar el contenido

            # Título del script (más grande y en negrita)
            title = tk.Label(script_frame, text=script_info["title"], font=(DarkModeStyle.FONT_FAMILY, 20, "bold"), fg=DarkModeStyle.LABEL_COLOR, bg=DarkModeStyle.BG_COLOR)
            title.pack(anchor="w", padx=20)

            # Descripción del script (debajo del título)
            description = tk.Label(script_frame, text=script_info["description"], font=(DarkModeStyle.FONT_FAMILY, 12), fg="#888888", bg=DarkModeStyle.BG_COLOR, wraplength=700, justify="left")
            description.pack(anchor="w", padx=20, pady=5)

            # Botón para ejecutar el script (debajo de la descripción)
            execute_button = self.create_rounded_button(script_frame, "Ejecutar", lambda s=script_info["script"]: self.run_script(folder_path, s))
            execute_button.pack(anchor="w", padx=20, pady=10)

        # Botón para volver al menú principal (en gris)
        back_button = self.create_rounded_button(frame, "Volver", self.show_main_menu, color=DarkModeStyle.BACK_BUTTON_COLOR)
        back_button.pack(pady=40)

    def run_script(self, folder, script):
        """Ejecutar un script de Python abriendo una terminal PowerShell"""
        script_path = os.path.join(folder, script)

        try:
            powershell_path = subprocess.check_output("where powershell", shell=True).decode().strip()

            # Ejecutar el script en PowerShell, abriendo la ventana de terminal y esperando el final
            command = f'{powershell_path} -NoExit python "{script_path}"'
            subprocess.Popen(command, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al ejecutar el script {script}.\n{str(e)}")


# --- Ejecutar la aplicación ---
if __name__ == "__main__":
    app = ScriptLauncherApp()
    app.mainloop()
