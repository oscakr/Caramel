-- ==============================================================================
-- CARAMEL - PLATAFORMA ACADÉMICA Y MOTOR DE RECOMENDACIÓN (UNIMAR)
-- Esquema Oficial de Base de Datos para Supabase (PostgreSQL 15 en 3FN)
-- Conforme al Cuadro Nº 23: Diccionario de Datos del Modelo Entidad-Relación
-- ==============================================================================

-- 1. Habilitar extensión para identificadores UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Eliminar tablas previas en cascada si existen (para inicialización limpia)
DROP TABLE IF EXISTS valoraciones CASCADE;
DROP TABLE IF EXISTS revisiones_pares CASCADE;
DROP TABLE IF EXISTS archivos_codigo CASCADE;
DROP TABLE IF EXISTS proyectos CASCADE;
DROP TABLE IF EXISTS catedras CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- ==============================================================================
-- 2. TABLA: ROLES (Catálogo de roles institucionales)
-- ==============================================================================
CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE,
    permisos JSONB NOT NULL DEFAULT '{}'::jsonb
);

COMMENT ON TABLE roles IS 'Catálogo de roles jerárquicos conforme a ISO 21001 y políticas UNIMAR';

-- ==============================================================================
-- 3. TABLA: USUARIOS (Comunidad estudiantil y docente con correo @unimar.edu.ve)
-- ==============================================================================
CREATE TABLE usuarios (
    id_usuario UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_completo VARCHAR(150) NOT NULL,
    correo_institucional VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INTEGER NOT NULL REFERENCES roles(id_rol) ON UPDATE CASCADE ON DELETE RESTRICT,
    titulo_honorifico VARCHAR(50) DEFAULT 'Casi Ingeniero', -- 'Casi Ingeniero', 'Ingeniero', 'Profesor', 'Doctor'
    carrera VARCHAR(100) NOT NULL DEFAULT 'Ingeniería de Sistemas',
    trimestre INTEGER NOT NULL DEFAULT 3,
    avatar_url VARCHAR(255) DEFAULT 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
    puntos_reputacion INTEGER NOT NULL DEFAULT 0,
    fecha_registro TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_correo_unimar CHECK (correo_institucional LIKE '%@unimar.edu.ve')
);

CREATE INDEX idx_usuarios_correo ON usuarios(correo_institucional);
CREATE INDEX idx_usuarios_rol ON usuarios(id_rol);

-- ==============================================================================
-- 4. TABLA: CATEDRAS (Unidades curriculares del plan de estudio de UNIMAR)
-- ==============================================================================
CREATE TABLE catedras (
    id_catedra SERIAL PRIMARY KEY,
    codigo_materia VARCHAR(20) NOT NULL UNIQUE,
    nombre_catedra VARCHAR(100) NOT NULL,
    trimestre INTEGER NOT NULL CHECK (trimestre BETWEEN 1 AND 12)
);

CREATE INDEX idx_catedras_trimestre ON catedras(trimestre);

-- ==============================================================================
-- 5. TABLA: PROYECTOS / MATERIALES (Proyectos de software y material académico bajo Dublin Core)
-- ==============================================================================
CREATE TABLE proyectos (
    id_proyecto UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    id_autor UUID NOT NULL REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
    id_catedra INTEGER NOT NULL REFERENCES catedras(id_catedra) ON UPDATE CASCADE ON DELETE RESTRICT,
    lenguaje_principal VARCHAR(50) NOT NULL, -- Python, Java, C++, JS, SQL, etc.
    tipo_material VARCHAR(50) NOT NULL DEFAULT 'proyecto', -- 'proyecto', 'libro', 'video', 'guia'
    enlace_externo VARCHAR(350), -- Enlace opcional a video de YouTube, repositorio o drive
    cover_url VARCHAR(300) DEFAULT 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400',
    estado_curaduria VARCHAR(30) NOT NULL DEFAULT 'Pendiente', -- 'Pendiente', 'Aprobado', 'Destacado', 'Rechazado'
    id_validador UUID REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE SET NULL,
    fecha_publicacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_estado_curaduria CHECK (estado_curaduria IN ('Pendiente', 'Aprobado', 'Destacado', 'Rechazado'))
);

