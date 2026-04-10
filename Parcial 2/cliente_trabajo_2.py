import pickle
import socket
import threading
import time

# Clase para mensajes privados 
class MensajePrivado:
    def __init__(self, remitente, contenido):
        self.remitente = remitente
        self.contenido = contenido
    
    def __repr__(self):
        return f"Mensaje de {self.remitente}: {self.contenido}"


# Salas iniciales 
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
            print(f"{marca} {nick}: {estado}")

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
        lector = sesion.socket.makefile('rb') 
        while self.ejecutando and sesion.conectado:
            try:
                linea_bytes = lector.readline()
                if not linea_bytes: break
                
                
                linea_cruda = linea_bytes.strip()
                if not linea_cruda: continue

                # Si detectamos el objeto de mensaje privado, lo cargamos con pickle
                if linea_cruda == b"__INICIO_PM__":
                    try:
                        
                        obj_pm = pickle.load(lector)
                        
                        if isinstance(obj_pm, MensajePrivado):
                            msg_display = f"[PRIVADO de {obj_pm.remitente}]: {obj_pm.contenido}"
                            sesion.agregar_mensaje(msg_display)
                            if sesion.nickname == self.usuario_activo:
                                print(f"\r{msg_display}\n[{sesion.nickname}@{sesion.sala_actual}]> ", end="", flush=True)
                    except Exception as e:
                        print(f"\n[ERROR] Al decodificar PM: {e}")
                    continue

                # Procesar comandos internos o mensajes de texto normales
                linea = linea_cruda.decode("utf-8")

                if linea == "__ASK_NICKNAME__":
                    sesion.socket.send((sesion.nickname + "\n").encode("utf-8"))
                elif linea == "__READY__":
                    sesion.listo.set()
                elif linea == "__LEAVE__" or linea == "__QUIT__":
                    sesion.conectado = False
                    break
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
                    # Mensaje normal de la sala
                    sesion.agregar_mensaje(linea)
                    if sesion.nickname == self.usuario_activo:
                        print(f"\r{linea}\n[{sesion.nickname}@{sesion.sala_actual}]> ", end="", flush=True)
            except Exception as e:
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
                elif msg_lower.startswith("/pm "):
                    try:
                        partes = msg.split(" ", 2)
                        if len(partes) >= 3:
                            dest = partes[1]
                            contenido = partes[2]
                            
                            # Creamos el objeto (instancia de la clase)
                            obj_pm = MensajePrivado(dest, contenido) 
                            
                            # Enviamos el objeto con dump 
                            sesion.socket.sendall(b"__INICIO_PM__\n")
                            flujo = sesion.socket.makefile('wb')
                            pickle.dump(obj_pm, flujo)
                            flujo.flush() #flush es importante para asegurar que se envíe inmediatamente
                        else:
                            print("[SISTEMA] Uso: /pm <usuario> <mensaje>")
                    except Exception as e:
                        print(f"[ERROR] No se pudo enviar PM: {e}")
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
