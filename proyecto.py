import heapq
import json
import time
import random
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import math

class TipoEmergencia(Enum):
    INCENDIO = "incendio"
    ACCIDENTE = "accidente"
    ROBO = "robo"
    MEDICA = "medica"
    RESCATE = "rescate"

class PrioridadEmergencia(Enum):
    CRITICA = 1
    ALTA = 2
    MEDIA = 3
    BAJA = 4

@dataclass
class Emergencia:
    id: str
    tipo: TipoEmergencia
    prioridad: PrioridadEmergencia
    ubicacion: Tuple[float, float]  # (lat, lon)
    descripcion: str
    timestamp: float = field(default_factory=time.time)
    atendida: bool = False
    tiempo_respuesta: Optional[float] = None
    
    def __lt__(self, other):
        return self.prioridad.value < other.prioridad.value

@dataclass
class Recurso:
    id: str
    tipo: str  # ambulancia, bombero, policia
    ubicacion: Tuple[float, float]
    disponible: bool = True
    capacidad: int = 1

class Nodo:
    def __init__(self, id: str, nombre: str, ubicacion: Tuple[float, float]):
        self.id = id
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.activo = True
        self.emergencias_pendientes = []  # Cola de prioridad local
        self.recursos = []
        self.datos_transmitidos = 0
        self.emergencias_atendidas = 0
        self.conexiones = {}  # {nodo_id: peso}
        
    def agregar_emergencia(self, emergencia: Emergencia):
        heapq.heappush(self.emergencias_pendientes, emergencia)
    
    def obtener_emergencia_prioritaria(self) -> Optional[Emergencia]:
        if self.emergencias_pendientes:
            return heapq.heappop(self.emergencias_pendientes)
        return None
    
    def agregar_recurso(self, recurso: Recurso):
        self.recursos.append(recurso)
    
    def recursos_disponibles(self) -> List[Recurso]:
        return [r for r in self.recursos if r.disponible]

class ArbolBusquedaGeografica:
    """Árbol BST para búsqueda eficiente por coordenadas"""
    
    class NodoArbol:
        def __init__(self, nodo, es_latitud=True):
            self.nodo = nodo
            self.es_latitud = es_latitud
            self.izquierda = None
            self.derecha = None
    
    def __init__(self):
        self.raiz = None
    
    def insertar(self, nodo: Nodo):
        self.raiz = self._insertar_recursivo(self.raiz, nodo, True)
    
    def _insertar_recursivo(self, raiz_actual, nodo, es_latitud):
        if raiz_actual is None:
            return self.NodoArbol(nodo, es_latitud)
        
        coord_actual = nodo.ubicacion[0] if es_latitud else nodo.ubicacion[1]
        coord_raiz = raiz_actual.nodo.ubicacion[0] if es_latitud else raiz_actual.nodo.ubicacion[1]
        
        if coord_actual < coord_raiz:
            raiz_actual.izquierda = self._insertar_recursivo(
                raiz_actual.izquierda, nodo, not es_latitud
            )
        else:
            raiz_actual.derecha = self._insertar_recursivo(
                raiz_actual.derecha, nodo, not es_latitud
            )
        
        return raiz_actual
    
    def buscar_nodos_cercanos(self, ubicacion: Tuple[float, float], radio: float) -> List[Nodo]:
        resultado = []
        self._buscar_recursivo(self.raiz, ubicacion, radio, resultado, True)
        return resultado
    
    def _buscar_recursivo(self, nodo_actual, ubicacion, radio, resultado, es_latitud):
        if nodo_actual is None:
            return
        
        # Calcular distancia euclidiana
        distancia = math.sqrt(
            (nodo_actual.nodo.ubicacion[0] - ubicacion[0]) ** 2 +
            (nodo_actual.nodo.ubicacion[1] - ubicacion[1]) ** 2
        )
        
        if distancia <= radio:
            resultado.append(nodo_actual.nodo)
        
        coord_actual = ubicacion[0] if es_latitud else ubicacion[1]
        coord_nodo = nodo_actual.nodo.ubicacion[0] if es_latitud else nodo_actual.nodo.ubicacion[1]
        
        # Explorar subárboles relevantes
        if coord_actual - radio <= coord_nodo:
            self._buscar_recursivo(nodo_actual.izquierda, ubicacion, radio, resultado, not es_latitud)
        if coord_actual + radio >= coord_nodo:
            self._buscar_recursivo(nodo_actual.derecha, ubicacion, radio, resultado, not es_latitud)

