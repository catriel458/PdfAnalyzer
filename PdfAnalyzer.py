import os
import shutil
import threading
import time
import datetime
import queue
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font
from tkinter.scrolledtext import ScrolledText
import PyPDF2
import unicodedata
import re

class AnalizadorPDFs:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador de PDFs")
        
        # Obtener dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Establecer ancho fijo y altura casi completa de la pantalla
        width = 650
        height = screen_height - 80  # Dejamos un pequeño margen arriba y abajo
        
        # Calcular la posición x,y para centrar la ventana
        x = (screen_width - width) // 2
        y = 0  # Posicionar cerca de la parte superior
        
        # Establecer geometría
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Variables
        self.pdf_files = []
        
        # Obtener ruta del escritorio
        self.escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Carpeta de destino fija en el escritorio
        self.output_folder = os.path.join(self.escritorio, "PDFs Encontrados")
        
        # Lista de criterios de búsqueda (cada elemento es una lista de palabras)
        # Ejemplo: [["factura", "pagada"], ["contrato", "firmado"], ["reporte"]]
        self.conditions = [
            ["documento", "importante"],
            ["factura", "pagada"],
            ["contrato", "firmado"]
        ]
        
        # Estadísticas
        self.stats = {
            "total": 0,
            "processed": 0,
            "matches": 0,
            "errors": 0
        }
        
        # Cola de procesamiento
        self.process_queue = queue.Queue()
        self.is_processing = False
        self.stats_lock = threading.Lock()
        
        # Para debugging
        self.debug_enabled = True
        
        # Configurar estilos
        self.configure_styles()
        
        # Crear la interfaz
        self.create_widgets()

    def debug_print(self, message):
        """Imprime mensajes de depuración."""
        if self.debug_enabled:
            print(f"[DEBUG] {message}")
    
    def normalizar_texto(self, texto):
        """Función para normalizar texto (eliminar acentos, espacios extras, etc.)"""
        # Convertir a minúsculas
        texto = texto.lower()
        # Eliminar acentos
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        # Eliminar espacios extras
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    def configure_styles(self):
        # Colores del tema
        self.color_primary = "#2c3e50"        # Azul oscuro principal
        self.color_header_bg = "#34495e"      # Azul gris para headers
        self.color_header_text = "#ffffff"    # Texto blanco para headers
        self.color_bg = "#ffffff"             # Fondo blanco
        self.color_text = "#2c3e50"           # Texto oscuro
        self.color_button = "#3498db"         # Botones azules
        self.color_button_text = "#ffffff"    # Texto blanco para botones
        self.color_border = "#bdc3c7"         # Bordes gris claro
        self.color_success = "#27ae60"        # Verde para éxito
        self.color_danger = "#e74c3c"         # Rojo para errores
        self.color_warning = "#f39c12"        # Naranja para advertencias
        
        # Fuentes
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.normal_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.small_font = font.Font(family="Segoe UI", size=9)
        
        # Configurar la raíz
        self.root.configure(bg=self.color_bg)
        
        # Estilos ttk
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Frame
        self.style.configure("TFrame", background=self.color_bg)
        
        # Label
        self.style.configure("TLabel", 
                             font=self.normal_font, 
                             background=self.color_bg, 
                             foreground=self.color_text)
        
        # Header Label
        self.style.configure("Header.TLabel", 
                             font=self.header_font, 
                             background=self.color_header_bg, 
                             foreground=self.color_header_text,
                             padding=10)
        
        # Title Label
        self.style.configure("Title.TLabel", 
                             font=self.title_font, 
                             background=self.color_bg, 
                             foreground=self.color_text)
        
        # Entry
        self.style.configure("TEntry", 
                             font=self.normal_font,
                             fieldbackground="#ffffff")
        
        # Button
        self.style.configure("TButton", 
                             font=self.button_font,
                             background=self.color_button,
                             foreground=self.color_button_text)
        
        # Progressbar
        self.style.configure("blue.Horizontal.TProgressbar", 
                             background=self.color_button,
                             troughcolor="#ecf0f1")
    def create_widgets(self):
        # Header principal (barra superior)
        header_frame = tk.Frame(self.root, bg=self.color_header_bg)
        header_frame.pack(fill=tk.X)
        
        # Texto del header
        header_label = tk.Label(
            header_frame, 
            text="Analizador de PDFs",
            font=self.title_font,
            bg=self.color_header_bg,
            fg=self.color_header_text,
            padx=20,
            pady=10
        )
        header_label.pack(side=tk.LEFT)
        
        # Botón de ayuda en la barra superior
        help_btn = tk.Button(
            header_frame,
            text="?",
            font=("Segoe UI", 14, "bold"),
            bg=self.color_header_bg,
            fg=self.color_header_text,
            bd=0,
            command=self.show_help,
            width=3
        )
        help_btn.pack(side=tk.RIGHT, padx=20, pady=5)
        
        # Container frame para el contenido con scrollbar
        container_frame = tk.Frame(self.root)
        container_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y scrollbar vertical
        self.main_canvas = tk.Canvas(container_frame, bg=self.color_bg)
        scrollbar = ttk.Scrollbar(container_frame, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame principal 
        self.main_frame = ttk.Frame(self.main_canvas)
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.main_frame, anchor=tk.NW)
        
        # Sección de título
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(10, 20), padx=20)
        
        main_title = tk.Label(
            title_frame,
            text="ANALIZADOR DE DOCUMENTOS PDF",
            font=("Segoe UI", 14, "bold"),
            bg=self.color_bg,
            fg=self.color_text
        )
        main_title.pack(pady=(0, 5))
        
        subtitle = tk.Label(
            title_frame,
            text="BÚSQUEDA POR CRITERIOS PERSONALIZADOS",
            font=("Segoe UI", 12),
            bg=self.color_bg,
            fg="#7f8c8d"
        )
        subtitle.pack(pady=(0, 10))
        
        # Crear las secciones principales
        self.create_criteria_section(self.main_frame)
        self.create_pdf_section(self.main_frame)
        self.create_progress_section(self.main_frame)
        self.create_buttons_section(self.main_frame)
        
        # Configurar el scrollregion
        self.main_frame.bind("<Configure>", self._on_frame_configure)
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        """Actualiza el scrollregion cuando el tamaño del frame cambia."""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        # Fijar el ancho del canvas window
        width = max(630, event.width)
        self.main_canvas.itemconfig(self.canvas_window, width=width)

    def _on_mousewheel(self, event):
        """Maneja el scroll con la rueda del mouse."""
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_criteria_section(self, parent):
        # Frame de sección de criterios
        section_frame = ttk.Frame(parent)
        section_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Header de la sección
        header_frame = tk.Frame(section_frame, bg=self.color_header_bg)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text="Criterios de Búsqueda",
            font=self.header_font,
            bg=self.color_header_bg,
            fg=self.color_header_text,
            padx=10,
            pady=8
        )
        header_label.pack(anchor=tk.W)
        
        # Contenido de la sección
        content_frame = ttk.Frame(section_frame, style="TFrame")
        content_frame.pack(fill=tk.X, pady=0)
        
        # Agregar borde con relieve
        content_canvas = tk.Canvas(content_frame, bg=self.color_bg, bd=1, relief=tk.SOLID, highlightthickness=0)
        content_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame para contenido dentro del canvas
        inner_frame = ttk.Frame(content_canvas)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Explicación
        explain_label = tk.Label(
            inner_frame,
            text="Define conjuntos de palabras que deben aparecer TODAS juntas en un PDF para que sea seleccionado:",
            font=self.small_font,
            bg=self.color_bg,
            fg="#7f8c8d",
            wraplength=580,
            justify=tk.LEFT
        )
        explain_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Frame para agregar nuevo criterio
        add_frame = ttk.Frame(inner_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            add_frame,
            text="Agregar palabras (separadas por comas):",
            font=self.normal_font,
            bg=self.color_bg,
            fg=self.color_text
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Frame horizontal para entrada y botón
        input_frame = ttk.Frame(add_frame)
        input_frame.pack(fill=tk.X)
        
        self.criteria_entry = tk.Entry(
            input_frame,
            font=self.normal_font,
            width=50
        )
        self.criteria_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.criteria_entry.bind("<Return>", lambda e: self.add_criteria())
        
        add_btn = tk.Button(
            input_frame,
            text="Agregar",
            command=self.add_criteria,
            bg=self.color_success,
            fg=self.color_button_text,
            font=self.button_font,
            relief=tk.FLAT,
            padx=15,
            pady=2
        )
        add_btn.pack(side=tk.RIGHT)
        
        # Lista de criterios actuales
        criteria_list_frame = ttk.Frame(inner_frame)
        criteria_list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        tk.Label(
            criteria_list_frame,
            text="Criterios actuales:",
            font=self.normal_font,
            bg=self.color_bg,
            fg=self.color_text
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Frame con scrollbar para la lista de criterios
        list_container = tk.Frame(criteria_list_frame, bg=self.color_bg)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar para la lista
        list_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox para mostrar criterios
        self.criteria_listbox = tk.Listbox(
            list_container,
            font=self.normal_font,
            height=6,
            yscrollcommand=list_scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.criteria_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.criteria_listbox.yview)
        
        # Botón para eliminar criterio seleccionado
        delete_btn = tk.Button(
            criteria_list_frame,
            text="Eliminar Seleccionado",
            command=self.delete_selected_criteria,
            bg=self.color_danger,
            fg=self.color_button_text,
            font=self.button_font,
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        delete_btn.pack(pady=(10, 0))
        
        # Cargar criterios iniciales
        self.refresh_criteria_list()

    def add_criteria(self):
        """Agrega un nuevo criterio de búsqueda."""
        try:
            text = self.criteria_entry.get().strip()
            if not text:
                messagebox.showwarning("Advertencia", "Por favor ingrese al menos una palabra.")
                return
            
            # Dividir por comas y limpiar espacios
            words = [word.strip().lower() for word in text.split(',') if word.strip()]
            
            if not words:
                messagebox.showwarning("Advertencia", "Por favor ingrese palabras válidas.")
                return
            
            # Verificar que no sea duplicado
            if words in self.conditions:
                messagebox.showwarning("Advertencia", "Este criterio ya existe.")
                return
            
            # Agregar a la lista
            self.conditions.append(words)
            self.refresh_criteria_list()
            self.criteria_entry.delete(0, tk.END)
            
            self.debug_print(f"Criterio agregado: {words}")
            
        except Exception as e:
            self.debug_print(f"Error al agregar criterio: {str(e)}")
            messagebox.showerror("Error", f"Error al agregar criterio: {str(e)}")

    def delete_selected_criteria(self):
        """Elimina el criterio seleccionado."""
        try:
            selection = self.criteria_listbox.curselection()
            if not selection:
                messagebox.showwarning("Advertencia", "Por favor seleccione un criterio para eliminar.")
                return
            
            index = selection[0]
            if 0 <= index < len(self.conditions):
                deleted_criteria = self.conditions.pop(index)
                self.refresh_criteria_list()
                self.debug_print(f"Criterio eliminado: {deleted_criteria}")
            
        except Exception as e:
            self.debug_print(f"Error al eliminar criterio: {str(e)}")
            messagebox.showerror("Error", f"Error al eliminar criterio: {str(e)}")

    def refresh_criteria_list(self):
        """Actualiza la lista visual de criterios."""
        try:
            self.criteria_listbox.delete(0, tk.END)
            for i, criteria in enumerate(self.conditions):
                display_text = f"{i+1}. {', '.join(criteria)}"
                self.criteria_listbox.insert(tk.END, display_text)
        except Exception as e:
            self.debug_print(f"Error al actualizar lista de criterios: {str(e)}")
    def create_pdf_section(self, parent):
        # Frame de sección
        section_frame = ttk.Frame(parent)
        section_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Header de la sección
        header_frame = tk.Frame(section_frame, bg=self.color_header_bg)
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(
            header_frame, 
            text="Documentos PDF para Analizar",
            font=self.header_font,
            bg=self.color_header_bg,
            fg=self.color_header_text,
            padx=10,
            pady=8
        )
        header_label.pack(anchor=tk.W)
        
        # Contenido de la sección
        content_frame = ttk.Frame(section_frame, style="TFrame")
        content_frame.pack(fill=tk.X, pady=0)
        
        # Agregar borde con relieve
        content_canvas = tk.Canvas(content_frame, bg=self.color_bg, bd=1, relief=tk.SOLID, highlightthickness=0)
        content_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame para contenido dentro del canvas
        inner_frame = ttk.Frame(content_canvas)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Botón de selección y contador
        select_frame = ttk.Frame(inner_frame)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_pdf_btn = tk.Button(
            select_frame, 
            text="Seleccionar PDFs", 
            command=self.select_pdf_files,
            bg=self.color_button,
            fg=self.color_button_text,
            font=self.button_font,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.select_pdf_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.file_count_label = tk.Label(
            select_frame,
            text="0 archivos seleccionados",
            font=self.normal_font,
            bg=self.color_bg,
            fg=self.color_text
        )
        self.file_count_label.pack(side=tk.LEFT)
        
        # Lista de PDFs
        list_frame = ttk.Frame(inner_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        list_label = tk.Label(
            list_frame,
            text="Archivos seleccionados:",
            font=self.normal_font,
            bg=self.color_bg,
            fg=self.color_text
        )
        list_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Scrolled text (lista de archivos)
        self.pdf_list = ScrolledText(
            list_frame, 
            height=5, 
            width=70,
            font=self.small_font,
            wrap=tk.WORD
        )
        self.pdf_list.pack(fill=tk.BOTH, expand=True)

    def create_progress_section(self, parent):
        # Frame para el botón de análisis
        analyze_frame = ttk.Frame(parent)
        analyze_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
    
        # Botón de análisis centrado
        button_container = tk.Frame(analyze_frame, bg=self.color_bg)
        button_container.pack(fill=tk.X)
        
        self.analyze_btn = tk.Button(
            button_container,
            text="🔍 ANALIZAR PDFs",
            command=self.start_analysis,
            bg=self.color_warning,
            fg=self.color_button_text,
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            padx=30,
            pady=12
        )
        self.analyze_btn.pack()
        
        # Panel de estadísticas
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Header de la sección
        stats_header = tk.Frame(stats_frame, bg=self.color_header_bg)
        stats_header.pack(fill=tk.X)
        
        stats_label = tk.Label(
            stats_header, 
            text="Estadísticas del Análisis",
            font=self.header_font,
            bg=self.color_header_bg,
            fg=self.color_header_text,
            padx=10,
            pady=8
        )
        stats_label.pack(anchor=tk.W)
        
        # Contenido de estadísticas
        stats_content = ttk.Frame(stats_frame)
        stats_content.pack(fill=tk.X)
        
        # Agregar borde con relieve
        stats_canvas = tk.Canvas(stats_content, bg=self.color_bg, bd=1, relief=tk.SOLID, highlightthickness=0)
        stats_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Frame para las estadísticas
        self.stats_container = ttk.Frame(stats_canvas)
        self.stats_container.pack(fill=tk.X, padx=15, pady=15)
        
        # Crear las etiquetas de estadísticas
        self.create_stats_labels()
        
        # Barra de progreso
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Header de la barra de progreso
        progress_header = tk.Frame(progress_frame, bg=self.color_header_bg)
        progress_header.pack(fill=tk.X)
        
        progress_title = tk.Label(
            progress_header, 
            text="Progreso del Análisis",
            font=self.header_font,
            bg=self.color_header_bg,
            fg=self.color_header_text,
            padx=10,
            pady=8
        )
        progress_title.pack(anchor=tk.W)
        
        # Contenido de la barra de progreso
        progress_content = ttk.Frame(progress_frame)
        progress_content.pack(fill=tk.X)
        
        # Agregar borde con relieve
        progress_canvas = tk.Canvas(progress_content, bg=self.color_bg, bd=1, relief=tk.SOLID, highlightthickness=0)
        progress_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Contenido
        inner_progress = ttk.Frame(progress_canvas)
        inner_progress.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.progress_label = tk.Label(
            inner_progress,
            text="Progreso: 0%",
            font=self.normal_font,
            bg=self.color_bg,
            fg=self.color_text
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            inner_progress, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var,
            style="blue.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X)

    def create_buttons_section(self, parent):
        # Barra inferior con botones
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        # Frame para centrar botones
        buttons_container = tk.Frame(bottom_frame, bg=self.color_bg)
        buttons_container.pack()
        
        self.clear_btn = tk.Button(
            buttons_container,
            text="🗑️ Limpiar Todo",
            command=self.clear_all,
            bg="#95a5a6",
            fg=self.color_button_text,
            font=self.button_font,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.help_btn = tk.Button(
            buttons_container,
            text="❓ Ayuda",
            command=self.show_help,
            bg=self.color_button,
            fg=self.color_button_text,
            font=self.button_font,
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.help_btn.pack(side=tk.LEFT, padx=5)

    def create_stats_labels(self):
        # Eliminar widgets existentes
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        # Crear grid para las estadísticas
        stats_grid = ttk.Frame(self.stats_container)
        stats_grid.pack(fill=tk.X)
        
        # Configurar columnas con pesos iguales
        for i in range(2):
            stats_grid.columnconfigure(i, weight=1)
        
        # Total PDFs
        total_frame = tk.Frame(stats_grid, bg="#ecf0f1", bd=1, relief=tk.SOLID)
        total_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.total_label = tk.Label(
            total_frame, 
            text=f"Total PDFs: {self.stats['total']}",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1",
            fg=self.color_text
        )
        self.total_label.pack(padx=10, pady=10)
        
        # Procesados
        processed_frame = tk.Frame(stats_grid, bg="#ecf0f1", bd=1, relief=tk.SOLID)
        processed_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.processed_label = tk.Label(
            processed_frame, 
            text=f"Procesados: {self.stats['processed']}",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1",
            fg=self.color_text
        )
        self.processed_label.pack(padx=10, pady=10)
        
        # Coincidencias
        matches_frame = tk.Frame(stats_grid, bg="#d5f4e6", bd=1, relief=tk.SOLID)
        matches_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.matches_label = tk.Label(
            matches_frame, 
            text=f"Encontrados: {self.stats['matches']}",
            font=("Segoe UI", 11, "bold"),
            foreground=self.color_success,
            bg="#d5f4e6"
        )
        self.matches_label.pack(padx=10, pady=10)
        
        # Errores
        errors_frame = tk.Frame(stats_grid, bg="#fadbd8", bd=1, relief=tk.SOLID)
        errors_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.errors_label = tk.Label(
            errors_frame, 
            text=f"Errores: {self.stats['errors']}",
            font=("Segoe UI", 11, "bold"),
            foreground=self.color_danger,
            bg="#fadbd8"
        )
        self.errors_label.pack(padx=10, pady=10)

    def select_pdf_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if files:
            self.pdf_files = list(files)
            self.file_count_label.config(text=f"{len(self.pdf_files)} archivos seleccionados")
            
            # Actualizar estadísticas
            self.stats["total"] = len(self.pdf_files)
            self.stats["processed"] = 0
            self.stats["matches"] = 0
            self.stats["errors"] = 0
            self.update_stats_display()
            
            # Mostrar lista de archivos
            self.pdf_list.delete(1.0, tk.END)
            for i, file in enumerate(self.pdf_files):
                self.pdf_list.insert(tk.END, f"{i+1}. {os.path.basename(file)}\n")
            
            self.debug_print(f"Seleccionados {len(self.pdf_files)} archivos")
    
    def update_stats_display(self):
        # Actualizar las etiquetas con los valores actuales
        self.total_label.config(text=f"Total PDFs: {self.stats['total']}")
        self.processed_label.config(text=f"Procesados: {self.stats['processed']}")
        self.matches_label.config(text=f"Encontrados: {self.stats['matches']}")
        self.errors_label.config(text=f"Errores: {self.stats['errors']}")
        
        # Forzar actualización de la interfaz
        self.root.update_idletasks()
    
    def clear_all(self):
        """Limpia todos los datos y restablece la interfaz."""
        try:
            # Confirmar si está en medio de un procesamiento
            if self.is_processing:
                result = messagebox.askyesno(
                    "Procesamiento en curso", 
                    "¿Está seguro de que desea detener el procesamiento actual y limpiar todos los datos?"
                )
                if not result:
                    return
            
            # Detener cualquier procesamiento en curso
            self.is_processing = False
            
            # Limpiar listas y resultados
            self.pdf_files = []
            self.file_count_label.config(text="0 archivos seleccionados")
            self.pdf_list.delete(1.0, tk.END)
            
            # Restablecer estadísticas
            self.stats["total"] = 0
            self.stats["processed"] = 0
            self.stats["matches"] = 0
            self.stats["errors"] = 0
            self.update_stats_display()
            
            # Restablecer progreso
            self.progress_var.set(0)
            self.progress_label.config(text="Progreso: 0%")
            
            # Vaciar la cola de procesamiento
            while not self.process_queue.empty():
                try:
                    self.process_queue.get_nowait()
                    self.process_queue.task_done()
                except queue.Empty:
                    break
            
            # Reiniciar la queue
            self.process_queue = queue.Queue()
            
            # Restablecer botones
            self.analyze_btn.config(state=tk.NORMAL)
            self.select_pdf_btn.config(state=tk.NORMAL)
            
            # Actualizar la interfaz
            self.root.update_idletasks()
            
            self.debug_print("Interfaz reiniciada")
        except Exception as e:
            self.debug_print(f"Error al limpiar: {str(e)}")

    def init_log_file(self):
        """Inicializa el archivo de registro con encabezados."""
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.log_filename), exist_ok=True)
            
            with open(self.log_filename, 'w', encoding='utf-8') as f:
                f.write("# INFORME DE ANÁLISIS DE PDFs\n")
                f.write(f"# Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total de archivos analizados: {len(self.pdf_files)}\n")
                f.write(f"# Criterios de búsqueda:\n")
                for i, condition in enumerate(self.conditions):
                    f.write(f"#   Criterio {i+1}: {', '.join(condition)}\n")
                f.write("\n# RESULTADOS\n")
                f.write("# --------------------------------------------------------------\n")
                f.write("# ARCHIVO | CRITERIO ENCONTRADO | UBICACIÓN\n")
                f.write("# --------------------------------------------------------------\n\n")
            
            self.debug_print(f"Archivo de registro creado: {self.log_filename}")
        except Exception as e:
            self.debug_print(f"Error al crear archivo de registro: {str(e)}")
            raise
    
    def log_match(self, filename, condition, dest_path):
        """Registra una coincidencia en el archivo de registro."""
        try:
            with open(self.log_filename, 'a', encoding='utf-8') as f:
                f.write(f"{filename} | {', '.join(condition)} | {dest_path}\n")
        except Exception as e:
            self.debug_print(f"Error al registrar coincidencia: {str(e)}")
    
    def log_summary(self):
        """Añade un resumen al final del archivo de registro."""
        try:
            with open(self.log_filename, 'a', encoding='utf-8') as f:
                f.write("\n# --------------------------------------------------------------\n")
                f.write("# RESUMEN\n")
                f.write("# --------------------------------------------------------------\n")
                f.write(f"# Total de archivos procesados: {self.stats['processed']}\n")
                f.write(f"# Total de archivos encontrados: {self.stats['matches']}\n")
                f.write(f"# Total de errores: {self.stats['errors']}\n")
                f.write(f"# Porcentaje de éxito: {(self.stats['matches'] / max(1, self.stats['total'])) * 100:.2f}%\n")
                f.write(f"# Finalizado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            self.debug_print(f"Error al crear resumen del log: {str(e)}")

    def start_analysis(self):
        """Inicia el análisis de PDFs."""
        try:
            self.debug_print("Iniciando análisis...")
            
            # Asegurarse de que no hay un procesamiento en curso
            if self.is_processing:
                messagebox.showwarning("Advertencia", "Hay un análisis en curso. Por favor, espere a que finalice.")
                return
            
            # Verificar que hay PDFs seleccionados
            if not self.pdf_files:
                messagebox.showwarning("Advertencia", "No hay archivos PDF seleccionados.")
                return
            
            # Verificar que hay criterios definidos
            if not self.conditions:
                messagebox.showwarning("Advertencia", "No hay criterios de búsqueda definidos. Por favor agregue al menos un criterio.")
                return
            
            # Crear carpeta de destino si no existe
            if not os.path.exists(self.output_folder):
                try:
                    os.makedirs(self.output_folder)
                    self.debug_print(f"Carpeta de destino creada: {self.output_folder}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la carpeta de destino: {str(e)}")
                    self.debug_print(f"Error creando carpeta de destino: {str(e)}")
                    return
            
            # Reiniciar el sistema de procesamiento
            self.reset_processing_system()
            
            # Restablecer estadísticas pero mantener el total
            with self.stats_lock:
                self.stats["processed"] = 0
                self.stats["matches"] = 0
                self.stats["errors"] = 0
            self.update_stats_display()
            
            # Configurar la interfaz para el procesamiento
            self.analyze_btn.config(state=tk.DISABLED)
            self.select_pdf_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
            
            # Añadir todos los archivos a la cola
            for pdf_path in self.pdf_files:
                self.process_queue.put(pdf_path)
                self.debug_print(f"Añadido a la cola: {os.path.basename(pdf_path)}")
            
            # Iniciar el procesamiento
            self.is_processing = True
            
            # Resetear la barra de progreso
            self.progress_var.set(0)
            self.progress_label.config(text="Progreso: 0%")
            
            # Crear archivo de registro
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_filename = os.path.join(
                self.output_folder, 
                f"reporte_analisis_{timestamp}.txt"
            )
            self.debug_print(f"Nombre del archivo de registro: {self.log_filename}")
            
            # Inicializar archivo de registro
            self.init_log_file()
            
            # Iniciar procesamiento en hilos
            num_threads = min(4, len(self.pdf_files))  # Limitar a 4 hilos como máximo
            self.processing_threads = []
            
            for i in range(num_threads):
                thread = threading.Thread(target=self.process_pdfs_thread, args=(i,))
                thread.daemon = True
                self.processing_threads.append(thread)
                thread.start()
                self.debug_print(f"Hilo de procesamiento {i} iniciado")
            
            # Iniciar hilo de monitoreo
            self.monitor_thread = threading.Thread(target=self.monitor_progress)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.debug_print("Hilo de monitoreo iniciado")
            
            # Actualizar la interfaz
            self.root.update_idletasks()
            
        except Exception as e:
            self.debug_print(f"Error al iniciar análisis: {str(e)}")
            messagebox.showerror("Error", f"Error al iniciar el análisis: {str(e)}")
            self.is_processing = False

    def monitor_progress(self):
        """Monitorea el progreso del procesamiento y actualiza la UI."""
        try:
            self.debug_print("Monitor de progreso iniciado")
            while self.is_processing:
                try:
                    # Verificar si todos los archivos han sido procesados
                    if self.stats["processed"] >= self.stats["total"]:
                        # Todos los archivos han sido procesados
                        self.debug_print("Todos los archivos procesados, finalizando")
                        self.root.after(0, self.finalize_processing)
                        break
                        
                    # Calcular progreso
                    progress = (self.stats["processed"] / max(1, self.stats["total"])) * 100
                    
                    # Actualizar UI (en el hilo principal)
                    self.root.after(0, lambda p=progress: self.update_progress(p))
                    
                    # Esperar un poco antes de verificar de nuevo
                    time.sleep(0.2)
                except Exception as e:
                    self.debug_print(f"Error en ciclo de monitoreo: {str(e)}")
            
            self.debug_print("Monitor de progreso finalizado")
        except Exception as e:
            self.debug_print(f"Error fatal en hilo de monitoreo: {str(e)}")

    def reset_processing_system(self):
        """Reinicia el sistema de procesamiento para dejarlo listo para un nuevo análisis."""
        try:
            # Detener cualquier procesamiento en curso
            self.is_processing = False
            
            # Vaciar la cola de procesamiento
            while not self.process_queue.empty():
                try:
                    self.process_queue.get_nowait()
                    self.process_queue.task_done()
                except queue.Empty:
                    break
            
            # Reiniciar la queue
            self.process_queue = queue.Queue()
            
            # Restablecer la barra de progreso
            self.progress_var.set(0)
            self.progress_label.config(text="Progreso: 0%")
            
            # Actualizar la interfaz
            self.root.update_idletasks()
            
            self.debug_print("Sistema de procesamiento reiniciado")
        except Exception as e:
            self.debug_print(f"Error al reiniciar el sistema: {str(e)}")
        
    def check_pdf_conditions(self, pdf_text):
        """Verifica si un PDF cumple alguna de las condiciones."""
        try:
            # Si el texto está vacío, no cumple ninguna condición
            if not pdf_text:
                return False, None
            
            # Normalizar el texto para buscar coincidencias de manera más robusta
            pdf_text_norm = self.normalizar_texto(pdf_text)
            
            # Verificar cada conjunto de condiciones
            for condition in self.conditions:
                # Verificar si todos los términos de esta condición están presentes
                all_terms_found = True
                for term in condition:
                    term_norm = self.normalizar_texto(term)
                    if term_norm not in pdf_text_norm:
                        all_terms_found = False
                        break
                
                if all_terms_found:
                    return True, condition
            
            return False, None
        except Exception as e:
            self.debug_print(f"Error al verificar condiciones: {str(e)}")
            # En caso de error, asumir que no cumple condiciones
            return False, None
        
    def process_pdfs_thread(self, thread_id):
        """Función para procesar PDFs en un hilo separado."""
        try:
            self.debug_print(f"Hilo {thread_id} iniciado")
            while self.is_processing:
                try:
                    # Intentar obtener un archivo de la cola
                    try:
                        pdf_path = self.process_queue.get(block=False)
                        self.debug_print(f"Hilo {thread_id} procesando: {os.path.basename(pdf_path)}")
                    except queue.Empty:
                        # No hay más archivos, terminar este hilo
                        self.debug_print(f"Hilo {thread_id} sin más archivos para procesar")
                        break
                    
                    # Procesar el archivo
                    try:
                        filename = os.path.basename(pdf_path)
                        
                        # Extraer el texto del PDF
                        pdf_text = self.extract_pdf_text(pdf_path)
                        
                        # Verificar si el PDF cumple alguna de las condiciones
                        match_found, condition_matched = self.check_pdf_conditions(pdf_text)
                        
                        if match_found:
                            # El PDF cumple criterios, moverlo a la carpeta de destino
                            self.debug_print(f"Archivo cumple criterios: {filename}")
                            
                            # Incrementar contador de coincidencias
                            with self.stats_lock:
                                self.stats["matches"] += 1
                            
                            dest_path = os.path.join(self.output_folder, filename)
                            
                            # Mover el archivo
                            shutil.move(pdf_path, dest_path)
                            self.debug_print(f"Archivo movido a: {dest_path}")
                            
                            # Registrar en log
                            self.log_match(filename, condition_matched, dest_path)
                            
                            # Actualizar UI
                            self.root.after(0, lambda f=filename, c=condition_matched: 
                                        self.update_ui_match(f, c))
                        
                        else:
                            # El PDF no cumple criterios, no se mueve
                            self.debug_print(f"Archivo no cumple criterios: {filename}")
                            self.root.after(0, lambda f=filename: self.update_ui_no_match(f))
                    
                    except Exception as e:
                        # Incrementar contador de errores
                        with self.stats_lock:
                            self.stats["errors"] += 1
                        
                        self.debug_print(f"Error procesando {filename}: {str(e)}")
                        
                        # Actualizar UI (en el hilo principal)
                        self.root.after(0, lambda f=filename, e=str(e): self.update_ui_error(f, e))
                    
                    finally:
                        # Incrementar contador de procesados siempre, incluso si hay error
                        with self.stats_lock:
                            self.stats["processed"] += 1
                        
                        # Marcar como completado en la cola
                        self.process_queue.task_done()
                        
                        # Forzar una actualización de la interfaz de usuario
                        self.root.after(0, self.update_stats_display)
                    
                except Exception as e:
                    self.debug_print(f"Error en procesamiento del hilo {thread_id}: {str(e)}")
            
            self.debug_print(f"Hilo {thread_id} finalizado")
        except Exception as e:
            self.debug_print(f"Error fatal en hilo {thread_id}: {str(e)}")

    def extract_pdf_text(self, pdf_path):
        """Extrae todo el texto de un archivo PDF."""
        try:
            with open(pdf_path, 'rb') as file:
                try:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    
                    # Extraer texto de todas las páginas
                    for page in reader.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:  # Verificar que la extracción fue exitosa
                                text += page_text
                        except Exception as e:
                            self.debug_print(f"Error al extraer texto de una página: {str(e)}")
                    
                    return text
                except Exception as e:
                    self.debug_print(f"Error al crear PdfReader: {str(e)}")
                    return ""
        except Exception as e:
            self.debug_print(f"Error al abrir el archivo PDF {pdf_path}: {str(e)}")
            raise
        
    def update_progress(self, progress):
        """Actualiza la barra de progreso."""
        try:
            self.progress_var.set(progress)
            self.progress_label.config(text=f"Progreso: {progress:.1f}%")
            
            # Cambiar el color de la barra según el progreso
            if progress < 30:
                self.style.configure("blue.Horizontal.TProgressbar", background='#3498db')
            elif progress < 70:
                self.style.configure("blue.Horizontal.TProgressbar", background='#2ecc71')
            else:
                self.style.configure("blue.Horizontal.TProgressbar", background='#27ae60')
            
            # Forzar actualización
            self.root.update_idletasks()
        except Exception as e:
            self.debug_print(f"Error al actualizar progreso: {str(e)}")
    
    def update_ui_match(self, filename, condition):
        """Actualiza la UI cuando se encuentra una coincidencia."""
        try:
            # Solo actualizar estadísticas
            self.update_stats_display()
        except Exception as e:
            self.debug_print(f"Error en update_ui_match: {str(e)}")
    
    def update_ui_no_match(self, filename):
        """Actualiza la UI cuando no se encuentra coincidencia."""
        try:
            # Solo actualizar estadísticas
            self.update_stats_display()
        except Exception as e:
            self.debug_print(f"Error en update_ui_no_match: {str(e)}")
    
    def update_ui_error(self, filename, error_msg):
        """Actualiza la UI cuando ocurre un error."""
        try:
            # Solo actualizar estadísticas
            self.update_stats_display()
        except Exception as e:
            self.debug_print(f"Error en update_ui_error: {str(e)}")
        
    def finalize_processing(self):
        """Finaliza el procesamiento y muestra resultados."""
        try:
            if not self.is_processing:  # Evitar finalizar múltiples veces
                return
                
            self.debug_print("Finalizando procesamiento")
            self.is_processing = False
            
            # Establecer progreso a 100% completado
            self.progress_var.set(100)
            self.progress_label.config(text="Progreso: 100% - ¡Completado!")
            
            # Añadir resumen al log
            try:
                self.log_summary()
            except Exception as e:
                self.debug_print(f"Error al crear resumen de log: {str(e)}")
            
            # Habilitar botones nuevamente
            self.analyze_btn.config(state=tk.NORMAL)
            self.select_pdf_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
            
            # Mostrar mensaje con resultados
            if self.stats['matches'] > 0:
                message = f"¡Análisis completado con éxito!\n\n" \
                        f"📊 Resultados:\n" \
                        f"• Total de PDFs analizados: {self.stats['processed']}\n" \
                        f"• PDFs que cumplen criterios: {self.stats['matches']}\n" \
                        f"• Errores encontrados: {self.stats['errors']}\n\n" \
                        f"📁 Los archivos encontrados se movieron a:\n" \
                        f"{self.output_folder}\n\n" \
                        f"📄 Se generó un informe detallado:\n" \
                        f"{os.path.basename(self.log_filename)}"
                
                messagebox.showinfo("✅ Análisis Completado", message)
            else:
                message = f"Análisis completado.\n\n" \
                        f"📊 Resultados:\n" \
                        f"• Total de PDFs analizados: {self.stats['processed']}\n" \
                        f"• PDFs que cumplen criterios: {self.stats['matches']}\n" \
                        f"• Errores encontrados: {self.stats['errors']}\n\n" \
                        f"ℹ️ No se encontraron PDFs que cumplieran con los criterios definidos.\n" \
                        f"Considere revisar o modificar los criterios de búsqueda."
                
                messagebox.showinfo("ℹ️ Análisis Completado", message)
            
            self.debug_print("Procesamiento finalizado exitosamente")
            
        except Exception as e:
            self.debug_print(f"Error al finalizar procesamiento: {str(e)}")
            messagebox.showerror("Error", f"Error al finalizar el procesamiento: {str(e)}")
    
    def show_help(self):
        """Muestra la ventana de ayuda."""
        help_text = """
🔍 ANALIZADOR DE PDFs - GUÍA DE USO

Este programa te permite buscar archivos PDF que contengan palabras específicas 
y moverlos automáticamente a una carpeta organizada.

📋 CÓMO USAR:

1️⃣ DEFINIR CRITERIOS DE BÚSQUEDA:
   • En la sección "Criterios de Búsqueda", agrega conjuntos de palabras
   • Ejemplo: "factura, pagada" (el PDF debe tener AMBAS palabras)
   • Ejemplo: "contrato" (el PDF debe tener esta palabra)
   • Puedes agregar múltiples criterios
   • Si un PDF cumple CON CUALQUIER criterio, será seleccionado

2️⃣ SELECCIONAR PDFs:
   • Haz clic en "Seleccionar PDFs"
   • Elige uno o varios archivos PDF para analizar
   • Puedes seleccionar cientos de archivos a la vez

3️⃣ ANALIZAR:
   • Haz clic en "🔍 ANALIZAR PDFs"
   • El programa buscará en cada PDF las palabras de tus criterios
   • Los PDFs que cumplan criterios se moverán a "PDFs Encontrados"

📊 ESTADÍSTICAS:
   • Total PDFs: Archivos seleccionados para analizar
   • Procesados: Archivos ya analizados
   • Encontrados: Archivos que cumplen criterios (movidos)
   • Errores: Archivos que no se pudieron procesar

💡 CONSEJOS:
   • Las búsquedas ignoran acentos y mayúsculas
   • Usa palabras clave específicas para mejores resultados
   • El programa genera un reporte detallado de los resultados

📁 CARPETAS:
   • Los PDFs encontrados se mueven a: "PDFs Encontrados" (en tu escritorio)
   • Los archivos originales se conservan en esa carpeta
   • Se genera un archivo de reporte con los detalles del análisis

🔧 OPCIONES:
   • "🗑️ Limpiar Todo": Reinicia todo el programa
   • "❓ Ayuda": Muestra esta ventana de ayuda

¿Necesitas más ayuda? Revisa los criterios y asegúrate de que las palabras 
que buscas realmente aparezcan en los PDFs.
        """
        
        try:
            # Ventana de ayuda
            help_window = tk.Toplevel(self.root)
            help_window.title("Ayuda - Analizador de PDFs")
            help_window.geometry("700x650")
            help_window.configure(bg=self.color_bg)
            help_window.transient(self.root)
            help_window.grab_set()
            
            # Header de la ventana
            header_frame = tk.Frame(help_window, bg=self.color_header_bg)
            header_frame.pack(fill=tk.X)
            
            header_label = tk.Label(
                header_frame, 
                text="📖 Guía de Uso del Analizador de PDFs",
                font=self.header_font,
                bg=self.color_header_bg,
                fg=self.color_header_text,
                padx=15,
                pady=12
            )
            header_label.pack(anchor=tk.W)
            
            # Contenido de ayuda
            help_text_widget = ScrolledText(
                help_window, 
                wrap=tk.WORD, 
                padx=15, 
                pady=15, 
                font=self.normal_font,
                bg="#f8f9fa",
                fg=self.color_text
            )
            help_text_widget.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            help_text_widget.insert(tk.END, help_text)
            help_text_widget.config(state=tk.DISABLED)
            
            # Botón de cerrar
            close_btn_frame = tk.Frame(help_window, bg=self.color_bg)
            close_btn_frame.pack(pady=15)
            
            close_button = tk.Button(
                close_btn_frame, 
                text="✅ Entendido",
                command=help_window.destroy,
                bg=self.color_success,
                fg=self.color_button_text,
                font=self.button_font,
                relief=tk.FLAT,
                padx=25,
                pady=8
            )
            close_button.pack()
        except Exception as e:
            self.debug_print(f"Error al mostrar ayuda: {str(e)}")

def main():
    try:
        root = tk.Tk()
        # Configurar icono (opcional)
        try:
            root.iconbitmap('icon.ico')
        except:
            pass  # Si no hay icono disponible, continuar sin él
            
        app = AnalizadorPDFs(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal en la aplicación: {str(e)}")
        messagebox.showerror("Error Fatal", f"Error al iniciar la aplicación: {str(e)}")

if __name__ == "__main__":
    main()                        