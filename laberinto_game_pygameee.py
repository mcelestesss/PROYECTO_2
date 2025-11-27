import pygame
import random
import time
from collections import deque
import json
import os

# Inicialización de Pygame
pygame.init()

# Constantes
ANCHO_MAPA = 21
ALTO_MAPA = 21
TAMANO_CELDA = 30
ANCHO_VENTANA = ANCHO_MAPA * TAMANO_CELDA
ALTO_VENTANA = ALTO_MAPA * TAMANO_CELDA
FPS = 60

# Colores
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
VERDE_CAMINO = (46, 204, 113)      # #2ecc71
AZUL_MURO = (52, 73, 94)           # #34495e
MORADO_LIANA = (155, 89, 182)      # #9b59b6
AMARILLO_TUNEL = (241, 196, 15)    # #f1c40f
ROJO_JUGADOR = (231, 76, 60)       # #e74c3c
AZUL_ENEMIGO = (52, 152, 219)      # #3498db

# Clases de Casillas (se mantienen igual)
class Casilla:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def transitable_por_jugador(self): 
        return False
        
    def transitable_por_enemigo(self): 
        return False

class Camino(Casilla):
    def transitable_por_jugador(self): 
        return True
        
    def transitable_por_enemigo(self): 
        return True

class Muro(Casilla):
    def transitable_por_jugador(self): 
        return False
        
    def transitable_por_enemigo(self): 
        return False

class Liana(Casilla):
    def transitable_por_jugador(self): 
        return False
        
    def transitable_por_enemigo(self): 
        return True

class Tunel(Casilla):
    def transitable_por_jugador(self): 
        return True
        
    def transitable_por_enemigo(self): 
        return False

