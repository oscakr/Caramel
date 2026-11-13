# Tareas Pendientes y Hoja de Ruta - Plataforma Caramel (UNIMAR)

**Proyecto:** Plataforma Caramel - Sistema de Recomendación de Documentos Académicos  
**Institución:** Universidad de Margarita (UNIMAR) - Decanato de Ingeniería  
**Estudiante / CEO:** Oscar Alvarez (`oalvarez.7305@unimar.edu.ve`)  
**Base de Datos:** Supabase PostgreSQL Cloud (AWS `us-west-2` activo 24/7)  
**Última actualización:** 11 de Noviembre de 2026  

---

## Índice de Contenido
1. [Subida de Materiales de Estudio Reales](#1-subida-de-materiales-de-estudio-reales)
2. [Modificación y Dinamismo del Formulario de Aportes](#2-modificación-y-dinamismo-del-formulario-de-aportes)
3. [Fase de Pruebas Operativas con Compañeros](#3-fase-de-pruebas-operativas-con-compañeros)
4. [Validación Docente y Curaduría Académica](#4-validación-docente-y-curaduría-académica)
5. [Métricas y Validación para el Tomo de Tesis (Capítulos IV y V)](#5-métricas-y-validación-para-el-tomo-de-tesis-capítulos-iv-y-v)
6. [Próxima Actualización Estética: Sustitución de Tonos Amarillos por Marrón](#6-próxima-actualización-estética-sustitución-de-tonos-amarillos-por-marrón)

---

## 1. Subida de Materiales de Estudio Reales

Actualmente la plataforma cuenta con 10 libros base indexados. Para incorporar el material oficial que usan los profesores y estudiantes de UNIMAR, se debe seguir este procedimiento:

### A. Almacenamiento y Hospedaje de Archivos
* **Archivos PDF y Guías de Estudio:**
  * Alojar los archivos pesados (PDFs de más de 10 MB) en Google Drive Institucional UNIMAR, OneDrive o en un Bucket de almacenamiento en **Supabase Storage** (creando un bucket público llamado `materiales-academicos`).
  * Configurar el enlace como público (*"Cualquiera con el enlace puede ver"*).
* **Clases Grabadas y Videos Explicativos:**
  * Subir las clases a YouTube en modo *Oculto (Unlisted)* o *Público*.
  * Caramel detecta automáticamente URLs de YouTube y las renderiza como reproductores incrustados sin publicidad.
* **Proyectos y Archivos de Código (Cuadro Nº 23):**
  * Alojar en repositorios de GitHub o pegar el código fuente directamente en el sistema para asociarlo a la tabla `ARCHIVOS_CODIGO`.

### B. Proceso de Indexación para el Algoritmo
Para que el motor híbrido (`TF-IDF` + `Filtrado Curricular`) recomiende con precisión, cada material nuevo debe registrarse con los siguientes metadatos:
1. **Título Académico Preciso:** Nombre exacto del libro o guía (ej. *Guía de Ejercicios Prácticos: Árboles AVL y Grafos*).
2. **Autor o Profesor Expositor:** Nombre del profesor de UNIMAR o autor del texto (ej. *Ing. Flavio Rosales* o *James Stewart*).
3. **Cátedra Oficial:** Asignatura exacta de la carrera (ej. `SIS-301 Estructuras de Datos`).
4. **Trimestre Sugerido:** Del 1 al 12 según el plan de estudios.
5. **Etiquetas Temáticas (Tags):** Palabras clave separadas por comas (ej. `c++, algoritmos, memoria dinámica, apuntadores, árboles binarios`).
6. **Sinopsis / Descripción Pedagógica:** Breve resumen de 2 o 3 líneas explicando qué competencias desarrollará el alumno al estudiar este recurso.

---

## 2. Modificación y Dinamismo del Formulario de Aportes

El formulario de aportes (`/upload-material`) fue perfeccionado siguiendo la premisa **"ONE QUESTION AT A TIME"**:

### Mejoras Completadas:
- [x] **Selector Ágil de Cátedras Adaptado a tu Trimestre (Paso 1):**
  * Catálogo oficial organizado curricularmente por trimestres para UNIMAR Ingeniería de Sistemas.
  * 3 botones táctiles principales con sustitución aleatoria en 1 clic (``): cambia la cátedra por otra de tu trimestre que no se encuentre actualmente visible entre las 3 opciones, sin abrir ventanas modales.
- [x] **Eliminación de Casillas Redundantes (Paso 3):**
  * Título asignado automáticamente con el nombre de la cátedra seleccionada (el docente en su panel define el tema específico en el plan de evaluación).
  * Aportador vinculado automáticamente desde la sesión institucional activa del usuario.
- [x] **Validación Preventiva de Duplicados en Vivo:**
  * Alerta instantánea en caso de intentar subir un video de YouTube ya existente: *`¡El video que intentas aprobar ya fue validado anteriormente, más atento Casi Ingeniero!`*
- [x] **Carga Local de Archivos con Límite de 30 MB:**
  * Dropzones optimizados para PDF y paquetes comprimidos ZIP con cálculo dinámico de peso en MB y validación de tipos MIME.

---

## 3. Fase de Pruebas Operativas con Compañeros

Para que tus compañeros prueben la plataforma y generen la data real de interacción:

- [ ] **Alta de Cuentas Estudiantiles:**
  * *Opción Directa:* Enviarles el enlace `/register` para que creen su cuenta con su correo institucional `@unimar.edu.ve`.
  * *Opción en Lote:* Ejecutar un script para cargar masivamente las cuentas con nombre, correo y una contraseña inicial común (ej. `unimar2026`).
- [ ] **Conexión de Red para Pruebas Externas:**
  * *Red Local (Mismo WiFi):* Conectarse mediante la IP local: `http://192.168.11.21:8001`.
  * *Fuera de la Red (Casas de los compañeros):* Levantar un túnel seguro con **Cloudflare Tunnel** (`cloudflared tunnel`) o desplegar el frontend en la nube (Render o Railway) conectado al Supabase actual.
- [ ] **Dinámica de Prueba Asignada a los Alumnos:**
  * Cada compañero debe ingresar, explorar el catálogo de su trimestre, guardar materiales en favoritos, leer y publicar al menos 2 o 3 valoraciones sinceras (estrellas del 1 al 5 y comentarios).

---

## 4. Validación Docente y Curaduría Académica

Garantizar el cumplimiento del ciclo de curaduría pedagógica exigido por la norma ISO 21001:

- [x] **Módulo de Inspección y Descarga de Contenidos (12 de Noviembre de 2026):**
  * Implementado en [validation_panel.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/validation_panel.html).
  * **Descarga de ZIP:** Botón directo para descargar paquetes `.zip` de código fuente (`download` attribute).
  * **Lectura y Descarga de PDF:** Botones independientes para previsualizar («Leer PDF» en pestaña nueva) y «Descargar».
  * **Reproductor de Video:** Embebido directo de clases de YouTube (`youtube-nocookie.com`) con enlace alternativo a YouTube.
  * **Ficha del Estudiante:** Identificación de nombre completo, carrera y trimestre del estudiante que aportó el material.
- [x] **Comprobación de Identidad Docente y Autorización Exclusiva del CEO (12 de Noviembre de 2026):**
  * Toda cuenta nueva registrada como docente, curador o administrador inicia bloqueada para validaciones (`validado_por_ceo = 0`).
  * Despliegue de ventana emergente (pop-up modal) en el menú principal con el mensaje de espera requerido y saludo personalizado por nombre y apellido.
  * Ocultación del badge «VALIDAR» y protección estricta de rutas contra acceso no autorizado.
  * Panel de control exclusivo para el CEO (**Oscar Alvarez**) en `/validation-panel` para aprobar o reasignar docentes con 1 clic.
- [ ] **Pruebas con Docentes:**
  * Acceso de prueba para el **Prof. Flavio Rosales** (`flavio.rosales@unimar.edu.ve`, Docente de Cátedra).
  * Acceso para la **Dra. Elena Mendoza** (`elena.mendoza@unimar.edu.ve`, Curador/Administrador).
- [ ] **Aprobación de Recursos:**
  * Los recursos subidos por estudiantes entran en estado `"pendiente"`.
  * El profesor ingresa al `/validation-panel`, revisa el material propuesto y lo aprueba con 1 clic para que aparezca oficialmente en el feed público.

---

## 5. Métricas y Validación para el Tomo de Tesis (Capítulos IV y V)

Para sustentar la tesis con rigor científico y metodológico ante el jurado evaluador:

- [ ] **Script de Exportación de Resultados:**
  * Desarrollar un script en Python que extraiga de Supabase:
    * Total de valoraciones reales recopiladas.
    * Promedio de estrellas por cátedra y por tipo de material.
    * Distribución de actividad por trimestre.
    * Generación automática de archivo CSV/Excel listo para graficar.
- [ ] **Métricas del Algoritmo de Recomendación:**
  * Calcular y registrar en tablas formales:
    * **Precision@K:** Porcentaje de recomendaciones relevantes entre los primeros 5 sugeridos.
    * **Recall@K:** Capacidad del algoritmo de encontrar todos los materiales afines al estudiante.
    * **Tiempo medio de respuesta (latencia):** Demostrar que el algoritmo procesa el modelo híbrido en menos de 200 ms.
- [ ] **Encuesta de Satisfacción y Usabilidad (Cuestionario SUS / TAM):**
  * Aplicar a los compañeros evaluadores una breve encuesta de 5 a 10 preguntas:
    1. *¿Las recomendaciones del feed fueron acordes a las materias que estás cursando?*
    2. *¿La interfaz visual fue clara, intuitiva y fácil de usar?*
    3. *¿Consideras útil que se distinga el material aprobado por docentes?*
    4. *¿Qué tan rápido encontraste material relevante para tus asignaturas?*
    5. *¿Recomendarías Caramel como plataforma oficial de estudio en UNIMAR?*

---

## 6. Actualización Estética: Sustitución de Tonos por la Paleta #7FB3A6 / #2F4A44

- [x] **Migración de Familias Cromáticas al Tono #7FB3A6 (Base) y #2F4A44 (Sombra):**
  * **Estado:** Completado el 12 de Noviembre de 2026.
  * **Código HEX Primario:** `#7FB3A6` (Verde agua / salvia sofisticado y sereno).
  * **Código HEX Profundo:** `#2F4A44` (Tono pino / bosque profundo de anclaje armónico).
  * **Alcance aplicado:**
    * Familias cromáticas `amber` y `yellow` reconfiguradas en `tailwind.config` dentro de [base.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/base.html) con la escala: 50 (`#f0f7f5`), 100 (`#ddede9`), 200 (`#bfddd6`), 300 (`#9ecbc0`), 400 (`#8dbfae`), 500 (`#7FB3A6`), 600 (`#639589`), 700 (`#48736a`), 800 (`#2F4A44`), 900 (`#203430`), 950 (`#13211e`).
    * Variables maestras de [caramel.css](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/static/css/caramel.css) actualizadas (`--caramel-accent: #7FB3A6`, `--caramel-glow: rgba(127, 179, 166, 0.25)`, `.text-caramel-glow`).
    * Contraste y legibilidad WCAG AAA asegurados en toda la UI: botones activos con texto oscuro `text-stone-950` sobre `#7FB3A6` (contraste 8.14:1) y textos/iconos nítidos sobre fondos oscuros.
    * Estrellas de valoración ([app.js](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/static/js/app.js)), insignias, barras de progreso y bordes activos perfectamente sincronizados.
- [x] **Consolidación de Estados Hover y Microinteracciones (12 de Noviembre de 2026):**
  * Eliminación total de tonos crema/pastel en interacciones con el mouse.
  * Todos los estados `:hover`, `group-hover` y `focus` consolidados en `#7FB3A6` (enlaces, tarjetas, botones secundarios, tabs y pulgar de scrollbar).
  * Inclusión del matiz crema cálido `#E6D4BA` únicamente para subtextos y metadatos estáticos de lectura.
  * Tagline e indicadores de paso de `/upload-material` homologados al español: *«SIN DESESPERO CASI INGENIERO»*, *«PASO 1 DE 3»*, etc.
  * Animación dinámica de 360° en el botón de reemplazo aleatorio de cátedra.
- [x] **Restricción Curricular al Eje de Programación en `/upload-material` (12 de Noviembre de 2026):**
  * Extraído de `pensumunimar.pdf` de Ingeniería de Sistemas de UNIMAR.
  * Catálogo restringido exclusivamente a las 14 asignaturas solicitadas: `Técnicas de Programación` (3º), `Programación I` (4º), `Programación II` (5º), `Estructura de Datos` (5º), `Programación III` (6º), `Sistemas I` (6º), `Base de Datos I` (6º), `Programación IV` (7º), `Sistemas II` (7º), `Base de Datos II` (7º), `Sistemas III` (8º), `Sistemas Operativos` (9º), `Sistemas de Información Gerencial` (9º) y `Metodología de Desarrollo de Software` (10º).
  * Eliminado el texto redundante de instrucciones en el Paso 1 para un diseño minimalista y limpio.

- [x] **Integración de Hardware Real y Preparación Online (12 de Noviembre de 2026):**
  * Barra superior de status oculta en vista de escritorio (`body.view-desktop`).
  * Reloj en vivo sincronizado con el sistema operativo del teléfono/dispositivo.
  * Batería real del equipo leída mediante Web Battery API (`navigator.getBattery`) con nivel porcentual dinámico e indicador de carga.
  * Preparación de base de datos y registro de usuarios en `/register` lista para despliegue en dominio y hosting público.

- [x] **Corrección de Carga de Archivos ZIP y Manejo de Respuestas (12 de Noviembre de 2026):**
  * Solucionado el fallo interno al acceder al nombre del autor en la sesión activa (`full_name` vs `nombre_completo`).
  * Validación integral de paquetes `.zip` (extensión, tamaño máximo 30 MB y almacenamiento seguro en `/uploads/`).
  * Verificado con respuesta `HTTP 200` y registro inmediato en la base de datos `caramel.db`.

---

## Comandos Rápidos del Proyecto

| Acción | Comando |
| :--- | :--- |
| **Iniciar servidor (terminal)** | `caramel` o `./run.sh` |
| **Iniciar en segundo plano** | `caramel start` |
| **Detener el servidor** | `caramel stop` |
| **Verificar estado** | `caramel status` |
| **URL local de Login** | `http://localhost:8001/login` |
| **URL para compañeros en WiFi** | `http://192.168.11.21:8001/login` |
