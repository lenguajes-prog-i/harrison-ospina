import socket
import threading

# ---------------------------------------------
#  SALAS PREDEFINIDAS
# ---------------------------------------------
CONFIG_SALAS = {
    "general": 5555,
    "tech":    5556,
    "random":  5557,
}

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

    def transmitir(self, mensaje, emisor=None):
        with self.bloqueo:
            destinatarios = list(self.clientes)
        for cliente in destinatarios:
            if cliente != emisor:
                cliente.enviar(mensaje)

    def iniciar(self):
        hilo = threading.Thread(target=self._escuchar, daemon=True)
        hilo.start()

    def _escuchar(self):
        socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_servidor.bind(("", self.puerto))
        socket_servidor.listen()
        print(f"[INFO] Sala '{self.nombre}' escuchando en puerto {self.puerto}")

        while True:
            conexion, direccion = socket_servidor.accept()
            manejador = ManejadorCliente(conexion, direccion, self)
            self.agregar_cliente(manejador)
            manejador.start()

class ManejadorCliente(threading.Thread):
    def __init__(self, conexion, direccion, sala):
        super().__init__(daemon=True)
        self.conexion = conexion
        self.direccion = direccion
        self.sala = sala
        self.nickname = ""

    def enviar(self, mensaje):
        try:
            self.conexion.send((mensaje + "\n").encode("utf-8"))
        except:
            self.desconectar()

    def run(self):
        try:
            self.enviar("__ASK_NICKNAME__")
            self.nickname = self.conexion.recv(1024).decode("utf-8").strip()

            self.enviar(f"Bienvenido {self.nickname}! Estás en la sala '{self.sala.nombre}'.")
            self.enviar("__READY__")
            self.sala.transmitir(f"[+] {self.nickname} se unió a la sala", emisor=self)
            print(f"[+] {self.nickname} se unió a sala '{self.sala.nombre}'")

            while True:
                datos = self.conexion.recv(1024).decode("utf-8").strip()
                if not datos:
                    break
                self.manejar_comando(datos)
        except:
            pass
        finally:
            self.desconectar()

    def manejar_comando(self, datos):
        if datos.startswith("/msg "):
            mensaje = datos.split(" ", 1)[1].strip()
            self.enviar_mensaje(mensaje)

        elif datos in ("/leave", "/quit"):
            self.desconectar()

        elif datos == "/rooms":
            info = "\n".join([f"  - {nombre}: puerto {puerto}" for nombre, puerto in CONFIG_SALAS.items()])
            self.enviar(f"Salas disponibles:\n{info}")
            
        elif not datos.startswith("/"):
            # Si no empieza con /, se envía como mensaje normal
            self.enviar_mensaje(datos)

        else:
            self.enviar("Comandos: /msg <texto>, /rooms, /leave, /quit")

    def enviar_mensaje(self, mensaje):
        mensaje_completo = f"[{self.nickname}] {mensaje}"
        self.sala.transmitir(mensaje_completo, emisor=self)
        # Log del servidor detallando origen y destino
        print(f"[{self.nickname}] -> [SALA: {self.sala.nombre}]: {mensaje}")

    def desconectar(self):
        self.sala.transmitir(f"[-] {self.nickname} salió de la sala", emisor=self)
        self.sala.remover_cliente(self)
        try:
            self.conexion.close()
        except:
            pass

if __name__ == "__main__":
    print("=== SERVIDOR DE CHAT ===")
    for nombre, puerto in CONFIG_SALAS.items():
        sala = Sala(nombre, puerto)
        sala.init_hilo = sala.iniciar()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\n[INFO] Servidor detenido.")