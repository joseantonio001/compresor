import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import zipfile
import os
import gzip
import bz2
import lzma
from datetime import datetime
from tqdm import tqdm
import py7zr
import shutil
import threading
from zipfile import ZipInfo

class CompresorAvanzado:
    def __init__(self):
        self.nivel_compresion = 6
        self.formatos_soportados = {
            'zip': self._comprimir_zip,
            '7z': self._comprimir_7z,
            'gz': self._comprimir_gzip,
            'bz2': self._comprimir_bz2,
            'xz': self._comprimir_lzma
        }
    
    def establecer_nivel_compresion(self, nivel):
        self.nivel_compresion = min(9, max(0, int(nivel)))
    
    def comprimir(self, archivos, destino, formato='zip', nombre=None, password=None):
        if formato not in self.formatos_soportados:
            raise ValueError(f"Formato no soportado. Opciones: {', '.join(self.formatos_soportados.keys())}")
        
        nombre = nombre or f"comprimido_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        nombre_archivo = f"{nombre}.{formato}"
        ruta_completa = os.path.join(destino, nombre_archivo)
        
        for archivo in archivos:
            if not os.path.exists(archivo):
                raise FileNotFoundError(f"El archivo/directorio no existe: {archivo}")
        
        metodo_compresion = self.formatos_soportados[formato]
        metodo_compresion(archivos, ruta_completa, password)
        
        return ruta_completa
    
    def _comprimir_zip(self, archivos, destino, password=None):
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if password:
                zipf.setpassword(password.encode('utf-8'))
            
            for archivo in archivos:
                if os.path.isfile(archivo):
                    self._agregar_archivo_zip(zipf, archivo)
                elif os.path.isdir(archivo):
                    self._agregar_directorio_zip(zipf, archivo)
    
    def _agregar_archivo_zip(self, zipf, archivo):
        file_size = os.path.getsize(archivo)
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(archivo)) as pbar:
            with open(archivo, 'rb') as f:
                zip_info = ZipInfo.from_file(archivo)
                zipf.writestr(zip_info, f.read(), compress_type=zipfile.ZIP_DEFLATED)
                pbar.update(file_size)
    
    def _agregar_directorio_zip(self, zipf, directorio):
        for root, dirs, files in os.walk(directorio):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(directorio))
                file_size = os.path.getsize(file_path)
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=file) as pbar:
                    with open(file_path, 'rb') as f:
                        zip_info = ZipInfo.from_file(file_path, arcname)
                        zipf.writestr(zip_info, f.read(), compress_type=zipfile.ZIP_DEFLATED)
                        pbar.update(file_size)
    
    def _comprimir_7z(self, archivos, destino, password=None):
        filters = [{'id': py7zr.FILTER_LZMA2, 'preset': self.nivel_compresion}]
        with py7zr.SevenZipFile(destino, 'w', filters=filters, password=password) as archive:
            for archivo in archivos:
                if os.path.isfile(archivo):
                    archive.write(archivo, os.path.basename(archivo))
                elif os.path.isdir(archivo):
                    archive.writeall(archivo, os.path.basename(archivo))
    
    def _comprimir_gzip(self, archivos, destino, password=None):
        if len(archivos) > 1:
            raise ValueError("GZIP solo soporta un archivo a la vez")
        with open(archivos[0], 'rb') as f_in:
            with gzip.open(destino, 'wb', compresslevel=self.nivel_compresion) as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _comprimir_bz2(self, archivos, destino, password=None):
        if len(archivos) > 1:
            raise ValueError("BZIP2 solo soporta un archivo a la vez")
        with open(archivos[0], 'rb') as f_in:
            with bz2.open(destino, 'wb', compresslevel=self.nivel_compresion) as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _comprimir_lzma(self, archivos, destino, password=None):
        if len(archivos) > 1:
            raise ValueError("LZMA solo soporta un archivo a la vez")
        with open(archivos[0], 'rb') as f_in:
            with lzma.open(destino, 'wb', preset=self.nivel_compresion) as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def descomprimir(self, archivo_comprimido, destino=None, password=None):
        if not os.path.isfile(archivo_comprimido):
            raise FileNotFoundError(f"Archivo no encontrado: {archivo_comprimido}")
        
        destino = destino or os.path.dirname(archivo_comprimido)
        os.makedirs(destino, exist_ok=True)
        
        extension = os.path.splitext(archivo_comprimido)[1][1:].lower()
        
        if extension == 'zip':
            self._descomprimir_zip(archivo_comprimido, destino, password)
        elif extension == '7z':
            self._descomprimir_7z(archivo_comprimido, destino, password)
        elif extension == 'gz':
            self._descomprimir_gzip(archivo_comprimido, destino)
        elif extension == 'bz2':
            self._descomprimir_bz2(archivo_comprimido, destino)
        elif extension == 'xz':
            self._descomprimir_lzma(archivo_comprimido, destino)
        else:
            raise ValueError(f"Formato no soportado: {extension}")
    
    def _descomprimir_zip(self, archivo, destino, password=None):
        with zipfile.ZipFile(archivo, 'r') as zipf:
            if password:
                zipf.setpassword(password.encode('utf-8'))
            for file in tqdm(zipf.namelist(), desc="Descomprimiendo"):
                zipf.extract(file, destino)
    
    def _descomprimir_7z(self, archivo, destino, password=None):
        with py7zr.SevenZipFile(archivo, 'r', password=password) as archive:
            archive.extractall(path=destino)
    
    def _descomprimir_gzip(self, archivo, destino):
        nombre_base = os.path.basename(archivo).replace('.gz', '')
        ruta_salida = os.path.join(destino, nombre_base)
        with gzip.open(archivo, 'rb') as f_in:
            with open(ruta_salida, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _descomprimir_bz2(self, archivo, destino):
        nombre_base = os.path.basename(archivo).replace('.bz2', '')
        ruta_salida = os.path.join(destino, nombre_base)
        with bz2.open(archivo, 'rb') as f_in:
            with open(ruta_salida, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _descomprimir_lzma(self, archivo, destino):
        nombre_base = os.path.basename(archivo).replace('.xz', '')
        ruta_salida = os.path.join(destino, nombre_base)
        with lzma.open(archivo, 'rb') as f_in:
            with open(ruta_salida, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

class CompresorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Compresor/Descompresor Avanzado")
        self.root.geometry("800x600")
        
        self.compresor = CompresorAvanzado()
        self.archivos_a_comprimir = []
        self.destino = ""
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de compresión
        self.comp_frame = ttk.Frame(self.notebook)
        self.crear_interfaz_compresion()
        self.notebook.add(self.comp_frame, text="Comprimir")
        
        # Pestaña de descompresión
        self.desc_frame = ttk.Frame(self.notebook)
        self.crear_interfaz_descompresion()
        self.notebook.add(self.desc_frame, text="Descomprimir")
    
    def crear_interfaz_compresion(self):
        ttk.Label(self.comp_frame, text="Archivos a comprimir:").grid(row=0, column=0, sticky=tk.W)
        
        self.lista_archivos = tk.Listbox(self.comp_frame, height=6, selectmode=tk.EXTENDED)
        self.lista_archivos.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Button(self.comp_frame, text="Agregar archivos", command=self.agregar_archivos).grid(row=2, column=0, pady=5)
        ttk.Button(self.comp_frame, text="Agregar directorio", command=self.agregar_directorio).grid(row=2, column=1, pady=5)
        ttk.Button(self.comp_frame, text="Eliminar selección", command=self.eliminar_seleccion).grid(row=2, column=2, pady=5)
        
        ttk.Label(self.comp_frame, text="Directorio de destino:").grid(row=3, column=0, sticky=tk.W, pady=(15,0))
        self.entry_destino = ttk.Entry(self.comp_frame, width=50)
        self.entry_destino.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Button(self.comp_frame, text="Explorar", command=self.seleccionar_destino).grid(row=4, column=2, pady=5)
        
        options_frame = ttk.LabelFrame(self.comp_frame, text="Opciones de compresión", padding=10)
        options_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(15,0))
        
        ttk.Label(options_frame, text="Nombre del archivo:").grid(row=0, column=0, sticky=tk.W)
        self.entry_nombre = ttk.Entry(options_frame)
        self.entry_nombre.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(options_frame, text="Formato:").grid(row=1, column=0, sticky=tk.W)
        self.formato_var = tk.StringVar(value="zip")
        formatos = ["zip", "7z", "gz", "bz2", "xz"]
        ttk.OptionMenu(options_frame, self.formato_var, "zip", *formatos).grid(row=1, column=1, sticky="ew", padx=5)
        
        ttk.Label(options_frame, text="Nivel de compresión (0-9):").grid(row=2, column=0, sticky=tk.W)
        self.nivel_var = tk.StringVar(value="6")
        ttk.Spinbox(options_frame, from_=0, to=9, textvariable=self.nivel_var, width=5).grid(row=2, column=1, sticky="w", padx=5)
        
        self.encriptar_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Encriptar archivo", variable=self.encriptar_var, 
                       command=self.toggle_password).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5,0))
        
        self.entry_password = ttk.Entry(options_frame, show="*", state=tk.DISABLED)
        self.entry_password.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.progress = ttk.Progressbar(self.comp_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(20,5))
        self.lbl_progress = ttk.Label(self.comp_frame, text="Listo")
        self.lbl_progress.grid(row=7, column=0, columnspan=3)
        
        ttk.Button(self.comp_frame, text="Comprimir archivos", command=self.iniciar_compresion).grid(row=8, column=0, columnspan=3, pady=(20,0))
    
    def crear_interfaz_descompresion(self):
        ttk.Label(self.desc_frame, text="Archivo comprimido:").pack(pady=5)
        self.entry_archivo_comprimido = ttk.Entry(self.desc_frame, width=50)
        self.entry_archivo_comprimido.pack(pady=5)
        ttk.Button(self.desc_frame, text="Seleccionar archivo", 
                  command=self.seleccionar_archivo_comprimido).pack(pady=5)
        
        ttk.Label(self.desc_frame, text="Directorio de destino:").pack(pady=5)
        self.entry_destino_desc = ttk.Entry(self.desc_frame, width=50)
        self.entry_destino_desc.pack(pady=5)
        ttk.Button(self.desc_frame, text="Seleccionar destino", 
                  command=self.seleccionar_destino_descompresion).pack(pady=5)
        
        ttk.Label(self.desc_frame, text="Contraseña (si está encriptado):").pack(pady=5)
        self.entry_password_desc = ttk.Entry(self.desc_frame, show="*")
        self.entry_password_desc.pack(pady=5)
        
        self.progress_desc = ttk.Progressbar(self.desc_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_desc.pack(pady=10, fill=tk.X)
        self.lbl_progress_desc = ttk.Label(self.desc_frame, text="Listo")
        self.lbl_progress_desc.pack()
        
        ttk.Button(self.desc_frame, text="Descomprimir", 
                  command=self.iniciar_descompresion).pack(pady=20)
    
    def toggle_password(self):
        if self.encriptar_var.get():
            self.entry_password.config(state=tk.NORMAL)
        else:
            self.entry_password.config(state=tk.DISABLED)
    
    def agregar_archivos(self):
        archivos = filedialog.askopenfilenames(title="Seleccionar archivos a comprimir")
        if archivos:
            for archivo in archivos:
                if archivo not in self.archivos_a_comprimir:
                    self.archivos_a_comprimir.append(archivo)
            self.actualizar_lista()
    
    def agregar_directorio(self):
        directorio = filedialog.askdirectory(title="Seleccionar directorio a comprimir")
        if directorio and directorio not in self.archivos_a_comprimir:
            self.archivos_a_comprimir.append(directorio)
            self.actualizar_lista()
    
    def eliminar_seleccion(self):
        seleccionados = self.lista_archivos.curselection()
        for index in reversed(seleccionados):
            del self.archivos_a_comprimir[index]
        self.actualizar_lista()
    
    def seleccionar_destino(self):
        directorio = filedialog.askdirectory(title="Seleccionar directorio de destino")
        if directorio:
            self.destino = directorio
            self.entry_destino.delete(0, tk.END)
            self.entry_destino.insert(0, directorio)
    
    def actualizar_lista(self):
        self.lista_archivos.delete(0, tk.END)
        for archivo in self.archivos_a_comprimir:
            self.lista_archivos.insert(tk.END, archivo)
    
    def iniciar_compresion(self):
        if not self.archivos_a_comprimir:
            messagebox.showerror("Error", "No hay archivos seleccionados para comprimir")
            return
        
        if not self.entry_destino.get():
            messagebox.showerror("Error", "No se ha seleccionado un directorio de destino")
            return
        
        nombre = self.entry_nombre.get() or f"comprimido_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        formato = self.formato_var.get()
        nivel = int(self.nivel_var.get())
        password = self.entry_password.get() if self.encriptar_var.get() else None
        
        self.compresor.establecer_nivel_compresion(nivel)
        self.habilitar_controles(False)
        self.lbl_progress.config(text="Comprimiendo...")
        self.progress["value"] = 0
        
        threading.Thread(
            target=self.ejecutar_compresion,
            args=(nombre, formato, password),
            daemon=True
        ).start()
    
    def ejecutar_compresion(self, nombre, formato, password):
        try:
            resultado = self.compresor.comprimir(
                archivos=self.archivos_a_comprimir,
                destino=self.entry_destino.get(),
                formato=formato,
                nombre=nombre,
                password=password
            )
            
            def mostrar_exito():
                self.lbl_progress.config(text=f"¡Compresión completada! Archivo creado en: {resultado}")
                messagebox.showinfo("Éxito", f"Archivo comprimido creado:\n{resultado}")
                self.habilitar_controles(True)
                self.progress["value"] = 100
            
            self.root.after(0, mostrar_exito)
        
        except Exception as ex:
            error_msg = str(ex)
            
            def mostrar_error():
                self.lbl_progress.config(text=f"Error: {error_msg}")
                messagebox.showerror("Error", f"Ocurrió un error durante la compresión:\n{error_msg}")
                self.habilitar_controles(True)
                self.progress["value"] = 100
            
            self.root.after(0, mostrar_error)
    
    def habilitar_controles(self, habilitar):
        state = tk.NORMAL if habilitar else tk.DISABLED
        
        # Widgets que soportan state
        widgets = [
            self.lista_archivos,
            self.entry_destino,
            self.entry_nombre,
            self.entry_password
        ]
        
        for widget in widgets:
            widget.config(state=state)
        
        # Manejo especial para password
        if not habilitar or self.encriptar_var.get():
            self.entry_password.config(state=state)
        
        # Actualizar variables de control
        self.formato_var.set(self.formato_var.get())
        self.nivel_var.set(self.nivel_var.get())
        self.encriptar_var.set(self.encriptar_var.get())
    
    def seleccionar_archivo_comprimido(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo comprimido",
            filetypes=[
                ("Archivos comprimidos", "*.zip *.7z *.gz *.bz2 *.xz"),
                ("Todos los archivos", "*.*")
            ])
        if archivo:
            self.entry_archivo_comprimido.delete(0, tk.END)
            self.entry_archivo_comprimido.insert(0, archivo)
    
    def seleccionar_destino_descompresion(self):
        directorio = filedialog.askdirectory(title="Seleccionar directorio de destino")
        if directorio:
            self.entry_destino_desc.delete(0, tk.END)
            self.entry_destino_desc.insert(0, directorio)
    
    def iniciar_descompresion(self):
        archivo = self.entry_archivo_comprimido.get()
        destino = self.entry_destino_desc.get() or os.path.dirname(archivo)
        password = self.entry_password_desc.get() or None
        
        if not archivo:
            messagebox.showerror("Error", "No se ha seleccionado un archivo comprimido")
            return
        
        self.habilitar_controles_descompresion(False)
        self.lbl_progress_desc.config(text="Descomprimiendo...")
        self.progress_desc["value"] = 0
        
        threading.Thread(
            target=self.ejecutar_descompresion,
            args=(archivo, destino, password),
            daemon=True
        ).start()
    
    def ejecutar_descompresion(self, archivo, destino, password):
        try:
            self.compresor.descomprimir(archivo, destino, password)
            
            def mostrar_exito():
                self.lbl_progress_desc.config(text=f"¡Descompresión completada! Archivos en: {destino}")
                messagebox.showinfo("Éxito", f"Archivos descomprimidos en:\n{destino}")
                self.habilitar_controles_descompresion(True)
                self.progress_desc["value"] = 100
            
            self.root.after(0, mostrar_exito)
        
        except Exception as ex:
            error_msg = str(ex)
            
            def mostrar_error():
                self.lbl_progress_desc.config(text=f"Error: {error_msg}")
                messagebox.showerror("Error", f"Ocurrió un error:\n{error_msg}")
                self.habilitar_controles_descompresion(True)
                self.progress_desc["value"] = 100
            
            self.root.after(0, mostrar_error)
    
    def habilitar_controles_descompresion(self, habilitar):
        state = tk.NORMAL if habilitar else tk.DISABLED
        self.entry_archivo_comprimido.config(state=state)
        self.entry_destino_desc.config(state=state)
        self.entry_password_desc.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = CompresorApp(root)
    root.mainloop()