class TablaHashEmergencias:
    """Tabla hash para acceso rápido a emergencias por ID"""
    
    def __init__(self, tamaño=1000):
        self.tamaño = tamaño
        self.tabla = [[] for _ in range(tamaño)]
    
    def _hash(self, clave: str) -> int:
        return hash(clave) % self.tamaño
    
    def insertar(self, emergencia: Emergencia):
        indice = self._hash(emergencia.id)
        # Verificar si ya existe y actualizar
        for i, (id_em, em) in enumerate(self.tabla[indice]):
            if id_em == emergencia.id:
                self.tabla[indice][i] = (emergencia.id, emergencia)
                return
        self.tabla[indice].append((emergencia.id, emergencia))
    
    def buscar(self, id_emergencia: str) -> Optional[Emergencia]:
        indice = self._hash(id_emergencia)
        for id_em, emergencia in self.tabla[indice]:
            if id_em == id_emergencia:
                return emergencia
        return None
    
    def obtener_todas(self) -> List[Emergencia]:
        todas = []
        for bucket in self.tabla:
            todas.extend([em for _, em in bucket])
        return todas

class SimuladorRedLAN:
    def __init__(self):
        self.nodos: Dict[str, Nodo] = {}
        self.grafo = defaultdict(dict)  # {nodo_origen: {nodo_destino: peso}}
        self.arbol_geografico = ArbolBusquedaGeografica()
        self.tabla_emergencias = TablaHashEmergencias()
        self.historial_rutas = []
        self.estadisticas = {
            'emergencias_totales': 0,
            'emergencias_atendidas': 0,
            'tiempo_respuesta_promedio': 0.0,
            'datos_transmitidos_total': 0
        }
    
    def agregar_nodo(self, id: str, nombre: str, ubicacion: Tuple[float, float]):
        """Agregar un nodo (estación) a la red"""
        nodo = Nodo(id, nombre, ubicacion)
        self.nodos[id] = nodo
        self.arbol_geografico.insertar(nodo)
        print(f"Nodo {id} ({nombre}) agregado en ubicación {ubicacion}")
    
    def agregar_conexion(self, nodo1: str, nodo2: str, peso: float):
        """Agregar conexión bidireccional entre nodos con peso (latencia/distancia)"""
        if nodo1 in self.nodos and nodo2 in self.nodos:
            self.grafo[nodo1][nodo2] = peso
            self.grafo[nodo2][nodo1] = peso
            self.nodos[nodo1].conexiones[nodo2] = peso
            self.nodos[nodo2].conexiones[nodo1] = peso
            print(f"Conexión agregada: {nodo1} <-> {nodo2} (peso: {peso})")
        else:
            print("Error: Uno o ambos nodos no existen")
    
    def dijkstra(self, origen: str, destino: str) -> Tuple[List[str], float]:
        """Implementación del algoritmo de Dijkstra para encontrar la ruta más corta"""
        if origen not in self.nodos or destino not in self.nodos:
            return [], float('inf')
        
        if not self.nodos[origen].activo or not self.nodos[destino].activo:
            return [], float('inf')
        
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[origen] = 0
        padres = {nodo: None for nodo in self.nodos}
        visitados = set()
        
        # Cola de prioridad: (distancia, nodo)
        cola = [(0, origen)]
        
        while cola:
            dist_actual, nodo_actual = heapq.heappop(cola)
            
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            if nodo_actual == destino:
                break
            
            # Explorar vecinos
            for vecino, peso in self.grafo[nodo_actual].items():
                if vecino not in visitados and self.nodos[vecino].activo:
                    nueva_distancia = dist_actual + peso
                    
                    if nueva_distancia < distancias[vecino]:
                        distancias[vecino] = nueva_distancia
                        padres[vecino] = nodo_actual
                        heapq.heappush(cola, (nueva_distancia, vecino))
        
        # Reconstruir ruta
        ruta = []
        nodo_actual = destino
        while nodo_actual is not None:
            ruta.append(nodo_actual)
            nodo_actual = padres[nodo_actual]
        
        ruta.reverse()
        
        if len(ruta) == 1 and ruta[0] != origen:
            return [], float('inf')
        
        return ruta, distancias[destino]
    
    def registrar_emergencia(self, emergencia: Emergencia):
        """Registrar una nueva emergencia en el sistema"""
        self.tabla_emergencias.insertar(emergencia)
        self.estadisticas['emergencias_totales'] += 1
        
        # Encontrar el nodo más cercano
        nodos_cercanos = self.arbol_geografico.buscar_nodos_cercanos(
            emergencia.ubicacion, 5.0  # Radio de búsqueda
        )
        
        if nodos_cercanos:
            # Seleccionar el nodo más cercano activo
            nodo_mas_cercano = min(
                [n for n in nodos_cercanos if n.activo],
                key=lambda n: math.sqrt(
                    (n.ubicacion[0] - emergencia.ubicacion[0]) ** 2 +
                    (n.ubicacion[1] - emergencia.ubicacion[1]) ** 2
                ),
                default=None
            )
            
            if nodo_mas_cercano:
                nodo_mas_cercano.agregar_emergencia(emergencia)
                print(f"Emergencia {emergencia.id} asignada a nodo {nodo_mas_cercano.id}")
                return nodo_mas_cercano.id
        
        # Si no hay nodos cercanos, asignar al primer nodo activo
        for nodo in self.nodos.values():
            if nodo.activo:
                nodo.agregar_emergencia(emergencia)
                print(f"Emergencia {emergencia.id} asignada por defecto a nodo {nodo.id}")
                return nodo.id
        
        print("Error: No hay nodos activos para atender la emergencia")
        return None
    
    def procesar_emergencias(self):
        """Procesar emergencias pendientes en todos los nodos"""
        for nodo in self.nodos.values():
            if not nodo.activo:
                continue
            
            emergencia = nodo.obtener_emergencia_prioritaria()
            if emergencia and not emergencia.atendida:
                # Simular procesamiento
                recursos_disponibles = nodo.recursos_disponibles()
                
                if recursos_disponibles:
                    # Asignar recurso
                    recurso = recursos_disponibles[0]
                    recurso.disponible = False
                    
                    emergencia.atendida = True
                    emergencia.tiempo_respuesta = time.time() - emergencia.timestamp
                    nodo.emergencias_atendidas += 1
                    self.estadisticas['emergencias_atendidas'] += 1
                    
                    print(f"Emergencia {emergencia.id} atendida por {recurso.tipo} desde nodo {nodo.id}")
                    
                    # Simular transmisión de datos
                    self._simular_transmision_datos(nodo, emergencia)
                else:
                    # Re-agregar a la cola si no hay recursos
                    nodo.agregar_emergencia(emergencia)
    
    def _simular_transmision_datos(self, nodo: Nodo, emergencia: Emergencia):
        """Simular transmisión de datos sobre la emergencia"""
        # Simular envío a nodos conectados
        datos_enviados = len(emergencia.descripcion) + 100  # Bytes base
        
        for nodo_conectado in nodo.conexiones:
            if self.nodos[nodo_conectado].activo:
                nodo.datos_transmitidos += datos_enviados
                self.estadisticas['datos_transmitidos_total'] += datos_enviados
    
    def simular_falla_nodo(self, id_nodo: str):
        """Simular falla de un nodo y redistribuir emergencias"""
        if id_nodo in self.nodos:
            nodo = self.nodos[id_nodo]
            nodo.activo = False
            
            # Redistribuir emergencias pendientes
            emergencias_pendientes = []
            while nodo.emergencias_pendientes:
                emergencias_pendientes.append(heapq.heappop(nodo.emergencias_pendientes))
            
            # Redistribuir a nodos vecinos activos
            for emergencia in emergencias_pendientes:
                nodos_vecinos = [
                    self.nodos[vecino] for vecino in nodo.conexiones 
                    if self.nodos[vecino].activo
                ]
                
                if nodos_vecinos:
                    nodo_destino = random.choice(nodos_vecinos)
                    nodo_destino.agregar_emergencia(emergencia)
                    print(f"Emergencia {emergencia.id} redistribuida de {id_nodo} a {nodo_destino.id}")
            
            print(f"Nodo {id_nodo} marcado como inactivo")
    
    def restaurar_nodo(self, id_nodo: str):
        """Restaurar un nodo previamente fallido"""
        if id_nodo in self.nodos:
            self.nodos[id_nodo].activo = True
            print(f"Nodo {id_nodo} restaurado")
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de rendimiento de la red"""
        # Calcular tiempo de respuesta promedio
        emergencias_atendidas = [
            em for em in self.tabla_emergencias.obtener_todas() 
            if em.atendida and em.tiempo_respuesta
        ]
        
        if emergencias_atendidas:
            tiempo_promedio = sum(em.tiempo_respuesta for em in emergencias_atendidas) / len(emergencias_atendidas)
            self.estadisticas['tiempo_respuesta_promedio'] = tiempo_promedio
        
        # Estadísticas por nodo
        stats_nodos = {}
        for id_nodo, nodo in self.nodos.items():
            stats_nodos[id_nodo] = {
                'emergencias_atendidas': nodo.emergencias_atendidas,
                'datos_transmitidos': nodo.datos_transmitidos,
                'emergencias_pendientes': len(nodo.emergencias_pendientes),
                'activo': nodo.activo,
                'recursos_disponibles': len(nodo.recursos_disponibles())
            }
        
        return {
            'general': self.estadisticas,
            'nodos': stats_nodos
        }
    
    def cargar_topologia_desde_archivo(self, archivo: str):
        """Cargar topología de red desde archivo JSON"""
        try:
            with open(archivo, 'r') as f:
                data = json.load(f)
            
            # Cargar nodos
            for nodo_data in data.get('nodos', []):
                self.agregar_nodo(
                    nodo_data['id'],
                    nodo_data['nombre'],
                    tuple(nodo_data['ubicacion'])
                )
                
                # Agregar IP si está disponible
                if 'ip' in nodo_data:
                    self.nodos[nodo_data['id']].ip = nodo_data['ip']
                
                # Agregar recursos al nodo
                for recurso_data in nodo_data.get('recursos', []):
                    recurso = Recurso(
                        recurso_data['id'],
                        recurso_data['tipo'],
                        tuple(nodo_data['ubicacion'])
                    )
                    self.nodos[nodo_data['id']].agregar_recurso(recurso)
            
            # Cargar conexiones
            for conexion in data.get('conexiones', []):
                self.agregar_conexion(
                    conexion['nodo1'],
                    conexion['nodo2'],
                    conexion['peso']
                )
            
            print(f"Topología cargada desde {archivo}")
            
        except FileNotFoundError:
            print(f"Archivo {archivo} no encontrado")
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON en {archivo}")
    
    def cargar_topologia_packet_tracer(self, dispositivos: dict, conexiones: list):
        """Cargar topología directamente desde configuración de Packet Tracer"""
        print("Cargando topología desde Packet Tracer...")
        
        # Cargar dispositivos
        for dispositivo in dispositivos:
            # Usar coordenadas de Packet Tracer o generar ubicaciones lógicas
            ubicacion = (
                dispositivo.get('x', 0) / 100.0,  # Normalizar coordenadas PT
                dispositivo.get('y', 0) / 100.0
            )
            
            self.agregar_nodo(
                dispositivo['id'],
                dispositivo['nombre'],
                ubicacion
            )
            
            # Agregar información adicional del dispositivo
            nodo = self.nodos[dispositivo['id']]
            nodo.ip = dispositivo.get('ip', '')
            nodo.tipo_dispositivo = dispositivo.get('tipo', 'router')
            nodo.modelo = dispositivo.get('modelo', '')
            
            # Agregar recursos basados en el tipo de dispositivo
            if 'estacion' in dispositivo['nombre'].lower() or 'pc' in dispositivo['nombre'].lower():
                # Es una estación de trabajo
                recurso = Recurso(f"{dispositivo['id']}_operador", "operador", ubicacion)
                nodo.agregar_recurso(recurso)
            elif 'server' in dispositivo['nombre'].lower():
                # Es un servidor
                recurso = Recurso(f"{dispositivo['id']}_servidor", "servidor", ubicacion)
                nodo.agregar_recurso(recurso)
        
        # Cargar conexiones
        for conexion in conexiones:
            # Peso basado en tipo de conexión o distancia
            peso = conexion.get('latencia', 1.0)
            if 'ethernet' in conexion.get('tipo', '').lower():
                peso = 1.0  # Conexión rápida
            elif 'serial' in conexion.get('tipo', '').lower():
                peso = 5.0  # Conexión más lenta
            
            self.agregar_conexion(
                conexion['dispositivo1'],
                conexion['dispositivo2'],
                peso
            )
        
        print(f"Topología de Packet Tracer cargada: {len(dispositivos)} dispositivos, {len(conexiones)} conexiones")
    
    def generar_archivo_configuracion_pt(self, nombre_archivo: str = "topologia_pt.json"):
        """Generar archivo de configuración compatible con datos de Packet Tracer"""
        config_ejemplo = {
            "dispositivos": [
                {
                    "id": "R1",
                    "nombre": "Router Central",
                    "tipo": "router",
                    "modelo": "2811",
                    "ip": "192.168.1.1",
                    "x": 400,
                    "y": 300
                },
                {
                    "id": "S1",
                    "nombre": "Switch Principal",
                    "tipo": "switch",
                    "modelo": "2960",
                    "ip": "192.168.1.10",
                    "x": 200,
                    "y": 200
                },
                {
                    "id": "PC1",
                    "nombre": "Estación Bomberos",
                    "tipo": "pc",
                    "modelo": "PC-PT",
                    "ip": "192.168.1.100",
                    "x": 100,
                    "y": 100
                },
                {
                    "id": "PC2",
                    "nombre": "Estación Policía",
                    "tipo": "pc",
                    "modelo": "PC-PT",
                    "ip": "192.168.1.101",
                    "x": 300,
                    "y": 100
                },
                {
                    "id": "SRV1",
                    "nombre": "Servidor Emergencias",
                    "tipo": "server",
                    "modelo": "Server-PT",
                    "ip": "192.168.1.200",
                    "x": 500,
                    "y": 200
                }
            ],
            "conexiones": [
                {
                    "dispositivo1": "R1",
                    "dispositivo2": "S1",
                    "tipo": "ethernet",
                    "latencia": 1.0
                },
                {
                    "dispositivo1": "S1",
                    "dispositivo2": "PC1",
                    "tipo": "ethernet",
                    "latencia": 1.0
                },
                {
                    "dispositivo1": "S1",
                    "dispositivo2": "PC2",
                    "tipo": "ethernet",
                    "latencia": 1.0
                },
                {
                    "dispositivo1": "R1",
                    "dispositivo2": "SRV1",
                    "tipo": "ethernet",
                    "latencia": 1.0
                }
            ]
        }
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(config_ejemplo, f, indent=2, ensure_ascii=False)
        
        print(f"Archivo de configuración ejemplo generado: {nombre_archivo}")
        print("Modifica este archivo con los datos de tu topología de Packet Tracer")
    
    def generar_topologia_automatica(self, num_nodos: int = 10):
        """Generar topología de red automáticamente"""
        # Generar nodos con ubicaciones aleatorias
        for i in range(num_nodos):
            id_nodo = f"N{i+1:02d}"
            nombre = f"Estación {i+1}"
            ubicacion = (
                random.uniform(-10, 10),  # Latitud simulada
                random.uniform(-10, 10)   # Longitud simulada
            )
            
            self.agregar_nodo(id_nodo, nombre, ubicacion)
            
            # Agregar recursos aleatorios
            tipos_recursos = ['ambulancia', 'bombero', 'policia']
            num_recursos = random.randint(1, 3)
            
            for j in range(num_recursos):
                tipo = random.choice(tipos_recursos)
                recurso = Recurso(f"{id_nodo}_{tipo}_{j}", tipo, ubicacion)
                self.nodos[id_nodo].agregar_recurso(recurso)
        
        # Generar conexiones (red parcialmente conectada)
        nodos_ids = list(self.nodos.keys())
        for i, nodo1 in enumerate(nodos_ids):
            # Conectar con algunos nodos cercanos
            for j in range(i+1, min(i+4, len(nodos_ids))):
                nodo2 = nodos_ids[j]
                # Peso basado en distancia euclidiana
                pos1 = self.nodos[nodo1].ubicacion
                pos2 = self.nodos[nodo2].ubicacion
                distancia = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                
                self.agregar_conexion(nodo1, nodo2, round(distancia, 2))
        
        print(f"Topología automática generada con {num_nodos} nodos")
    
    def imprimir_estado_red(self):
        """Imprimir estado actual de la red"""
        print("\n" + "="*50)
        print("ESTADO ACTUAL DE LA RED")
        print("="*50)
        
        for id_nodo, nodo in self.nodos.items():
            estado = "ACTIVO" if nodo.activo else "INACTIVO"
            print(f"\nNodo {id_nodo} ({nodo.nombre}) - {estado}")
            print(f"  Ubicación: {nodo.ubicacion}")
            print(f"  Emergencias pendientes: {len(nodo.emergencias_pendientes)}")
            print(f"  Emergencias atendidas: {nodo.emergencias_atendidas}")
            print(f"  Recursos disponibles: {len(nodo.recursos_disponibles())}/{len(nodo.recursos)}")
            print(f"  Datos transmitidos: {nodo.datos_transmitidos} bytes")
            print(f"  Conexiones: {list(nodo.conexiones.keys())}")

def demo_simulador():
    """Función de demostración del simulador"""
    print("Iniciando Demo del Simulador de Red LAN para Emergencias")
    print("="*60)
    
    # Crear simulador
    sim = SimuladorRedLAN()
    
    # Generar topología automática
    sim.generar_topologia_automatica(8)
    
    # Crear algunas emergencias de prueba
    emergencias_prueba = [
        Emergencia("E001", TipoEmergencia.INCENDIO, PrioridadEmergencia.CRITICA, (2.5, 3.1), "Incendio en edificio comercial"),
        Emergencia("E002", TipoEmergencia.ACCIDENTE, PrioridadEmergencia.ALTA, (-1.2, 4.5), "Accidente de tráfico múltiple"),
        Emergencia("E003", TipoEmergencia.MEDICA, PrioridadEmergencia.MEDIA, (5.0, -2.0), "Emergencia médica"),
        Emergencia("E004", TipoEmergencia.ROBO, PrioridadEmergencia.BAJA, (-3.0, -1.5), "Robo en tienda"),
        Emergencia("E005", TipoEmergencia.RESCATE, PrioridadEmergencia.CRITICA, (1.0, 1.0), "Persona atrapada"),
    ]
    
    # Registrar emergencias
    print("\nRegistrando emergencias...")
    for emergencia in emergencias_prueba:
        sim.registrar_emergencia(emergencia)
    
    # Mostrar estado inicial
    sim.imprimir_estado_red()
    
    # Procesar emergencias
    print("\nProcesando emergencias...")
    sim.procesar_emergencias()
    
    # Simular falla de nodo
    print("\nSimulando falla del nodo N03...")
    sim.simular_falla_nodo("N03")
    
    # Procesar más emergencias
    print("\nProcesando emergencias después de la falla...")
    sim.procesar_emergencias()
    
    # Mostrar estadísticas finales
    print("\nEstadísticas finales:")
    stats = sim.obtener_estadisticas()
    print(f"Emergencias totales: {stats['general']['emergencias_totales']}")
    print(f"Emergencias atendidas: {stats['general']['emergencias_atendidas']}")
    print(f"Tiempo respuesta promedio: {stats['general']['tiempo_respuesta_promedio']:.2f} segundos")
    print(f"Datos transmitidos total: {stats['general']['datos_transmitidos_total']} bytes")
    
    # Prueba de algoritmo de Dijkstra
    print("\nPrueba de enrutamiento (Dijkstra):")
    ruta, distancia = sim.dijkstra("N01", "N08")
    if ruta:
        print(f"Ruta más corta de N01 a N08: {' -> '.join(ruta)}")
        print(f"Distancia total: {distancia:.2f}")
    else:
        print("No se encontró ruta entre N01 y N08")

if __name__ == "__main__":
    demo_simulador()