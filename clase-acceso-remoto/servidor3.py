import socket
import threading
from datetime import datetime
import pickle 

# Configuración de salas y puertos
# Configuración inicial de salas
CONFIG_SALAS = {
    "general": 5555,
    "tech":    5556,
    "random":  5557,
}

SALAS_INSTANCIAS = {} # nombre -> Sala
BLOQUEO_GLOBAL_SALAS = threading.Lock()

class Sala:
    def __init__(self, nombre, puerto):
        self.nombre = nombre
        self.puerto = puerto
        self.clientes = []
        self.bloqueo = threading.Lock()

    def agregar_cliente(self, cliente):
        with self.bloqueo:
            self.clientes.append(cliente)

    def remover_cliente(self, cliente):
        with self.bloqueo:
            if cliente in self.clientes:
                self.clientes.remove(cliente)
                print(f"[{self.nombre.upper()}] {cliente.nickname} ha salido.")

    def transmitir(self, mensaje, emisor=None):
        with self.bloqueo:
            destinatarios = list(self.clientes)
        
        for cliente in destinatarios:
            if cliente != emisor:
                cliente.enviar(mensaje)

    def transmitir_sistema(self, mensaje):
        with self.bloqueo:
            destinatarios = list(self.clientes)
        for cliente in destinatarios:
            cliente.enviar(mensaje)

    def obtener_lista_usuarios(self):
        with self.bloqueo:
            return [cliente.nickname for cliente in self.clientes]

    def iniciar(self):
        hilo = threading.Thread(target=self._escuchar, daemon=True)
        hilo.start()

    def _escuchar(self):
        socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_servidor.bind(("", self.puerto))
        socket_servidor.listen(10)
        print(f"[INFO] Sala '{self.nombre}' lista en puerto {self.puerto}")

        while True:
            try:
                conexion, direccion = socket_servidor.accept()
                manejador = ManejadorCliente(conexion, direccion, self)
                self.agregar_cliente(manejador)
                manejador.start()
            except Exception as e:
                print(f"[ERROR] Error en '{self.nombre}': {e}")

    def _timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

