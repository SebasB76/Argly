"""Configuración central de Argly: rutas, catálogos de negocio y umbrales."""
from __future__ import annotations

from pathlib import Path

# --- Rutas ---
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

SEED = 42

# --- Ciudades de Ecuador con coordenadas (lat, lng) para señales geográficas ---
CIUDADES = {
    "Quito": (-0.180, -78.467),
    "Guayaquil": (-2.170, -79.922),
    "Cuenca": (-2.900, -79.005),
    "Ambato": (-1.241, -78.620),
    "Manta": (-0.967, -80.709),
    "Machala": (-3.258, -79.960),
    "Loja": (-3.993, -79.204),
    "Santo Domingo": (-0.253, -79.175),
    "Portoviejo": (-1.055, -80.455),
    "Riobamba": (-1.664, -78.654),
}

# --- Catálogos de negocio ---
RAMOS = ["Vehículos", "Salud", "Vida", "Generales", "Hogar"]
COBERTURAS = {
    "Vehículos": ["Choque", "Robo", "Pérdida Total", "Daño a Terceros (RC)"],
    "Salud": ["Atención Médica"],
    "Vida": ["Fallecimiento"],
    "Generales": ["Daño", "Incendio"],
    "Hogar": ["Incendio", "Robo", "Daño"],
}
ESTADOS = ["Reserva", "Pago Total", "Pago Parcial", "Anticipo",
           "Negativa", "Cierre Sin Consecuencia", "Liquidado"]
TIPOS_PROVEEDOR = ["Taller", "Clínica", "Perito", "Concesionario", "Abogado"]
SEGMENTOS = ["Masivo", "Preferente", "Corporativo", "Pyme"]
CANALES_VENTA = ["Agente", "Bróker", "Digital", "Sucursal", "Call Center"]

# --- Umbrales de semáforo (sección 13 del reto) ---
UMBRAL_VERDE = 40       # 0-40 verde
UMBRAL_AMARILLO = 75    # 41-75 amarillo ; 76-100 rojo


def clasificar_riesgo(score: float) -> str:
    """Convierte un score 0-100 en el nivel del semáforo."""
    if score <= UMBRAL_VERDE:
        return "VERDE"
    if score <= UMBRAL_AMARILLO:
        return "AMARILLO"
    return "ROJO"
