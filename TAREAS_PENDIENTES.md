# 📋 Tareas Pendientes y Hoja de Ruta - Plataforma Caramel (UNIMAR)

**Proyecto:** Plataforma Caramel - Sistema de Recomendación de Documentos Académicos  
**Institución:** Universidad de Margarita (UNIMAR) - Decanato de Ingeniería  
**Estudiante / CEO:** Oscar Álvarez (`oalvarez.7305@unimar.edu.ve`)  
**Base de Datos:** Supabase PostgreSQL Cloud (AWS `us-west-2` activo 24/7)  
**Última actualización:** 11 de Noviembre de 2026  

---

## 📌 Índice de Contenido
1. [Subida de Materiales de Estudio Reales](#1-subida-de-materiales-de-estudio-reales)
2. [Modificación y Dinamismo del Formulario de Aportes](#2-modificación-y-dinamismo-del-formulario-de-aportes)
3. [Fase de Pruebas Operativas con Compañeros](#3-fase-de-pruebas-operativas-con-compañeros)
4. [Validación Docente y Curaduría Académica](#4-validación-docente-y-curaduría-académica)
5. [Métricas y Validación para el Tomo de Tesis (Capítulos IV y V)](#5-métricas-y-validación-para-el-tomo-de-tesis-capítulos-iv-y-v)

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
- [x] **Selector Ágil de Cátedras del Eje de Programación (Paso 1):**
  * Catálogo oficial enfocado estrictamente en las 7 materias troncales de desarrollo: *Programación I, II, III y IV, Estructura de Datos, Bases de Datos I y II*.
  * 3 botones táctiles principales con selector dinámico *smooth* (`⇄`) y buscador instantáneo para alternar materias sin recargar.
- [x] **Eliminación de Casillas Redundantes (Paso 3):**
  * Título asignado automáticamente con el nombre de la cátedra seleccionada (el docente en su panel define el tema específico en el plan de evaluación).
  * Aportador vinculado automáticamente desde la sesión institucional activa del usuario.
- [x] **Validación Preventiva de Duplicados en Vivo:**
  * Alerta instantánea en caso de intentar subir un video de YouTube ya existente: *`⚠️ ¡El video que intentas aprobar ya fue validado anteriormente, más atento Casi Ingeniero!`*
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

## 🚀 Comandos Rápidos del Proyecto

| Acción | Comando |
| :--- | :--- |
| **Iniciar servidor (terminal)** | `caramel` o `./run.sh` |
| **Iniciar en segundo plano** | `caramel start` |
| **Detener el servidor** | `caramel stop` |
| **Verificar estado** | `caramel status` |
| **URL local de Login** | `http://localhost:8001/login` |
| **URL para compañeros en WiFi** | `http://192.168.11.21:8001/login` |