class ManejadorCliente(threading.Thread):
    def __init__(self, conexion, direccion, sala):
        super().__init__(daemon=True)
        self.conexion = conexion
        self.direccion = direccion
        self.sala = sala
        self.nickname = ""
        self.bloqueo_envio = threading.Lock()

    def enviar(self, mensaje):
        with self.bloqueo_envio:
            try:
                self.conexion.send((mensaje + "\n").encode("utf-8"))
            except:
                self.desconectar()

    # Serializa el mensaje privado con pickle y lo envía precedido de la bandera __PKL__
    def enviar_privado(self, destinatario_cliente, texto):
        datos = pickle.dumps({"bandera": "__PRIVATE__", "de": self.nickname, "mensaje": texto})
        longitud = len(datos).to_bytes(4, "big")
        with destinatario_cliente.bloqueo_envio:
            try:
                destinatario_cliente.conexion.send(b"__PKL__\n")
                destinatario_cliente.conexion.send(longitud + datos)
            except:
                destinatario_cliente.desconectar()

    def run(self):
        try:
            self.enviar("__ASK_NICKNAME__")
            datos_nick = self.conexion.recv(1024).decode("utf-8").strip()
            
            if not datos_nick:
                self.desconectar()
                return
            
            self.nickname = datos_nick
            print(f"[{self.sala.nombre.upper()}] {self.nickname} se ha unido.")
            self.enviar(f"*** Bienvenido a la sala {self.sala.nombre.upper()}, {self.nickname}! ***")
            self.enviar("__READY__")
            self.mostrar_ayuda()
            self.enviar_actualizacion_salas() # Sincronizar salas con el nuevo usuario
            self.sala.transmitir(f"[SISTEMA] {self.nickname} se ha unido a la conversación.", emisor=self)

            buffer = ""
            while True:
                datos = self.conexion.recv(1024).decode("utf-8")
                if not datos: break
                buffer += datos
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip(): self.procesar_entrada(linea.strip())

        except (ConnectionResetError, BrokenPipeError):
            pass 
        except Exception as e:
            # Silenciar error de socket ya cerrado (común en Windows al desconectar)
            if "10038" not in str(e):
                print(f"[ERROR] Cliente {self.nickname}: {e}")
        finally:
            self.desconectar()

    def procesar_entrada(self, entrada):
        cmd_lower = entrada.lower() 
        if cmd_lower.startswith("/nick "): self.cambiar_nickname(entrada)
        elif cmd_lower == "/pm": self.enviar("[ERROR] Uso: /pm <nickname> <mensaje>")

        elif cmd_lower.startswith("/mensaje_privado "):
            partes = entrada.split(" ", 2)
            if len(partes) < 3:
                self.enviar("[ERROR] Uso: /mensaje_privado <nickname> <mensaje>")
            else:
                nick_destino = partes[1]
                texto_privado = partes[2]
                encontrado = False
                with BLOQUEO_GLOBAL_SALAS:
                    salas_copia = list(SALAS_INSTANCIAS.values())
                for sala in salas_copia:
                    with sala.bloqueo:
                        clientes_sala = list(sala.clientes)
                    for cliente in clientes_sala:
                        if cliente.nickname.lower() == nick_destino.lower():
                            self.enviar_privado(cliente, texto_privado)
                            self.enviar(f"[PRIVADO para {cliente.nickname}]: {texto_privado}")
                            encontrado = True
                            break
                    if encontrado:
                        break
                if not encontrado:
                    self.enviar(f"[ERROR] Usuario '{nick_destino}' no encontrado.")

        elif cmd_lower.startswith("/make "):
            nombre_sala = entrada.split(" ", 1)[1].strip().lower()
            if crear_nueva_sala(nombre_sala):
                self.sala.transmitir(f"[SISTEMA] {self.nickname} ha creado una nueva sala: '{nombre_sala}'")
                self.enviar(f"[OK] Sala '{nombre_sala}' creada exitosamente.")
                self.enviar_actualizacion_salas()
            else:
                self.enviar("[ERROR] No se pudo crear la sala (ya existe o límite alcanzado).")
        elif cmd_lower == "/rooms": self.mostrar_salas()
        elif cmd_lower == "/leave": 
            self.enviar("__LEAVE__")
            self.desconectar()
        elif cmd_lower == "/quit":
            self.enviar("__QUIT__")
            self.desconectar()
        elif cmd_lower == "/help": self.mostrar_ayuda()
        elif cmd_lower == "/users": self.mostrar_usuarios()
        else: self.enviar_mensaje(entrada)

    def cambiar_nickname(self, comando):
        try:
            nuevo_nick = comando.split(" ", 1)[1].strip()
            if not nuevo_nick: return
            nick_anterior = self.nickname
            self.nickname = nuevo_nick
            self.enviar(f"[OK] Ahora eres: {nuevo_nick}")
            self.sala.transmitir(f"[SISTEMA] {nick_anterior} ahora es {nuevo_nick}", emisor=self)
        except: pass

    def mostrar_salas(self):
        info = ["", "--- SALAS DISPONIBLES ---"]
        for nombre, puerto in CONFIG_SALAS.items():
            info.append(f"  - {nombre} (puerto {puerto})")
        self.enviar("\n".join(info))

    def mostrar_ayuda(self):
        ayuda = [
            "", "--- COMANDOS DISPONIBLES (VERSION NUEVA) ---",
            "  /nick <nombre> : Cambia tu nombre en la sala actual.",
            "  /make <nombre> : Crea una nueva sala de chat.",
            "  /users         : Lista los usuarios conectados a esta sala.",
            "  /mensaje_privado <destinatario> <mensaje> : Envia un mensaje privado a un usuario.",
            "  /rooms         : Muestra todas las salas disponibles y sus puertos.",
            "  /back          : Vuelve al menú principal sin desconectarte.",
            "  /leave         : Sale de la sala actual y cierra la conexión.",
            "  /quit          : Cierra completamente el programa de chat.",
            "  /help          : Muestra este mensaje de ayuda.",
            "",
            "  * También puedes usar Ctrl+C para volver al menú sin desconectarte.",
            ""
        ]
        self.enviar("\n".join(ayuda))

    def enviar_actualizacion_salas(self):
        # Protocolo: __UPDATE_ROOMS__ nombre:puerto,nombre:puerto...
        with BLOQUEO_GLOBAL_SALAS:
            data = ",".join([f"{n}:{p}" for n, p in CONFIG_SALAS.items()])
        mensaje = f"__UPDATE_ROOMS__ {data}"
        
        # Transmitir a todos en todas las salas
        with BLOQUEO_GLOBAL_SALAS:
            for sala in SALAS_INSTANCIAS.values():
                sala.transmitir_sistema(mensaje)

    def mostrar_usuarios(self):
        usuarios = self.sala.obtener_lista_usuarios()
        info = ["", f"--- USUARIOS EN {self.sala.nombre.upper()} ({len(usuarios)}) ---"]
        for u in usuarios: info.append(f"  {'>' if u == self.nickname else ' '} {u}")
        self.enviar("\n".join(info))

    def enviar_mensaje(self, mensaje):
        self.sala.transmitir(f"{self.nickname}: {mensaje}", emisor=self)
        print(f"[{self.sala.nombre.upper()}] {self.nickname}: {mensaje}")

    def desconectar(self):
        if self.nickname:
            self.sala.transmitir(f"[SISTEMA] {self.nickname} se ha desconectado", emisor=self)
        self.sala.remover_cliente(self)
        try: self.conexion.close()
        except: pass

def buscar_puerto_libre():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto

def crear_nueva_sala(nombre):
    nombre = nombre.lower()
    with BLOQUEO_GLOBAL_SALAS:
        if nombre in CONFIG_SALAS: return False
        if len(CONFIG_SALAS) >= 10: return False
        
        puerto = buscar_puerto_libre()
        CONFIG_SALAS[nombre] = puerto
        nueva_sala = Sala(nombre, puerto)
        SALAS_INSTANCIAS[nombre] = nueva_sala
        nueva_sala.iniciar()
        print(f"[SISTEMA][NUEVA SALA] Se ha creado '{nombre}' en el puerto {puerto}")
        return True

if __name__ == "__main__":
    print("Iniciando Servidor de Chat...")
    for nombre, puerto in CONFIG_SALAS.items():
        sala = Sala(nombre, puerto)
        SALAS_INSTANCIAS[nombre] = sala
        sala.iniciar()
    print("[OK] Servidor listo. Presiona Ctrl+C para salir.")
    try: threading.Event().wait()
    except KeyboardInterrupt: print("\nServidor detenido.")