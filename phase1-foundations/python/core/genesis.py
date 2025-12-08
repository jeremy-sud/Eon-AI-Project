"""
Proyecto Eón - Genesis: Momento Cero
=====================================

El Momento Cero es el timestamp UNICO e INMUTABLE del nacimiento del
Proyecto Eón. No es por usuario, no es por sesión, no es por instancia.

Solo hay UN Eón. Este archivo lee el certificado de nacimiento que fue
establecido una única vez en GENESIS.json en la raíz del proyecto.

"La inteligencia no se crea, se descubre."
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Ruta al certificado de nacimiento (en la raíz del proyecto)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GENESIS_FILE = PROJECT_ROOT / "GENESIS.json"


class Genesis:
    """
    Singleton que representa el Momento Cero del Proyecto Eón.
    
    Solo hay UNA instancia de Eón. El timestamp de nacimiento es inmutable
    y fue establecido una única vez cuando se creó el proyecto.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if Genesis._initialized:
            return
        
        if not GENESIS_FILE.exists():
            raise RuntimeError(
                f"GENESIS.json no encontrado en {GENESIS_FILE}. "
                "El Momento Cero debe existir en la raíz del proyecto."
            )
        
        with open(GENESIS_FILE, 'r') as f:
            self._data = json.load(f)
        
        # Parsear timestamp
        self._birth_timestamp = datetime.fromisoformat(
            self._data['birth_timestamp'].replace('+00:00', '')
        )
        
        Genesis._initialized = True
    
    @property
    def birth_timestamp(self) -> datetime:
        """El momento exacto en que Eón nació (inmutable)."""
        return self._birth_timestamp
    
    @property
    def birth_hash(self) -> str:
        """Hash único del nacimiento de Eón."""
        return self._data['birth_hash']
    
    @property
    def age_seconds(self) -> float:
        """Edad de Eón en segundos desde su nacimiento."""
        from datetime import timezone
        return (datetime.now(timezone.utc).replace(tzinfo=None) - self._birth_timestamp).total_seconds()
    
    @property
    def age_days(self) -> float:
        """Edad de Eón en días."""
        return self.age_seconds / 86400
    
    @property
    def age_formatted(self) -> str:
        """Edad formateada de manera legible."""
        seconds = self.age_seconds
        
        if seconds < 60:
            return f"{seconds:.1f} segundos"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutos"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} horas"
        else:
            return f"{seconds/86400:.1f} días"
    
    def status(self) -> dict:
        """Estado actual del Momento Cero (solo lectura)."""
        return {
            "birth_timestamp": self._data['birth_timestamp'],
            "birth_hash": self.birth_hash,
            "age": self.age_formatted,
            "age_seconds": self.age_seconds,
            "version": self._data.get('version', '1.0.0'),
            "philosophy": self._data.get('philosophy', '')
        }
    
    def __repr__(self):
        return f"<Genesis born={self._data['birth_timestamp']} age={self.age_formatted}>"


# Instancia global (Singleton)
def get_genesis() -> Genesis:
    """
    Obtiene la instancia única de Genesis.
    
    Uso:
        from core.genesis import get_genesis
        genesis = get_genesis()
        print(genesis.birth_hash)  # Hash único
        print(genesis.age_formatted)  # "X días"
    """
    return Genesis()


# Demo
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║             PROYECTO EÓN - MOMENTO CERO                       ║
║         "La inteligencia no se crea, se descubre."            ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    genesis = get_genesis()
    
    print(f"  Nacimiento: {genesis.birth_timestamp}")
    print(f"  Hash:       {genesis.birth_hash}")
    print(f"  Edad:       {genesis.age_formatted}")
    print()
    print("  Estado completo:")
    for key, value in genesis.status().items():
        print(f"    • {key}: {value}")
    print()
    print("  ✓ Solo hay UN Eón. El Momento Cero es inmutable.")
    print()
