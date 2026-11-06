#!/usr/bin/env python3
"""
Script de verificación de conexión y tablas oficiales en Supabase (PostgreSQL).
Verifica las 7 tablas del Cuadro Nº 23 de la Tesis UNIMAR.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or "sqlite" in DATABASE_URL:
    print("❌ No se detectó una DATABASE_URL de Supabase/PostgreSQL en el archivo .env")
    print("   Por favor coloca en tu archivo .env:")
    print("   DATABASE_URL=postgresql://postgres.xxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    from sqlalchemy import create_engine, inspect, text
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    with engine.connect() as conn:
        print("✅ ¡Conexión exitosa a Supabase (PostgreSQL)!")
        
        # Verificar versión de PostgreSQL
        version = conn.execute(text("SELECT version();")).scalar()
        print(f"📦 Motor: {version.split(',')[0]}")
        
        # Inspeccionar tablas existentes
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "roles", 
            "usuarios", 
            "catedras", 
            "proyectos", 
            "archivos_codigo", 
            "revisiones_pares", 
            "valoraciones"
        ]
        
        print("\n📋 Verificando las 7 tablas oficiales del Cuadro Nº 23:")
        all_found = True
        for t in expected_tables:
            if t in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {t};")).scalar()
                print(f"   ✓ {t.upper().ljust(18)} : {count} registros")
            else:
                print(f"   ✗ {t.upper().ljust(18)} : NO ENCONTRADA")
                all_found = False
                
        if all_found:
            print("\n🎉 ¡Todas las tablas del modelo de datos de la tesis existen y están operativas en Supabase!")
        else:
            print("\n⚠️ Algunas tablas faltan. Puedes crearlas ejecutando el archivo 'supabase_schema.sql' en el SQL Editor de Supabase.")

except Exception as e:
    print(f"❌ Error al conectar con Supabase: {e}")
    sys.exit(1)
