import socket
import threading
import time
import pickle 


# Salas iniciales (el cliente las actualizará al conectarse)
CONFIG_SALAS_INICIALES = {
    "general": 5555,
    "tech":    5556,
    "random":  5557,
}

class SesionUsuario:
    def __init__(self, nickname, host):
        self.nickname = nickname
        self.host = host
        self.socket = None
        self.sala_actual = None
        self.conectado = False
        self.listo = threading.Event()
        self.mensajes = []
        
    def agregar_mensaje(self, mensaje):
        self.mensajes.append(mensaje)
        if len(self.mensajes) > 50: self.mensajes.pop(0)

class ClienteMultiusuario:
    def __init__(self, host):
        self.host = host
        self.usuarios = {} # nickname -> SesionUsuario
        self.usuario_activo = None
        self.ejecutando = True
        self.salas = dict(CONFIG_SALAS_INICIALES)
        
    def crear_usuario(self, nickname):
        if nickname in self.usuarios:
            print(f"[ERROR] El usuario '{nickname}' ya existe.")
            return
        self.usuarios[nickname] = SesionUsuario(nickname, self.host)
        print(f"[OK] Usuario '{nickname}' creado.")

    def listar_usuarios(self):
        if not self.usuarios:
            print("\nNo hay usuarios creados.")
            return
        print("\n--- USUARIOS ---")
        for nick, sesion in self.usuarios.items():
            estado = f"Conectado a {sesion.sala_actual}" if sesion.conectado else "Desconectado"
            marca = "[*]" if nick == self.usuario_activo else "   "
            print(f"{marca} {nick}: {estado}") # Imprime el nickname y su estado (conectado/desconectado)

    def conectar_a_sala(self, nickname, sala):
        if nickname not in self.usuarios: return False
        if sala not in self.salas: return False
        
        sesion = self.usuarios[nickname] 
        if sesion.conectado: 
            if sesion.sala_actual == sala: return True   
            # Desconectar de la anterior si cambia
            self.desconectar_sesion(sesion)

        sesion.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sesion.socket.connect((self.host, self.salas[sala]))
            sesion.sala_actual = sala
            sesion.conectado = True
            sesion.listo.clear()
            
            threading.Thread(target=self.recibir_mensajes, args=(sesion,), daemon=True).start()
            return True
        except Exception as e:
            print(f"[ERROR] No se pudo conectar: {e}")
            return False

    def recibir_mensajes(self, sesion):
        buffer_texto = ""
        # Estado para recibir un bloque pickle pendiente
        esperando_pickle = False
        bytes_pickle_pendientes = b""
        longitud_pickle = 0

        while self.ejecutando and sesion.conectado:
            try:
                datos = sesion.socket.recv(4096)
                if not datos:
                    break

                # Si estamos en medio de recibir un bloque pickle binario
                if esperando_pickle:
                    bytes_pickle_pendientes += datos
                    if len(bytes_pickle_pendientes) >= longitud_pickle:
                        bloque = bytes_pickle_pendientes[:longitud_pickle]
                        # Descartar lo que sobra (no debería haber nada en este protocolo)
                        bytes_pickle_pendientes = bytes_pickle_pendientes[longitud_pickle:]
                        esperando_pickle = False
                        longitud_pickle = 0
                        try:
                            paquete = pickle.loads(bloque)
                            if paquete.get("bandera") == "__PRIVATE__":
                                linea = f"[PRIVADO de {paquete['de']}]: {paquete['mensaje']}"
                                sesion.agregar_mensaje(linea)
                                if sesion.nickname == self.usuario_activo:
                                    print(f"\r{linea}\n[{sesion.nickname}@{sesion.sala_actual}]> ", end="", flush=True)
                        except Exception as e:
                            print(f"[ERROR] No se pudo deserializar el mensaje privado: {e}")
                    continue

                # Intentar decodificar como texto normal
                try:
                    buffer_texto += datos.decode("utf-8")
                except UnicodeDecodeError:
                    continue

                while "\n" in buffer_texto:
                    linea, buffer_texto = buffer_texto.split("\n", 1)
                    linea = linea.rstrip()

                    if linea == "__ASK_NICKNAME__":
                        sesion.socket.send((sesion.nickname + "\n").encode("utf-8"))
                    elif linea == "__READY__":
                        sesion.listo.set()
                    elif linea == "__LEAVE__" or linea == "__QUIT__":
                        sesion.conectado = False
                        break
                    elif linea == "__PKL__":
                        # El siguiente recv será binario: 4 bytes de longitud + datos pickle
                        raw = b""
                        while len(raw) < 4:
                            chunk = sesion.socket.recv(4 - len(raw))
                            if not chunk:
                                break
                            raw += chunk
                        if len(raw) < 4:
                            break
                        longitud_pickle = int.from_bytes(raw, "big")
                        bytes_pickle_pendientes = b""
                        esperando_pickle = True
                        # Leer el bloque completo
                        while len(bytes_pickle_pendientes) < longitud_pickle:
                            chunk = sesion.socket.recv(longitud_pickle - len(bytes_pickle_pendientes))
                            if not chunk:
                                break
                            bytes_pickle_pendientes += chunk
                        if len(bytes_pickle_pendientes) >= longitud_pickle:
                            bloque = bytes_pickle_pendientes[:longitud_pickle]
                            esperando_pickle = False
                            bytes_pickle_pendientes = b""
                            longitud_pickle = 0
                            try:
                                paquete = pickle.loads(bloque)
                                if paquete.get("bandera") == "__PRIVATE__":
                                    linea_priv = f"[PRIVADO de {paquete['de']}]: {paquete['mensaje']}"
                                    sesion.agregar_mensaje(linea_priv)
                                    if sesion.nickname == self.usuario_activo:
                                        print(f"\r{linea_priv}\n[{sesion.nickname}@{sesion.sala_actual}]> ", end="", flush=True)
                            except Exception as e:
                                print(f"[ERROR] No se pudo deserializar el mensaje privado: {e}")
                    elif linea.startswith("__UPDATE_ROOMS__"):
                        try:
                            data = linea.split(" ", 1)[1]
                            nuevas_salas = {}
                            for item in data.split(","):
                                n, p = item.split(":") 
                                nuevas_salas[n] = int(p)
                            self.salas = nuevas_salas
                        except: pass
                    else:
                        sesion.agregar_mensaje(linea)
                        if sesion.nickname == self.usuario_activo:
                            print(f"\r{linea}\n[{sesion.nickname}@{sesion.sala_actual}]> ", end="", flush=True)
            except:
                break
        sesion.conectado = False

    def desconectar_sesion(self, sesion):
        if sesion.socket and sesion.conectado:
            try:
                sesion.socket.send("/leave\n".encode("utf-8"))
                time.sleep(0.1)
                sesion.socket.close()
            except: pass
        sesion.conectado = False

    def modo_chat(self, nickname):
        sesion = self.usuarios[nickname]
        if not sesion.conectado:
            print("Selecciona una sala:")
            for s in self.salas: print(f" - {s}")
            sala = input("Sala: ").strip().lower()
            if not self.conectar_a_sala(nickname, sala): return
            sesion.listo.wait(timeout=5)

        self.usuario_activo = nickname
        print(f"\n--- Chat: {nickname} en {sesion.sala_actual} ---")
        for m in sesion.mensajes[-10:]: print(m)
        
        while sesion.conectado:
            try:
                msg = input(f"[{nickname}@{sesion.sala_actual}]> ").strip()
                if not msg: continue
                
                msg_lower = msg.lower()
                if msg_lower == "/leave":
                    try: sesion.socket.send("/leave\n".encode("utf-8"))
                    except: pass
                    sesion.conectado = False
                    sesion.socket.close()
                    print(f"[INFO] Saliste de la sala {sesion.sala_actual}.")
                    break
                elif msg_lower.startswith("/mensaje_privado "):
                    sesion.socket.send((msg + "\n").encode("utf-8"))
                elif msg_lower == "/quit":
                    try: sesion.socket.send("/quit\n".encode("utf-8"))
                    except: pass
                    sesion.conectado = False
                    sesion.socket.close()
                    self.ejecutando = False
                    break
                elif msg_lower == "/rooms":
                    sesion.socket.send("/rooms\n".encode("utf-8"))
                elif msg_lower.startswith("/make "):
                    sesion.socket.send((msg + "\n").encode("utf-8"))
                elif msg_lower == "/back":
                    print("[INFO] Volviendo al menú principal (sigues conectado).")
                    break
                elif msg_lower == "/help":
                    sesion.socket.send("/help\n".encode("utf-8"))
                else:
                    sesion.socket.send((msg + "\n").encode("utf-8"))
            except KeyboardInterrupt:
                print("\n[INFO] Volviendo al menú...")
                break
            except Exception as e:
                print(f"\n[ERROR] Conexión perdida: {e}")
                sesion.conectado = False
                break
        self.usuario_activo = None

    def menu(self):
        while self.ejecutando:
            print("\n--- MENÚ PRINCIPAL ---")
            print(" crear   - Crear nuevo usuario")
            print(" listar  - Ver usuarios y estados")
            print(" entrar  - Entrar a una sala / Cambiar usuario")
            print(" salir   - Cerrar programa")
            
            cmd = input("\n> ").strip().lower()
            if cmd == "crear":
                nick = input("Nickname: ").strip()
                if nick: self.crear_usuario(nick)
            elif cmd == "listar":
                self.listar_usuarios()
            elif cmd == "entrar":
                if not self.usuarios:
                    print("Crea un usuario primero.")
                    continue
                self.listar_usuarios()
                nick = input("Quién eres (nickname): ").strip()
                if nick in self.usuarios: self.modo_chat(nick)
                else: print("Usuario no encontrado.")
            elif cmd == "salir":
                for sesion in self.usuarios.values():
                    if sesion.conectado:
                        try:
                            sesion.socket.send("/leave\n".encode("utf-8"))
                            sesion.socket.close()
                        except: pass
                self.ejecutando = False
            elif cmd == "help":
                print("\n--- COMANDOS DEL MENÚ ---")
                print(" crear   - Crear un nuevo perfil local.")
                print(" listar  - Ver tus perfiles y si están conectados.")
                print(" entrar  - Elegir un perfil y entrar/cambiar a una sala.")
                print(" salir   - Cerrar el programa.")

if __name__ == "__main__":
    host = input("IP Servidor (Enter para localhost): ").strip() or "127.0.0.1"
    ClienteMultiusuario(host).menu()