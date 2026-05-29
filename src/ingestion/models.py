"""Modelos SQLAlchemy de las tablas del reto. Columnas alineadas con el generador."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, Float, Integer, String

from src.ingestion.db import Base


class Asegurado(Base):
    __tablename__ = "asegurados"
    id_asegurado = Column(String, primary_key=True)
    segmento = Column(String)
    ciudad = Column(String)
    antiguedad_meses = Column(Integer)
    score_cliente = Column(Integer)
    telefono = Column(String)
    en_lista_restrictiva = Column(Boolean)
    numero_polizas = Column(Integer)
    reclamos_ultimos_12_meses = Column(Integer)
    mora_actual = Column(Boolean)


class Proveedor(Base):
    __tablename__ = "proveedores"
    id_proveedor = Column(String, primary_key=True)
    tipo = Column(String)
    ciudad = Column(String)
    antiguedad_meses = Column(Integer)
    en_lista_restrictiva = Column(Boolean)
    reclamos_asociados = Column(Integer)
    monto_promedio_reclamado = Column(Float)
    porcentaje_casos_observados = Column(Float)


class Poliza(Base):
    __tablename__ = "polizas"
    id_poliza = Column(String, primary_key=True)
    id_asegurado = Column(String, index=True)
    ramo = Column(String)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    prima = Column(Float)
    suma_asegurada = Column(Float)
    deducible = Column(Float)
    canal_venta = Column(String)
    ciudad = Column(String)
    estado_poliza = Column(String)


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    placa = Column(String, primary_key=True)
    chasis = Column(String)
    motor = Column(String)
    marca = Column(String)
    modelo = Column(String)
    anio = Column(Integer)
    id_asegurado = Column(String, index=True)
    id_poliza = Column(String, index=True)


class Siniestro(Base):
    __tablename__ = "siniestros"
    id_siniestro = Column(String, primary_key=True)
    id_poliza = Column(String, index=True)
    id_asegurado = Column(String, index=True)
    id_proveedor = Column(String, index=True)
    placa = Column(String)
    id_conductor = Column(String, index=True)
    ramo = Column(String)
    cobertura = Column(String)
    perdida_total = Column(Boolean)
    fecha_ocurrencia = Column(Date)
    fecha_reporte = Column(Date)
    monto_reclamado = Column(Float)
    monto_estimado = Column(Float)
    monto_pagado = Column(Float)
    estado = Column(String)
    sucursal = Column(String)
    descripcion = Column(String)
    documentos_completos = Column(Boolean)
    beneficiario_tipo = Column(String)
    hora_ocurrencia = Column(Integer)
    tipo_impacto = Column(String)
    tercero_identificado = Column(Boolean)
    ciudad_ocurrencia = Column(String)
    ciudad_taller = Column(String)
    clima_declarado = Column(String)
    clima_real = Column(String)
    patron = Column(String)
    etiqueta_fraude_simulada = Column(Integer)
    split = Column(String)
    dias_desde_inicio_poliza = Column(Integer)
    dias_desde_fin_poliza = Column(Integer)
    dias_entre_ocurrencia_reporte = Column(Integer)
    historial_siniestros_asegurado = Column(Integer)


class Documento(Base):
    __tablename__ = "documentos"
    id_documento = Column(String, primary_key=True)
    id_siniestro = Column(String, index=True)
    tipo_documento = Column(String)
    entregado = Column(Boolean)
    legible = Column(Boolean)
    fecha_emision = Column(Date)
    inconsistencia_detectada = Column(Boolean)
    observacion = Column(String)
