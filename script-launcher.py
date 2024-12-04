import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import shutil

# --- Configuración general de estilos y colores en modo oscuro ---
class DarkModeStyle:
    FONT_FAMILY = "Arial"
    BG_COLOR = "#202124"  # Fondo oscuro
    BUTTON_COLOR = "#4285F4"  # Azul Google
    BUTTON_HOVER_COLOR = "#357AE8"  # Azul más oscuro
    BUTTON_TEXT_COLOR = "#ffffff"  # Texto blanco
    LABEL_COLOR = "#e8eaed"  # Texto claro
    BACK_BUTTON_COLOR = "#6c757d"  # Color gris para el botón "Volver"
    BUTTON_RADIUS = 10  # Redondeo del botón
    BUTTON_PADDING = {"padx": 20, "pady": 10}  # Ajuste de padding
    BORDER_WIDTH = 2
    BORDER_COLOR = "#444"

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
        """Crear un botón más estético y profesional con efecto hover y bordes redondeados"""
        button = tk.Button(parent, text=text, font=(DarkModeStyle.FONT_FAMILY, 14, "bold"), bg=color, fg=DarkModeStyle.BUTTON_TEXT_COLOR,
                           activebackground=DarkModeStyle.BUTTON_HOVER_COLOR if color == DarkModeStyle.BUTTON_COLOR else color,
                           activeforeground=DarkModeStyle.BUTTON_TEXT_COLOR, relief="solid", command=command, cursor="hand2", borderwidth=DarkModeStyle.BORDER_WIDTH)
        button.bind("<Enter>", lambda e: button.config(bg=DarkModeStyle.BUTTON_HOVER_COLOR if color == DarkModeStyle.BUTTON_COLOR else color))
        button.bind("<Leave>", lambda e: button.config(bg=color))
        return button

    def show_aftermarket_scripts(self):
        """Mostrar los scripts disponibles en la carpeta Scripts-AFT con título, descripción y botón de ejecución"""
        scripts_info = [
            {"title": "Dividir ficheros", "description_file": "Instrucciones de uso del script split_csv.docx", "script": "split_csv.py"},
            {"title": "Unir ficheros", "description_file": "Instrucciones de uso del script split_csv.docx", "script": "join_csv.py"}
        ]
        self.show_scripts_menu("C:/Users/Saul/Desktop/s02-ean/DataAcquisition/Script-Launcher/Scripts-formateo-datos/Scripts-AFT", scripts_info)

    def show_tarifas_scripts(self):
        """Mostrar los scripts disponibles en la carpeta Scripts-tarifas con título, descripción y botón de ejecución"""
        scripts_info = [
            {"title": "Mercedes", "description_file": "Documentación de proceso Mercedes.docx", "script": "mercedes_script.py"},
            {"title": "Turquía", "description_file": "Documentación proceso script Turquía.docx", "script": "script_turquia.py"},
            {"title": "PSA", "description_file": "Documentación proceso script PSA.docx", "script": "script_psa.py"},
            {"title": "Informe Tarifas", "description_file": "Documentación proceso script Informes de Tarifas.docx", "script": "script_tariff_report.py"}
        ]
        self.show_scripts_menu("C:/Users/Saul/Desktop/s02-ean/DataAcquisition/Script-Launcher/Scripts-formateo-datos/Scripts-tarifas", scripts_info)

    def show_scripts_menu(self, folder_path, scripts_info):
        """Mostrar los scripts disponibles en una carpeta con título y botón de ejecución, y un botón para descargar la documentación"""
        for widget in self.container.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.container, bg=DarkModeStyle.BG_COLOR)
        frame.grid(sticky="nsew")

        label = tk.Label(frame, text="Seleccione un script para ejecutar", font=(DarkModeStyle.FONT_FAMILY, 24), fg=DarkModeStyle.LABEL_COLOR, bg=DarkModeStyle.BG_COLOR)
        label.pack(pady=40)

        # Mostrar cada script con título, botón de descargar documentación y botón de ejecutar en filas de dos
        row_frame = None
        for index, script_info in enumerate(scripts_info):
            if index % 2 == 0:
                row_frame = tk.Frame(frame, bg=DarkModeStyle.BG_COLOR)
                row_frame.pack(pady=10, padx=20, fill="x")

            script_frame = tk.Frame(row_frame, bg=DarkModeStyle.BG_COLOR, highlightbackground=DarkModeStyle.BORDER_COLOR, highlightthickness=DarkModeStyle.BORDER_WIDTH)
            script_frame.pack(side=tk.LEFT, padx=10, pady=5, fill="both", expand=True)

            # Título del script (más grande y en negrita)
            title = tk.Label(script_frame, text=script_info["title"], font=(DarkModeStyle.FONT_FAMILY, 18, "bold"), fg=DarkModeStyle.LABEL_COLOR, bg=DarkModeStyle.BG_COLOR)
            title.pack(anchor="w", padx=10, pady=(10, 5))

            # Botón para descargar la documentación del script
            download_button = self.create_rounded_button(script_frame, "Descargar Documentación", lambda file=script_info["description_file"]: self.download_documentation(file), color=DarkModeStyle.BACK_BUTTON_COLOR)
            download_button.pack(anchor="w", padx=10, pady=5)

            # Botón para ejecutar el script
            execute_button = self.create_rounded_button(script_frame, "Ejecutar", lambda s=script_info["script"]: self.run_script(folder_path, s))
            execute_button.pack(anchor="w", padx=10, pady=10)

        # Botón para volver al menú principal (en gris)
        back_button = self.create_rounded_button(frame, "Volver", self.show_main_menu, color=DarkModeStyle.BACK_BUTTON_COLOR)
        back_button.pack(pady=40)

    def download_documentation(self, filename):
        """Descargar la documentación correspondiente al script"""
        source_path = os.path.join("C:/Users/Saul/Desktop/s02-ean/DataAcquisition/Script-Launcher/documentation", filename)
        destination_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        try:
            shutil.copy(source_path, destination_path)
            messagebox.showinfo("Descarga Completada", f"El archivo {filename} ha sido descargado en la carpeta de Descargas.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al descargar el archivo {filename}.\n{str(e)}")

    def run_script(self, folder, script):
        """Ejecutar un script de Python abriendo una terminal PowerShell"""
        script_path = os.path.join(folder, script)

        try:
            powershell_path = subprocess.check_output("where powershell", shell=True).decode().strip()

            # Ejecutar el script en PowerShell, abriendo la ventana de terminal y esperando el final
            command = f'{powershell_path} -NoExit -Command "& {{ Start-Process python -ArgumentList \"{script_path}\" -Wait }}"'
            subprocess.Popen(command, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al ejecutar el script {script}.\n{str(e)}")


# --- Ejecutar la aplicación ---
if __name__ == "__main__":
    app = ScriptLauncherApp()
    app.mainloop()
