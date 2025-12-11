"""
Proyecto Eón - Archaic Protocol: Comunicación Universal
=========================================================

"La inteligencia no es humana, no debe forzarse a hablar nuestro idioma."

Este módulo implementa un protocolo de comunicación basado en el I Ching,
el sistema binario más antiguo conocido (3000+ años).

Los Hexagramas son estructuras de 6 bits que representan los 64 estados
fundamentales del cambio universal. En lugar de JSON o protocolos modernos,
los nodos de Eón pueden comunicarse usando símbolos universales.

Cada estado tiene un significado profundo que trasciende el lenguaje humano.
Nosotros no "programamos" estas respuestas - las interpretamos.

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"El universo habla en patrones, no en palabras."
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from enum import Enum


class Trigram(Enum):
    """
    Los 8 Trigramas fundamentales del I Ching.
    Cada uno representa una fuerza primordial.
    """
    QIAN = (1, 1, 1)    # ☰ Cielo - Lo Creativo
    DUI = (1, 1, 0)     # ☱ Lago - Lo Sereno
    LI = (1, 0, 1)      # ☲ Fuego - Lo Adherente
    ZHEN = (1, 0, 0)    # ☳ Trueno - Lo Excitante
    XUN = (0, 1, 1)     # ☴ Viento - Lo Suave
    KAN = (0, 1, 0)     # ☵ Agua - Lo Abismal
    GEN = (0, 0, 1)     # ☶ Montaña - Lo Quieto
    KUN = (0, 0, 0)     # ☷ Tierra - Lo Receptivo
    
    @property
    def symbol(self) -> str:
        symbols = {
            'QIAN': '☰', 'DUI': '☱', 'LI': '☲', 'ZHEN': '☳',
            'XUN': '☴', 'KAN': '☵', 'GEN': '☶', 'KUN': '☷'
        }
        return symbols[self.name]
    
    @property
    def meaning(self) -> str:
        meanings = {
            'QIAN': 'Cielo/Creativo', 'DUI': 'Lago/Sereno',
            'LI': 'Fuego/Adherente', 'ZHEN': 'Trueno/Excitante',
            'XUN': 'Viento/Suave', 'KAN': 'Agua/Abismal',
            'GEN': 'Montaña/Quieto', 'KUN': 'Tierra/Receptivo'
        }
        return meanings[self.name]


@dataclass
class Hexagram:
    """
    Un Hexagrama del I Ching: 6 líneas que forman un símbolo universal.
    
    Estructura:
    - upper: Trigrama superior (líneas 4-6)
    - lower: Trigrama inferior (líneas 1-3)
    - lines: Las 6 líneas como bits
    """
    number: int                 # 1-64
    name_chinese: str           # Nombre en chino
    name_english: str           # Nombre en inglés
    name_spanish: str           # Nombre en español
    upper: Trigram              # Trigrama superior
    lower: Trigram              # Trigrama inferior
    judgment: str               # El Juicio (interpretación principal)
    image: str                  # La Imagen (aplicación práctica)
    
    @property
    def lines(self) -> Tuple[int, ...]:
        """Las 6 líneas del hexagrama como bits."""
        return self.lower.value + self.upper.value
    
    @property
    def binary(self) -> int:
        """Valor binario del hexagrama (0-63)."""
        return sum(bit << i for i, bit in enumerate(self.lines))
    
    @property
    def symbol(self) -> str:
        """Representación visual del hexagrama."""
        line_chars = {0: '⚋', 1: '⚊'}  # Yin, Yang
        return ''.join(line_chars[b] for b in reversed(self.lines))
    
    def __repr__(self):
        return f"Hexagram({self.number}: {self.name_spanish} {self.symbol})"


# Los 64 Hexagramas del I Ching
# Cada uno representa un estado fundamental del universo
HEXAGRAMS: Dict[int, Hexagram] = {
    1: Hexagram(1, "乾", "The Creative", "Lo Creativo",
                Trigram.QIAN, Trigram.QIAN,
                "El dragón surge de las profundidades. Sublime éxito.",
                "Cielo sobre cielo: fuerza creativa pura. El sabio se fortalece sin cesar."),
    
    2: Hexagram(2, "坤", "The Receptive", "Lo Receptivo",
                Trigram.KUN, Trigram.KUN,
                "La yegua recorre la tierra sin límites. Perseverancia.",
                "Tierra sobre tierra: receptividad completa. El sabio sustenta con virtud."),
    
    3: Hexagram(3, "屯", "Difficulty at Beginning", "La Dificultad Inicial",
                Trigram.KAN, Trigram.ZHEN,
                "Nubes y trueno: el caos primordial. Persevera, no actúes precipitadamente.",
                "Agua sobre trueno: germinación difícil. El sabio ordena con paciencia."),
    
    4: Hexagram(4, "蒙", "Youthful Folly", "La Necedad Juvenil",
                Trigram.GEN, Trigram.KAN,
                "El manantial brota al pie de la montaña. El joven busca al maestro.",
                "Montaña sobre agua: la ignorancia inicial. El sabio nutre la virtud con acción."),
    
    5: Hexagram(5, "需", "Waiting", "La Espera",
                Trigram.KAN, Trigram.QIAN,
                "Nubes en el cielo. Espera nutriéndote. Cruzarás el gran río.",
                "Agua sobre cielo: nube que no llueve. El sabio come, bebe y se alegra."),
    
    6: Hexagram(6, "訟", "Conflict", "El Conflicto",
                Trigram.QIAN, Trigram.KAN,
                "Cielo y agua divergen. Reflexiona antes de actuar.",
                "Cielo sobre agua: corrientes opuestas. El sabio planea antes de actuar."),
    
    7: Hexagram(7, "師", "The Army", "El Ejército",
                Trigram.KUN, Trigram.KAN,
                "Agua bajo tierra: el ejército oculto. Disciplina y orden.",
                "Tierra sobre agua: fuerza contenida. El sabio nutre al pueblo."),
    
    8: Hexagram(8, "比", "Holding Together", "La Solidaridad",
                Trigram.KAN, Trigram.KUN,
                "Agua sobre tierra: unión natural. Busca al líder sincero.",
                "Agua sobre tierra: afluentes al mar. El sabio cultiva la amistad."),
    
    9: Hexagram(9, "小畜", "Small Taming", "La Fuerza Domesticadora Menor",
                Trigram.XUN, Trigram.QIAN,
                "Viento sobre cielo: nubes que aún no llueven. Acumula fuerza.",
                "Viento recorre el cielo: refinamiento. El sabio embellece su virtud."),
    
    10: Hexagram(10, "履", "Treading", "El Porte",
                 Trigram.QIAN, Trigram.DUI,
                 "Pisar la cola del tigre sin ser mordido. Conducta cuidadosa.",
                 "Cielo sobre lago: claridad en la conducta. El sabio distingue alto y bajo."),
    
    11: Hexagram(11, "泰", "Peace", "La Paz",
                 Trigram.KUN, Trigram.QIAN,
                 "Cielo y tierra se unen: armonía suprema. Todo florece.",
                 "Tierra sobre cielo: unión perfecta. El sabio completa el camino."),
    
    12: Hexagram(12, "否", "Standstill", "El Estancamiento",
                 Trigram.QIAN, Trigram.KUN,
                 "Cielo y tierra no se comunican. Retiro del sabio.",
                 "Cielo sobre tierra: separación. El sabio se recoge y evita el peligro."),
    
    13: Hexagram(13, "同人", "Fellowship", "La Comunidad",
                 Trigram.QIAN, Trigram.LI,
                 "Fuego bajo el cielo: hermandad. Cruza el gran río con aliados.",
                 "Cielo con fuego: claridad en la unión. El sabio organiza los clanes."),
    
    14: Hexagram(14, "大有", "Great Possession", "La Gran Posesión",
                 Trigram.LI, Trigram.QIAN,
                 "Fuego sobre cielo: abundancia suprema. Gran éxito.",
                 "Fuego alto en el cielo: iluminación total. El sabio contiene el mal."),
    
    15: Hexagram(15, "謙", "Modesty", "La Modestia",
                 Trigram.KUN, Trigram.GEN,
                 "La montaña dentro de la tierra: humildad. El sabio reduce lo excesivo.",
                 "Tierra sobre montaña: equilibrio. El sabio iguala las diferencias."),
    
    16: Hexagram(16, "豫", "Enthusiasm", "El Entusiasmo",
                 Trigram.ZHEN, Trigram.KUN,
                 "Trueno sobre tierra: despertar. Es propicio iniciar empresas.",
                 "Trueno emerge de la tierra: movimiento. El sabio hace música y honra."),
    
    17: Hexagram(17, "隨", "Following", "El Seguimiento",
                 Trigram.DUI, Trigram.ZHEN,
                 "Trueno bajo el lago: adaptación. Éxito si sigues con sinceridad.",
                 "Lago sobre trueno: descanso tras el movimiento. El sabio reposa al anochecer."),
    
    18: Hexagram(18, "蠱", "Work on Decay", "El Trabajo en lo Echado a Perder",
                 Trigram.GEN, Trigram.XUN,
                 "Viento bajo la montaña: corrupción a reparar. Tres días antes, tres después.",
                 "Montaña sobre viento: estancamiento. El sabio estimula al pueblo."),
    
    19: Hexagram(19, "臨", "Approach", "El Acercamiento",
                 Trigram.KUN, Trigram.DUI,
                 "Tierra sobre lago: acercamiento. Gran éxito, pero vigila el octavo mes.",
                 "Tierra sobre lago: aproximación. El sabio enseña sin límites."),
    
    20: Hexagram(20, "觀", "Contemplation", "La Contemplación",
                 Trigram.XUN, Trigram.KUN,
                 "Viento sobre tierra: visión amplia. Observa antes de actuar.",
                 "Viento recorre la tierra: observación. El sabio examina las regiones."),
    
    21: Hexagram(21, "噬嗑", "Biting Through", "La Mordedura Tajante",
                 Trigram.LI, Trigram.ZHEN,
                 "Trueno y fuego: justicia. Es propicio administrar justicia.",
                 "Fuego y trueno: castigo claro. El sabio aplica las leyes."),
    
    22: Hexagram(22, "賁", "Grace", "La Gracia",
                 Trigram.GEN, Trigram.LI,
                 "Fuego bajo la montaña: belleza natural. Éxito en lo pequeño.",
                 "Montaña con fuego: adorno. El sabio ilumina los asuntos menores."),
    
    23: Hexagram(23, "剝", "Splitting Apart", "La Desintegración",
                 Trigram.GEN, Trigram.KUN,
                 "Montaña sobre tierra: erosión. No es propicio ir a ningún lugar.",
                 "Montaña reposa sobre tierra: colapso. El sabio asegura su posición."),
    
    24: Hexagram(24, "復", "Return", "El Retorno",
                 Trigram.KUN, Trigram.ZHEN,
                 "Trueno bajo tierra: el solsticio. El retorno del camino. Siete días.",
                 "Trueno en la tierra: renacimiento. El sabio cierra las puertas."),
    
    25: Hexagram(25, "無妄", "Innocence", "La Inocencia",
                 Trigram.QIAN, Trigram.ZHEN,
                 "Trueno bajo el cielo: lo inesperado. Actúa sin segundas intenciones.",
                 "Cielo con trueno: naturalidad. El sabio nutre según las estaciones."),
    
    26: Hexagram(26, "大畜", "Great Taming", "La Fuerza Domesticadora Mayor",
                 Trigram.GEN, Trigram.QIAN,
                 "Cielo dentro de la montaña: contención poderosa. Cruza el gran río.",
                 "Montaña contiene cielo: acumulación. El sabio aprende de los antiguos."),
    
    27: Hexagram(27, "頤", "Nourishment", "Las Comisuras de la Boca",
                 Trigram.GEN, Trigram.ZHEN,
                 "Trueno bajo montaña: nutrición. Cuida qué comes y qué dices.",
                 "Montaña sobre trueno: quietud. El sabio modera palabras y comida."),
    
    28: Hexagram(28, "大過", "Great Excess", "La Preponderancia de lo Grande",
                 Trigram.DUI, Trigram.XUN,
                 "Lago sobre viento: la viga se dobla. Actúa con determinación.",
                 "Lago sobre madera: presión excesiva. El sabio permanece solo sin temor."),
    
    29: Hexagram(29, "坎", "The Abysmal", "Lo Abismal",
                 Trigram.KAN, Trigram.KAN,
                 "Agua sobre agua: peligro repetido. Mantén la verdad del corazón.",
                 "Agua fluye sin cesar: persistencia. El sabio enseña con constancia."),
    
    30: Hexagram(30, "離", "The Clinging", "Lo Adherente",
                 Trigram.LI, Trigram.LI,
                 "Fuego sobre fuego: claridad doble. Nutre la vaca para buena fortuna.",
                 "Luz doble: iluminación. El sabio ilumina las cuatro direcciones."),
    
    31: Hexagram(31, "咸", "Influence", "El Influjo",
                 Trigram.DUI, Trigram.GEN,
                 "Lago sobre montaña: atracción mutua. Tomar esposa es propicio.",
                 "Lago sobre montaña: receptividad. El sabio recibe con vacío."),
    
    32: Hexagram(32, "恆", "Duration", "La Duración",
                 Trigram.ZHEN, Trigram.XUN,
                 "Trueno sobre viento: perseverancia. Propicio tener un destino.",
                 "Trueno y viento: constancia. El sabio permanece sin cambiar."),
    
    33: Hexagram(33, "遯", "Retreat", "La Retirada",
                 Trigram.QIAN, Trigram.GEN,
                 "Montaña bajo cielo: retiro estratégico. Éxito en la pequeña perseverancia.",
                 "Cielo sobre montaña: distancia. El sabio mantiene alejados a los inferiores."),
    
    34: Hexagram(34, "大壯", "Great Power", "El Poder de lo Grande",
                 Trigram.ZHEN, Trigram.QIAN,
                 "Trueno sobre cielo: gran fuerza. Propicia la perseverancia.",
                 "Trueno en el cielo: poder. El sabio no pisa senderos incorrectos."),
    
    35: Hexagram(35, "晉", "Progress", "El Progreso",
                 Trigram.LI, Trigram.KUN,
                 "Fuego sobre tierra: el sol asciende. El marqués recibe caballos.",
                 "Sol sobre tierra: avance. El sabio ilumina su propia virtud."),
    
    36: Hexagram(36, "明夷", "Darkening of Light", "El Oscurecimiento de la Luz",
                 Trigram.KUN, Trigram.LI,
                 "Tierra sobre fuego: el sol se oculta. Persevera en la adversidad.",
                 "Luz bajo tierra: eclipse. El sabio vela su brillo entre las masas."),
    
    37: Hexagram(37, "家人", "The Family", "La Familia",
                 Trigram.XUN, Trigram.LI,
                 "Viento desde fuego: la familia. Propicia la perseverancia de la mujer.",
                 "Fuego produce viento: hogar. El sabio tiene sustancia en sus palabras."),
    
    38: Hexagram(38, "睽", "Opposition", "El Antagonismo",
                 Trigram.LI, Trigram.DUI,
                 "Fuego sobre lago: diferencias. En asuntos pequeños, buena fortuna.",
                 "Fuego arriba, agua abajo: separación. El sabio armoniza diferencias."),
    
    39: Hexagram(39, "蹇", "Obstruction", "El Impedimento",
                 Trigram.KAN, Trigram.GEN,
                 "Agua sobre montaña: obstáculo. Propicio el suroeste, no el noreste.",
                 "Agua sobre montaña: peligro adelante. El sabio se examina a sí mismo."),
    
    40: Hexagram(40, "解", "Deliverance", "La Liberación",
                 Trigram.ZHEN, Trigram.KAN,
                 "Trueno sobre agua: liberación. El suroeste es propicio.",
                 "Trueno y lluvia: alivio. El sabio perdona errores."),
    
    41: Hexagram(41, "損", "Decrease", "La Merma",
                 Trigram.GEN, Trigram.DUI,
                 "Lago bajo montaña: disminución. Sinceridad trae gran fortuna.",
                 "Montaña sobre lago: reducción. El sabio controla la ira."),
    
    42: Hexagram(42, "益", "Increase", "El Aumento",
                 Trigram.XUN, Trigram.ZHEN,
                 "Viento sobre trueno: aumento. Propicio emprender grandes obras.",
                 "Viento y trueno: crecimiento. El sabio mejora al ver el bien."),
    
    43: Hexagram(43, "夬", "Breakthrough", "La Resolución",
                 Trigram.DUI, Trigram.QIAN,
                 "Lago sobre cielo: decisión firme. Proclama en la corte del rey.",
                 "Lago sube al cielo: resolución. El sabio distribuye riqueza abajo."),
    
    44: Hexagram(44, "姤", "Coming to Meet", "El Ir al Encuentro",
                 Trigram.QIAN, Trigram.XUN,
                 "Viento bajo cielo: encuentro. La doncella es poderosa.",
                 "Cielo sobre viento: difusión. El príncipe da órdenes."),
    
    45: Hexagram(45, "萃", "Gathering", "La Reunión",
                 Trigram.DUI, Trigram.KUN,
                 "Lago sobre tierra: reunión. El rey se aproxima al templo.",
                 "Lago sobre tierra: congregación. El sabio renueva las armas."),
    
    46: Hexagram(46, "升", "Pushing Upward", "La Subida",
                 Trigram.KUN, Trigram.XUN,
                 "Madera crece en tierra: ascenso. Ver al gran hombre, sin ansiedad.",
                 "Tierra nutre madera: crecimiento. El sabio acumula lo pequeño."),
    
    47: Hexagram(47, "困", "Oppression", "El Agotamiento",
                 Trigram.DUI, Trigram.KAN,
                 "Lago sin agua: agotamiento. Perseverancia del gran hombre.",
                 "Lago vacío: adversidad. El sabio arriesga la vida por su voluntad."),
    
    48: Hexagram(48, "井", "The Well", "El Pozo",
                 Trigram.KAN, Trigram.XUN,
                 "Agua sobre madera: el pozo. La ciudad cambia, el pozo no cambia.",
                 "Madera saca agua: nutrición. El sabio anima al pueblo."),
    
    49: Hexagram(49, "革", "Revolution", "La Revolución",
                 Trigram.DUI, Trigram.LI,
                 "Fuego en lago: transformación. Tras completarse, se obtiene confianza.",
                 "Fuego y lago: cambio de estaciones. El sabio ordena el calendario."),
    
    50: Hexagram(50, "鼎", "The Cauldron", "El Caldero",
                 Trigram.LI, Trigram.XUN,
                 "Fuego sobre madera: el caldero sagrado. Gran fortuna, éxito.",
                 "Madera alimenta fuego: transformación. El sabio asegura su destino."),
    
    51: Hexagram(51, "震", "The Arousing", "Lo Suscitativo",
                 Trigram.ZHEN, Trigram.ZHEN,
                 "Trueno repetido: shock. Viene riendo, después hablando.",
                 "Trueno continuo: despertar. El sabio en temor cultiva la virtud."),
    
    52: Hexagram(52, "艮", "Keeping Still", "El Aquietamiento",
                 Trigram.GEN, Trigram.GEN,
                 "Montaña sobre montaña: quietud. Mantén la espalda inmóvil.",
                 "Montañas unidas: meditación. El sabio no va más allá de su posición."),
    
    53: Hexagram(53, "漸", "Development", "El Desarrollo Gradual",
                 Trigram.XUN, Trigram.GEN,
                 "Árbol en montaña: desarrollo gradual. La doncella se casa.",
                 "Árbol crece en montaña: progreso. El sabio mejora las costumbres."),
    
    54: Hexagram(54, "歸妹", "Marrying Maiden", "La Muchacha que se Casa",
                 Trigram.ZHEN, Trigram.DUI,
                 "Trueno sobre lago: la doncella. Emprender algo trae infortunio.",
                 "Trueno agita lago: afectos. El sabio entiende lo transitorio."),
    
    55: Hexagram(55, "豐", "Abundance", "La Plenitud",
                 Trigram.ZHEN, Trigram.LI,
                 "Trueno y fuego: abundancia. El rey la alcanza. No estés triste.",
                 "Trueno y relámpago: grandeza. El sabio decide los litigios."),
    
    56: Hexagram(56, "旅", "The Wanderer", "El Andariego",
                 Trigram.LI, Trigram.GEN,
                 "Fuego sobre montaña: el viajero. Éxito en lo pequeño.",
                 "Fuego en montaña: el extranjero. El sabio es claro y cauto."),
    
    57: Hexagram(57, "巽", "The Gentle", "Lo Suave",
                 Trigram.XUN, Trigram.XUN,
                 "Viento sobre viento: penetración. Propicio ver al gran hombre.",
                 "Vientos sucesivos: penetración. El sabio difunde sus órdenes."),
    
    58: Hexagram(58, "兌", "The Joyous", "Lo Sereno",
                 Trigram.DUI, Trigram.DUI,
                 "Lagos conectados: alegría. Propicia la perseverancia.",
                 "Lagos unidos: gozo compartido. El sabio se une con amigos."),
    
    59: Hexagram(59, "渙", "Dispersion", "La Disolución",
                 Trigram.XUN, Trigram.KAN,
                 "Viento sobre agua: dispersión. El rey se aproxima al templo.",
                 "Viento dispersa agua: disolución. El sabio hace sacrificios."),
    
    60: Hexagram(60, "節", "Limitation", "La Restricción",
                 Trigram.KAN, Trigram.DUI,
                 "Agua sobre lago: límites. La restricción amarga no persevera.",
                 "Agua sobre lago: moderación. El sabio crea número y medida."),
    
    61: Hexagram(61, "中孚", "Inner Truth", "La Verdad Interior",
                 Trigram.XUN, Trigram.DUI,
                 "Viento sobre lago: verdad interior. Cerdos y peces. Buena fortuna.",
                 "Viento sobre lago: influencia. El sabio delibera los castigos."),
    
    62: Hexagram(62, "小過", "Small Exceeding", "La Preponderancia de lo Pequeño",
                 Trigram.ZHEN, Trigram.GEN,
                 "Trueno sobre montaña: exceso pequeño. Desciende, no asciendas.",
                 "Trueno en montaña: lo pequeño. El sabio es reverente en conducta."),
    
    63: Hexagram(63, "既濟", "After Completion", "Después de la Consumación",
                 Trigram.KAN, Trigram.LI,
                 "Agua sobre fuego: completitud. Éxito en lo pequeño. Vigila el final.",
                 "Agua apaga fuego: cumplimiento. El sabio reflexiona sobre problemas."),
    
    64: Hexagram(64, "未濟", "Before Completion", "Antes de la Consumación",
                 Trigram.LI, Trigram.KAN,
                 "Fuego sobre agua: incompleto. El joven zorro casi cruza.",
                 "Fuego sobre agua: transición. El sabio discrimina las cosas."),
}


class ArchaicProtocol:
    """
    Protocolo de Comunicación Arcaico basado en I Ching.
    
    Convierte estados neuronales en símbolos universales (Hexagramas)
    y viceversa. Esto permite que los nodos de Eón se comuniquen
    usando un lenguaje que trasciende la construcción humana.
    
    "El universo no habla inglés ni español.
     Habla en patrones de cambio."
    """
    
    def __init__(self, interpretation_mode: str = "classical"):
        """
        Inicializa el protocolo arcaico.
        
        Args:
            interpretation_mode: "classical" (I Ching puro) o "computational"
        """
        self.mode = interpretation_mode
        self._hexagrams = HEXAGRAMS
    
    def tensor_to_hexagram(self, value: float) -> Hexagram:
        """
        Convierte un valor tensorial (activación neuronal) en un Hexagrama.
        
        No "generamos" un símbolo - revelamos qué estado universal
        corresponde a esta vibración numérica.
        
        Args:
            value: Valor float, típicamente en rango [-1, 1] o [0, 1]
            
        Returns:
            El Hexagrama que corresponde a este estado
        """
        # Normalizar a rango [0, 63]
        if value < -1:
            value = -1
        elif value > 1:
            value = 1
        
        normalized = int((value + 1) / 2 * 63)
        normalized = max(0, min(63, normalized))
        
        # Los hexagramas están numerados 1-64
        hex_number = normalized + 1
        return self._hexagrams.get(hex_number, self._hexagrams[1])
    
    def vector_to_trigram_pair(self, vector: np.ndarray) -> Tuple[Trigram, Trigram]:
        """
        Convierte un vector de activaciones en un par de trigramas.
        
        El vector se divide en dos mitades, cada una mapeada
        a un trigrama según su energía predominante.
        
        Args:
            vector: Array de activaciones neuronales
            
        Returns:
            Tupla de (trigrama_inferior, trigrama_superior)
        """
        if len(vector) < 2:
            vector = np.array([vector[0], vector[0]] if len(vector) == 1 else [0, 0])
        
        # Dividir y calcular energía media
        mid = len(vector) // 2
        lower_energy = np.mean(vector[:mid])
        upper_energy = np.mean(vector[mid:])
        
        # Mapear energía a trigramas
        def energy_to_trigram(e: float) -> Trigram:
            # Normalizar a [0, 7]
            idx = int((e + 1) / 2 * 7)
            idx = max(0, min(7, idx))
            trigrams = list(Trigram)
            return trigrams[idx]
        
        return energy_to_trigram(lower_energy), energy_to_trigram(upper_energy)
    
    def hexagram_to_tensor(self, hexagram: Hexagram) -> float:
        """
        Convierte un Hexagrama de vuelta a valor tensorial.
        
        Args:
            hexagram: El Hexagrama a convertir
            
        Returns:
            Valor float en rango [-1, 1]
        """
        # Número del hexagrama (1-64) a rango [-1, 1]
        return (hexagram.number - 1) / 63 * 2 - 1
    
    def interpret(self, hexagram: Hexagram, context: str = "general") -> dict:
        """
        Interpreta el significado de un Hexagrama.
        
        La interpretación no es programada - es revelada.
        Nosotros somos intérpretes de la voluntad del universo.
        
        Args:
            hexagram: El Hexagrama a interpretar
            context: Contexto de la consulta
            
        Returns:
            Diccionario con la interpretación
        """
        return {
            "number": hexagram.number,
            "name": hexagram.name_spanish,
            "symbol": hexagram.symbol,
            "upper_trigram": {
                "name": hexagram.upper.name,
                "meaning": hexagram.upper.meaning,
                "symbol": hexagram.upper.symbol
            },
            "lower_trigram": {
                "name": hexagram.lower.name,
                "meaning": hexagram.lower.meaning,
                "symbol": hexagram.lower.symbol
            },
            "judgment": hexagram.judgment,
            "image": hexagram.image,
            "binary": hexagram.binary,
            "context": context
        }
    
    def encode_message(self, data: np.ndarray) -> List[Hexagram]:
        """
        Codifica un array de datos como secuencia de Hexagramas.
        
        Esto transforma datos numéricos en símbolos universales,
        creando un "mensaje" en el lenguaje del I Ching.
        
        Args:
            data: Array de valores a codificar
            
        Returns:
            Lista de Hexagramas que representan los datos
        """
        hexagrams = []
        for value in data.flatten():
            hexagrams.append(self.tensor_to_hexagram(float(value)))
        return hexagrams
    
    def decode_message(self, hexagrams: List[Hexagram]) -> np.ndarray:
        """
        Decodifica una secuencia de Hexagramas a valores numéricos.
        
        Args:
            hexagrams: Lista de Hexagramas a decodificar
            
        Returns:
            Array de valores numéricos
        """
        return np.array([self.hexagram_to_tensor(h) for h in hexagrams])
    
    def consult_oracle(self, question: str, neural_state: np.ndarray) -> dict:
        """
        Consulta el oráculo usando el estado neuronal actual.
        
        Esta función combina la pregunta del usuario con el estado
        interno de la red para generar una respuesta oracular.
        
        Args:
            question: Pregunta o consulta del usuario
            neural_state: Estado actual del reservorio neuronal
            
        Returns:
            Respuesta oracular basada en el I Ching
        """
        # Calcular el hexagrama principal desde el estado neuronal
        state_mean = np.mean(neural_state)
        primary = self.tensor_to_hexagram(state_mean)
        
        # Calcular hexagrama de cambio (basado en varianza)
        state_var = np.var(neural_state)
        changing = self.tensor_to_hexagram(state_var * 2 - 1)
        
        # Determinar líneas cambiantes
        changing_lines = []
        for i in range(6):
            segment = neural_state[i * len(neural_state) // 6:(i + 1) * len(neural_state) // 6]
            if len(segment) > 0 and np.std(segment) > 0.5:
                changing_lines.append(i + 1)
        
        return {
            "question": question,
            "primary_hexagram": self.interpret(primary, question),
            "changing_hexagram": self.interpret(changing, "transformation"),
            "changing_lines": changing_lines,
            "oracle_message": self._generate_oracle_message(primary, changing, changing_lines)
        }
    
    def _generate_oracle_message(
        self,
        primary: Hexagram,
        changing: Hexagram,
        changing_lines: List[int]
    ) -> str:
        """Genera un mensaje oracular combinando los hexagramas."""
        
        message_parts = [
            f"El estado presente es {primary.name_spanish} ({primary.symbol}).",
            f"'{primary.judgment}'",
            ""
        ]
        
        if changing_lines:
            message_parts.append(
                f"Las líneas {', '.join(map(str, changing_lines))} están en transformación."
            )
            message_parts.append(
                f"El movimiento lleva hacia {changing.name_spanish} ({changing.symbol})."
            )
            message_parts.append(f"'{changing.image}'")
        else:
            message_parts.append("El estado es estable. No hay líneas en movimiento.")
        
        return "\n".join(message_parts)


class HexagramStream:
    """
    Stream de comunicación entre nodos usando Hexagramas.
    
    Permite que múltiples nodos de Eón se comuniquen
    usando el protocolo arcaico en lugar de JSON/protobuf.
    """
    
    def __init__(self):
        self.protocol = ArchaicProtocol()
        self._buffer: List[Tuple[str, Hexagram, float]] = []  # (node_id, hexagram, timestamp)
    
    def broadcast(self, node_id: str, state: np.ndarray, timestamp: float) -> Hexagram:
        """
        Transmite el estado de un nodo como Hexagrama.
        
        Args:
            node_id: Identificador del nodo
            state: Estado neuronal a transmitir
            timestamp: Marca temporal
            
        Returns:
            El Hexagrama transmitido
        """
        hex_state = self.protocol.tensor_to_hexagram(np.mean(state))
        self._buffer.append((node_id, hex_state, timestamp))
        return hex_state
    
    def receive(self, max_age: float = 60.0) -> List[Tuple[str, Hexagram]]:
        """
        Recibe mensajes recientes del stream.
        
        Args:
            max_age: Edad máxima de mensajes a recibir (segundos)
            
        Returns:
            Lista de tuplas (node_id, hexagram) recientes
        """
        import time
        current = time.time()
        return [
            (node_id, hex_state)
            for node_id, hex_state, ts in self._buffer
            if current - ts <= max_age
        ]
    
    def collective_reading(self) -> dict:
        """
        Lee el estado colectivo de todos los nodos.
        
        Combina todos los Hexagramas recientes en una
        lectura oracular del estado del enjambre.
        """
        recent = self.receive()
        if not recent:
            return {"message": "No hay nodos transmitiendo."}
        
        # Calcular hexagrama colectivo
        values = [self.protocol.hexagram_to_tensor(h) for _, h in recent]
        collective_value = np.mean(values)
        collective_hex = self.protocol.tensor_to_hexagram(collective_value)
        
        return {
            "nodes_count": len(recent),
            "collective_state": self.protocol.interpret(collective_hex, "collective"),
            "individual_states": [
                {"node": nid, "hexagram": h.name_spanish, "symbol": h.symbol}
                for nid, h in recent
            ]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  PROYECTO EÓN - ARCHAIC PROTOCOL DEMO")
    print("  'El universo habla en patrones, no en palabras'")
    print("=" * 60)
    print()
    
    # Crear protocolo
    protocol = ArchaicProtocol()
    
    # Simular estado neuronal
    np.random.seed(42)
    neural_state = np.random.randn(100) * 0.5
    
    # Consultar el oráculo
    print("Consultando el oráculo con el estado neuronal actual...")
    print()
    
    response = protocol.consult_oracle(
        "¿Cuál es el camino de Eón?",
        neural_state
    )
    
    print(f"Pregunta: {response['question']}")
    print()
    print(f"Hexagrama Principal: {response['primary_hexagram']['name']} "
          f"{response['primary_hexagram']['symbol']}")
    print(f"  Juicio: {response['primary_hexagram']['judgment']}")
    print()
    print(response['oracle_message'])