# Clase Mapa (se mantiene igual)
class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.matriz = [[1 for _ in range(ancho)] for _ in range(alto)]
        self.objetos = None

    def generar_laberinto(self):
        def dfs(x, y):
            direcciones = [(2, 0), (-2, 0), (0, 2), (0, -2)]
            random.shuffle(direcciones)
            for dx, dy in direcciones:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.alto - 1 and 1 <= ny < self.ancho - 1:
                    if self.matriz[nx][ny] == 1:
                        self.matriz[nx][ny] = 0
                        self.matriz[x + dx // 2][y + dy // 2] = 0
                        dfs(nx, ny)
                        
        self.matriz = [[1 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.matriz[1][1] = 0
        dfs(1, 1)
        self.matriz[self.alto - 2][self.ancho - 2] = 0
        self._agregar_elementos_especiales()

    def _agregar_elementos_especiales(self):
        for _ in range(self.ancho * self.alto // 20):
            x, y = random.randint(1, self.alto-2), random.randint(1, self.ancho-2)
            if self.matriz[x][y] == 0:
                if random.random() < 0.5:
                    self.matriz[x][y] = 2
                else:
                    self.matriz[x][y] = 3

    def existe_camino(self, inicio, fin):
        queue = deque([inicio])
        visitado = set([inicio])
        while queue:
            x, y = queue.popleft()
            if (x, y) == fin: 
                return True
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.alto and 0 <= ny < self.ancho:
                    if self.matriz[nx][ny] == 0 and (nx, ny) not in visitado:
                        visitado.add((nx, ny))
                        queue.append((nx, ny))
        return False

    def convertir_a_objetos(self):
        objetos = []
        for x in range(self.alto):
            fila = []
            for y in range(self.ancho):
                valor = self.matriz[x][y]
                if valor == 0: 
                    fila.append(Camino(x, y))
                elif valor == 1: 
                    fila.append(Muro(x, y))
                elif valor == 2: 
                    fila.append(Liana(x, y))
                elif valor == 3: 
                    fila.append(Tunel(x, y))
                else:
                    fila.append(Muro(x, y))
            objetos.append(fila)
        self.objetos = objetos
        return objetos

    def _es_transitable_numero(self, x, y, es_jugador=True):
        v = self.matriz[x][y]
        if v == 0:
            return True
        if v == 1:
            return False
        if v == 2:
            return not es_jugador
        if v == 3:
            return es_jugador
        return False

    def bfs_camino(self, inicio, fin, es_jugador=True):
        if inicio == fin:
            return [inicio]
        queue = deque([inicio])
        padres = {inicio: None}
        while queue:
            nodo = queue.popleft()
            if nodo == fin:
                path = []
                cur = fin
                while cur is not None:
                    path.append(cur)
                    cur = padres[cur]
                path.reverse()
                return path
            x, y = nodo
            for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.alto and 0 <= ny < self.ancho and (nx,ny) not in padres:
                    if self._es_transitable_numero(nx, ny, es_jugador):
                        padres[(nx,ny)] = nodo
                        queue.append((nx,ny))
        return None

# Clases de Entidades (se mantienen igual)
class Entidad:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def mover(self, nx, ny):
        self.x = nx
        self.y = ny

class Jugador(Entidad):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.energia = 100
        self.trampas = 3

class Enemigo(Entidad):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vivo = True

# Clase Juego (adaptada para Pygame)
class Juego:
    def __init__(self, ancho=ANCHO_MAPA, alto=ALTO_MAPA, num_enemigos=3):
        self.mapa = Mapa(ancho, alto)
        self.jugador = None
        self.enemigos = []
        self.nombre_jugador = ""
        self.modo_juego = ""
        self.num_enemigos = num_enemigos
        self.puntos = 0
        self.tiempo_inicio = 0
        self.tiempo_fin = 0
        self.enemigos_atrapados = 0
        self.enemigos_escapados = 0

    def iniciar(self, nombre, modo):
        self.nombre_jugador = nombre
        self.modo_juego = modo
        self.puntos = 0
        self.enemigos_atrapados = 0
        self.enemigos_escapados = 0
        self.tiempo_inicio = time.time()
        
        inicio = (1, 1)
        salida = (self.mapa.alto - 2, self.mapa.ancho - 2)
        
        self.mapa.generar_laberinto()
        while not self.mapa.existe_camino(inicio, salida):
            self.mapa.generar_laberinto()

        self.mapa.convertir_a_objetos()
        self.jugador = Jugador(*inicio)

        self.enemigos = []
        posibles = []
        for x in range(self.mapa.alto):
            for y in range(self.mapa.ancho):
                if self.mapa._es_transitable_numero(x, y, es_jugador=False):
                    if abs(x - inicio[0]) + abs(y - inicio[1]) > 6 and (x,y) != salida:
                        posibles.append((x,y))
        random.shuffle(posibles)
        i = 0
        while len(self.enemigos) < self.num_enemigos and i < len(posibles):
            pos = posibles[i]
            self.enemigos.append(Enemigo(*pos))
            i += 1
        if len(self.enemigos) == 0:
            self.enemigos.append(Enemigo(*salida))

    def calcular_puntos_escape(self):
        self.tiempo_fin = time.time()
        tiempo_transcurrido = self.tiempo_fin - self.tiempo_inicio
        puntos_base = 1000
        penalizacion_tiempo = int(tiempo_transcurrido * 2)
        bonus_dificultad = self.num_enemigos * 50
        puntos_finales = max(100, puntos_base - penalizacion_tiempo + bonus_dificultad)
        self.puntos = puntos_finales
        return puntos_finales

    def cazar_enemigo(self, enemigo):
        self.enemigos_atrapados += 1
        puntos_ganados = 20 * self.num_enemigos
        self.puntos += puntos_ganados
        return puntos_ganados

    def enemigo_escapa(self, enemigo):
        self.enemigos_escapados += 1
        puntos_perdidos = 10 * self.num_enemigos
        self.puntos = max(0, self.puntos - puntos_perdidos)
        return puntos_perdidos

# Clase principal de la aplicación en Pygame
class AppPygame:
    def __init__(self):
        self.ventana = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        pygame.display.set_caption("Laberinto - POO")
        self.reloj = pygame.time.Clock()
        self.juego = Juego(ANCHO_MAPA, ALTO_MAPA, num_enemigos=4)
        self.corriendo = True
        self.tempo_enemigo_ms = 450
        self.ultimo_movimiento_enemigo = 0

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.mover_jugador(-1, 0)
                elif evento.key == pygame.K_DOWN:
                    self.mover_jugador(1, 0)
                elif evento.key == pygame.K_LEFT:
                    self.mover_jugador(0, -1)
                elif evento.key == pygame.K_RIGHT:
                    self.mover_jugador(0, 1)

    def mover_jugador(self, dx, dy):
        nx = self.juego.jugador.x + dx
        ny = self.juego.jugador.y + dy
        if 0 <= nx < self.juego.mapa.alto and 0 <= ny < self.juego.mapa.ancho:
            casilla = self.juego.mapa.objetos[nx][ny]
            if casilla.transitable_por_jugador():
                self.juego.jugador.mover(nx, ny)
                self.verificar_estado_juego()

    def verificar_estado_juego(self):
        salida = (self.juego.mapa.alto - 2, self.juego.mapa.ancho - 2)
        if (self.juego.jugador.x, self.juego.jugador.y) == salida:
            if self.juego.modo_juego == "ESCAPA":
                puntos = self.juego.calcular_puntos_escape()
                print(f"¡Felicidades! Has escapado. Puntos: {puntos}")
                self.corriendo = False
            # En modo CAZADOR, llegar a la salida no tiene significado especial

        for e in self.juego.enemigos:
            if (e.x, e.y) == (self.juego.jugador.x, self.juego.jugador.y):
                if self.juego.modo_juego == "ESCAPA":
                    print("Has sido atrapado")
                    self.corriendo = False
                elif self.juego.modo_juego == "CAZADOR":
                    self.juego.cazar_enemigo(e)
                    self._respawnear_enemigo(e)

    def _respawnear_enemigo(self, enemigo):
        opciones = []
        for x in range(self.juego.mapa.alto):
            for y in range(self.juego.mapa.ancho):
                if self.juego.mapa._es_transitable_numero(x, y, es_jugador=False):
                    if (x, y) != (self.juego.jugador.x, self.juego.jugador.y):
                        opciones.append((x, y))
        if opciones:
            pos = random.choice(opciones)
            enemigo.mover(*pos)

    def actualizar_enemigos(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.ultimo_movimiento_enemigo > self.tempo_enemigo_ms:
            self.ultimo_movimiento_enemigo = tiempo_actual
            modo = self.juego.modo_juego
            jugador_pos = (self.juego.jugador.x, self.juego.jugador.y)

            for enemigo in self.juego.enemigos:
                if (enemigo.x, enemigo.y) == jugador_pos:
                    continue

                if modo == "ESCAPA":
                    inicio = (enemigo.x, enemigo.y)
                    path = self.juego.mapa.bfs_camino(inicio, jugador_pos, es_jugador=False)
                    if path and len(path) >= 2:
                        siguiente = path[1]
                        enemigo.mover(*siguiente)
                    else:
                        self._enemigo_mover_aleatorio(enemigo)
                else:
                    mejor = None
                    mejor_dist = -1
                    for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                        nx, ny = enemigo.x + dx, enemigo.y + dy
                        if 0 <= nx < self.juego.mapa.alto and 0 <= ny < self.juego.mapa.ancho:
                            if self.juego.mapa._es_transitable_numero(nx, ny, es_jugador=False):
                                dist = abs(nx - jugador_pos[0]) + abs(ny - jugador_pos[1])
                                if dist > mejor_dist:
                                    mejor_dist = dist
                                    mejor = (nx, ny)
                    if mejor:
                        enemigo.mover(*mejor)
                    else:
                        self._enemigo_mover_aleatorio(enemigo)

            self.verificar_estado_juego()

    def _enemigo_mover_aleatorio(self, enemigo):
        opciones = []
        for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
            nx, ny = enemigo.x + dx, enemigo.y + dy
            if 0 <= nx < self.juego.mapa.alto and 0 <= ny < self.juego.mapa.ancho:
                if self.juego.mapa._es_transitable_numero(nx, ny, es_jugador=False):
                    opciones.append((nx, ny))
        if opciones:
            enemigo.mover(*random.choice(opciones))

    def dibujar_mapa(self):
        for x in range(self.juego.mapa.alto):
            for y in range(self.juego.mapa.ancho):
                casilla = self.juego.mapa.objetos[x][y]
                if isinstance(casilla, Camino):
                    color = VERDE_CAMINO
                elif isinstance(casilla, Muro):
                    color = AZUL_MURO
                elif isinstance(casilla, Liana):
                    color = MORADO_LIANA
                elif isinstance(casilla, Tunel):
                    color = AMARILLO_TUNEL
                else:
                    color = NEGRO
                pygame.draw.rect(self.ventana, color, (y * TAMANO_CELDA, x * TAMANO_CELDA, TAMANO_CELDA, TAMANO_CELDA))

    def dibujar_entidades(self):
        # Dibujar jugador
        jx, jy = self.juego.jugador.x, self.juego.jugador.y
        pygame.draw.rect(self.ventana, ROJO_JUGADOR, (jy * TAMANO_CELDA, jx * TAMANO_CELDA, TAMANO_CELDA, TAMANO_CELDA))
        # Dibujar enemigos
        for e in self.juego.enemigos:
            pygame.draw.rect(self.ventana, AZUL_ENEMIGO, (e.y * TAMANO_CELDA, e.x * TAMANO_CELDA, TAMANO_CELDA, TAMANO_CELDA))

    def ejecutar(self):
        # Por simplicidad, aquí iniciamos el juego en modo ESCAPA con un nombre fijo
        # En un juego completo, deberías tener una pantalla de registro
        self.juego.iniciar("Jugador", "ESCAPA")

        while self.corriendo:
            self.manejar_eventos()
            self.actualizar_enemigos()
            self.ventana.fill(NEGRO)
            self.dibujar_mapa()
            self.dibujar_entidades()
            pygame.display.flip()
            self.reloj.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    app = AppPygame()
    app.ejecutar()