CREATE INDEX idx_proyectos_autor ON proyectos(id_autor);
CREATE INDEX idx_proyectos_catedra ON proyectos(id_catedra);
CREATE INDEX idx_proyectos_estado ON proyectos(estado_curaduria);

-- ==============================================================================
-- 6. TABLA: ARCHIVOS_CODIGO (Archivos y scripts de código fuente adjuntos)
-- ==============================================================================
CREATE TABLE archivos_codigo (
    id_archivo UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_proyecto UUID NOT NULL REFERENCES proyectos(id_proyecto) ON UPDATE CASCADE ON DELETE CASCADE,
    nombre_archivo VARCHAR(120) NOT NULL,
    extension VARCHAR(10) NOT NULL, -- .py, .java, .cpp, .js, .sql, .zip
    contenido_codigo TEXT,
    tamanio_bytes BIGINT NOT NULL,
    ruta_almacenamiento VARCHAR(255) NOT NULL,
    CONSTRAINT chk_extension_valida CHECK (extension IN ('.py', '.java', '.cpp', '.js', '.sql', '.zip', '.pdf', '.docx'))
);

CREATE INDEX idx_archivos_proyecto ON archivos_codigo(id_proyecto);

-- ==============================================================================
-- 7. TABLA: REVISIONES_PARES (Evaluación técnica, retroalimentación y sugerencias)
-- ==============================================================================
CREATE TABLE revisiones_pares (
    id_revision UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_proyecto UUID NOT NULL REFERENCES proyectos(id_proyecto) ON UPDATE CASCADE ON DELETE CASCADE,
    id_revisor UUID NOT NULL REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
    comentario_tecnico TEXT NOT NULL,
    calificacion_criterio INTEGER CHECK (calificacion_criterio BETWEEN 1 AND 5),
    linea_referencia INTEGER,
    fecha_revision TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_revisiones_proyecto ON revisiones_pares(id_proyecto);
CREATE INDEX idx_revisiones_revisor ON revisiones_pares(id_revisor);

-- ==============================================================================
-- 8. TABLA: VALORACIONES (Votación comunitaria de utilidad técnica: +1 / -1)
-- ==============================================================================
CREATE TABLE valoraciones (
    id_valoracion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_proyecto UUID NOT NULL REFERENCES proyectos(id_proyecto) ON UPDATE CASCADE ON DELETE CASCADE,
    id_usuario UUID NOT NULL REFERENCES usuarios(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
    tipo_voto SMALLINT NOT NULL CHECK (tipo_voto IN (-1, 1)),
    fecha_voto TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_valoracion_usuario_proyecto UNIQUE (id_proyecto, id_usuario)
);

CREATE INDEX idx_valoraciones_proyecto ON valoraciones(id_proyecto);

-- ==============================================================================
-- 9. DATOS SEMILLA INICIALES (ROLES, CÁTEDRAS, USUARIOS Y PROYECTOS BASE)
-- ==============================================================================

-- Roles oficiales
INSERT INTO roles (id_rol, nombre_rol, permisos) VALUES
(1, 'Estudiante', '{"can_read": true, "can_upload": true, "can_review": true}'::jsonb),
(2, 'Docente de Cátedra', '{"can_read": true, "can_upload": true, "can_review": true, "can_validate": true}'::jsonb),
(3, 'Curador/Administrador', '{"can_read": true, "can_upload": true, "can_review": true, "can_validate": true, "can_admin": true}'::jsonb),
(4, 'CEO', '{"can_read": true, "can_upload": true, "can_review": true, "can_validate": true, "can_admin": true, "is_ceo": true}'::jsonb);

-- Cátedras de Ingeniería de Sistemas en UNIMAR
INSERT INTO catedras (id_catedra, codigo_materia, nombre_catedra, trimestre) VALUES
(1, 'SIS-101', 'Algoritmos y Programación I', 1),
(2, 'MAT-102', 'Cálculo I', 1),
(3, 'SIS-201', 'Algoritmos y Programación II', 2),
(4, 'MAT-202', 'Cálculo II', 2),
(5, 'SIS-301', 'Estructuras de Datos', 3),
(6, 'SIS-302', 'Arquitectura del Computador', 3),
(7, 'SIS-401', 'Base de Datos I', 4),
(8, 'SIS-402', 'Sistemas Operativos', 4),
(9, 'SIS-501', 'Redes de Computadoras', 5),
(10, 'SIS-601', 'Ingeniería de Software', 6);

-- Usuarios institucionales con contraseñas seguras cifradas en bcrypt (password: 'password123')
INSERT INTO usuarios (id_usuario, nombre_completo, correo_institucional, password_hash, id_rol, titulo_honorifico, carrera, trimestre, avatar_url, puntos_reputacion) VALUES
('11111111-1111-1111-1111-111111111111', 'Oscar Álvarez', 'oalvarez.7305@unimar.edu.ve', '$2b$12$7j7L/yXQV7sR1MGz8cPgWewTtqtcLAYpOilPYK4DvZLMnIqFJ3JgK', 4, 'Casi Ingeniero', 'Ingeniería de Sistemas', 3, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 120),
('77777777-7777-7777-7777-777777777777', 'Ing. Flavio Rosales', 'flavio.rosales@unimar.edu.ve', '$2b$12$7j7L/yXQV7sR1MGz8cPgWewTtqtcLAYpOilPYK4DvZLMnIqFJ3JgK', 2, 'Ingeniero', 'Ingeniería de Sistemas', 0, 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150', 500),
('88888888-8888-8888-8888-888888888888', 'Dra. Elena Mendoza', 'elena.mendoza@unimar.edu.ve', '$2b$12$7j7L/yXQV7sR1MGz8cPgWewTtqtcLAYpOilPYK4DvZLMnIqFJ3JgK', 3, 'Doctora', 'Decanato de Ingeniería', 0, 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150', 1000);

-- Proyectos aprobados de ejemplo inicial
INSERT INTO proyectos (id_proyecto, titulo, descripcion, id_autor, id_catedra, lenguaje_principal, tipo_material, enlace_externo, estado_curaduria, fecha_publicacion) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Implementación de Árboles AVL y Rotaciones Balanceadas', 'Estructura de datos en C++ con rotaciones simples y dobles para balanceo dinámico de índices en memoria.', '11111111-1111-1111-1111-111111111111', 5, 'C++', 'proyecto', 'https://github.com/unimar/arboles-avl', 'Aprobado', NOW()),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Video Explicativo: Transformaciones Lineales y Matrices', 'Clase magistral grabada sobre valores y vectores propios aplicados a gráficos por computadora.', '77777777-7777-7777-7777-777777777777', 4, 'Python', 'video', 'https://www.youtube.com/watch?v=fNk_zzaMoSs', 'Aprobado', NOW()),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Diseño de Motor Relacional y Optimización de Consultas SQL', 'Modelo en 3FN con procedimientos almacenados, índices B-Tree y plan de ejecución optimizado.', '22222222-2222-2222-2222-222222222222', 7, 'SQL', 'proyecto', 'https://github.com/unimar/sql-engine', 'Aprobado', NOW());

-- Archivo de código asociado al proyecto AVL
INSERT INTO archivos_codigo (id_archivo, id_proyecto, nombre_archivo, extension, contenido_codigo, tamanio_bytes, ruta_almacenamiento) VALUES
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'avl_tree.cpp', '.cpp', 
'#include <iostream>\nusing namespace std;\n\nstruct Node {\n    int key;\n    Node *left, *right;\n    int height;\n};\n\nint height(Node *N) {\n    return (N == nullptr) ? 0 : N->height;\n}\n\nint main() {\n    cout << "Arbol AVL UNIMAR Inicializado" << endl;\n    return 0;\n}', 
254, '/storage/proyectos/avl_tree.cpp');

-- Revisión de pares técnica del Prof. Flavio
INSERT INTO revisiones_pares (id_revision, id_proyecto, id_revisor, comentario_tecnico, calificacion_criterio, linea_referencia) VALUES
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '77777777-7777-7777-7777-777777777777', 'Excelente implementación del algoritmo de rebalanceo de Adelson-Velsky y Landis. Cumple con la complejidad O(log n).', 5, 12);

-- Valoraciones comunitarias
INSERT INTO valoraciones (id_valoracion, id_proyecto, id_usuario, tipo_voto) VALUES
('ffffffff-ffff-ffff-ffff-ffffffffffff', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '33333333-3333-3333-3333-333333333333', 1),
('ffffffff-ffff-ffff-ffff-ffffffffffee', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222', 1);
