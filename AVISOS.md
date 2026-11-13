# AVISOS Y REGISTRO DE CAMBIOS TÉCNICOS — CARAMEL

Este documento detalla todas las modificaciones realizadas recientemente en la plataforma, las nuevas funcionalidades implementadas y la resolución del problema visual detectado en el perfil.

---

## 1. Formulario de Carga de Materiales (`/upload-material`)

### Lo que se solicitó:
* Que al pulsar el botón de la flecha (``) diga *"Reemplazarla por otra de tu trimestre"*.
* Que al hacer clic en la flecha **no abra ninguna lista ni modal**, sino que cambie instantáneamente a una materia aleatoria que no se encuentre presente entre las 3 opciones visibles.
* Eliminar la estructura fija del antiguo eje académico (*Programación I al IV, Estructura de Datos, Bases de Datos I y II*).

### Lo que se implementó:
1. **Tooltips y Textos Guía:**
   * El botón flotante de cada slot ahora tiene el atributo `title="Reemplazarla por otra de tu trimestre"`.
   * El subtítulo superior indica:  
     *«Haz clic en la materia deseada o pulsa la flecha () para reemplazarla por otra de tu trimestre.»*
2. **Reemplazo Aleatorio en 1 Clic (Sin Modales ni Listas):**
   * Se suprimió completamente el modal/drawer emergente, el buscador y las listas desplegables.
   * Se creó el método reactivo `replaceRandomSlot(index)` en Alpine.js:
     ```javascript
     replaceRandomSlot(index) {
       const currentNames = this.slots.map(s => s.nombre);
       let pool = this.materiasDeTuTrimestre.filter(m => !currentNames.includes(m.nombre));
       if (pool.length > 0) {
         const randomIndex = Math.floor(Math.random() * pool.length);
         this.slots[index] = { ...pool[randomIndex] };
       }
     }
     ```
   * Al hacer clic, toma el conjunto de asignaturas del trimestre del usuario en sesión y **excluye las 3 que ya están en pantalla**, eligiendo una al azar con animación de giro háptico.
3. **Eliminación del Eje Académico Fijo:**
   * Se retiró el pie de página que mencionaba el eje restringido de programación.
   * Se implementó el pénsum completo de **Ingeniería de Sistemas de UNIMAR** estructurado del 1º al 12º trimestre, cargando automáticamente el trimestre del estudiante autenticado (`userTrimestre`).

---

## 2. Personalización Arbitraria de Foto de Perfil (`/profile`)

### Lo que se solicitó:
* Darle la oportunidad al usuario de cambiar su foto de perfil de forma totalmente arbitraria para personalizar su experiencia universitaria.

### Lo que se implementó:
1. **Botón Flotante de Edición:**
   * En la tarjeta del perfil, el avatar cuenta con un botón flotante (`` / ``) y un enlace directo *«Cambiar foto de perfil»*.
2. **Modal con 3 Modalidades de Personalización:**
   * **Pestaña 1 (Pegar URL Arbitraria):** Permite ingresar cualquier enlace directo de imagen en Internet (Unsplash, Discord, GitHub, Pinterest, Google, etc.) con previsualización en vivo.
   * **Pestaña 2 (Subir Foto Local):** Permite cargar cualquier archivo (JPG, PNG o WebP) desde la computadora o teléfono móvil.
   * **Pestaña 3 (Avatares UNIMAR Tech):** 6 avatares preconfigurados con temáticas de ingeniería (Científica de Datos, Desarrollador, Especialista en Redes, etc.) para asignación inmediata en 1 clic.
3. **Nuevos Endpoints Backend en `app/routes/feed.py`:**
   * `POST /api/profile/set-avatar`: Actualiza la URL directa en el campo `avatar_url` del usuario en la base de datos.
   * `POST /api/profile/upload-avatar`: Recibe el archivo de imagen, lo valida (límite 10 MB, extensiones seguras), lo almacena en el directorio `/uploads/` y actualiza la sesión activa.

---

## 3. Módulo «Mi Showcase» (4 Materiales de Ingeniería)

### Lo que se solicitó:
* Poner la opción de exhibir como showcase los **4 materiales favoritos para la carrera de ingeniería**.
* Nombre exacto y obligatorio de la sección: **«Mi Showcase»**.

### Lo que se implementó:
1. **Diseño de las 4 Tarjetas:**
   * Se añadió la sección **Mi Showcase** justo debajo de las estadísticas de guardados/reseñas con la insignia *«4 Favoritos»*.
   * Renderiza 4 tarjetas en grid (`TOP #1`, `TOP #2`, `TOP #3`, `TOP #4`) con:
     * Portada HD del documento.
     * Título y autores.
     * Calificación promedio por estrellas.
     * Trimestre sugerido.
     * Enlace directo para abrir y leer el material.
2. **Personalización Interactiva:**
   * Botón `Personalizar` y botones de cambio rápido (``) en cada tarjeta.
   * Modal interactivo con buscador instantáneo para seleccionar cualquier documento del catálogo de ingeniería de UNIMAR y asignarlo al slot deseado.
3. **Persistencia en la Base de Datos:**
   * Se agregó la columna `showcase_ids` a la tabla `users` (y `usuarios`) en `caramel.db`.
   * Endpoint `POST /api/profile/update-showcase` que almacena los 4 IDs seleccionados y actualiza la vista reactivamente.

---

## 4. Diagnóstico y Corrección del Bug Visual

### ¿Qué causó el error que viste en pantalla?
* Al intentar incrustar el JSON de los documentos dentro del atributo HTML `x-data="..."`:
  ```html
  <!-- Causa del error -->
  <div x-data="{
     showcaseSlots: [ { title: {{ doc.title|tojson }} } ]
  }">
  ```
  El filtro `tojson` generaba comillas dobles (`"Cálculo..."`), lo que provocaba que el navegador interpretara la primera comilla como el **cierre del atributo HTML `x-data`**.
* Como consecuencia, el navegador expulsaba todo el resto del código JavaScript fuera de la etiqueta HTML y lo renderizaba en la pantalla como texto plano crudo.

### ¿Cómo se solucionó definitivamente?
* Se desacopló toda la lógica a una función pura de JavaScript dentro de una etiqueta `<script>` estándar:
  ```html
  <script>
  function profileApp() {
    return {
      // Estado de avatar, showcase, métodos y slots
    };
  }
  </script>

  <div class="space-y-6 pt-2 pb-10" x-data="profileApp()">
  ```
* Al estar dentro del bloque `<script>`, el analizador de HTML ya no entra en conflicto con las comillas del JSON.
* La vista se renderiza con 100% de limpieza visual, sin caracteres sueltos y con total reactividad en Alpine.js.

---

## Archivos Modificados:

| Archivo | Ruta | Descripción |
| :--- | :--- | :--- |
| **upload_material.html** | `app/templates/upload_material.html` | Reemplazo aleatorio en 1 clic de tu trimestre y eliminación del eje académico fijo. |
| **profile.html** | `app/templates/profile.html` | Sección **Mi Showcase** (4 tarjetas), modal de avatar arbitrario y encapsulación en `profileApp()`. |
| **feed.py** | `app/routes/feed.py` | Endpoints `/api/profile/set-avatar`, `/upload-avatar` y `/update-showcase`. |
| **models.py** | `app/models.py` | Definición del campo `showcase_ids` en `User` y `Usuario`. |
| **caramel.db** | `caramel.db` | Columna `showcase_ids` migrada en SQLite. |
| **BLUEPRINT_CARAMEL.md** | `BLUEPRINT_CARAMEL.md` | Especificación técnica actualizada de la plataforma. |
| **TAREAS_PENDIENTES.md** | `TAREAS_PENDIENTES.md` | Estado de las tareas completadas. |
| **AVISOS.md** | `AVISOS.md` | Este documento de aviso y auditoría técnica. |

---

## 5. Actualización de Paleta de Colores: Nueva Identidad Visual #7FB3A6 / #2F4A44

* **Objetivo:** Sustituir las familias cromáticas de acento por el tono `#7FB3A6` (tono salvia/verde agua armónico) y su ancla profunda `#2F4A44` (pino oscuro).
* **Estado:** Completado con éxito (12 de Noviembre de 2026).
* **Detalle de la Implementación:**
  1. `base.html`: Reconfiguración integral de las paletas `amber` y `yellow` en `tailwind.config` con la escala cromática:
     - `500: '#7FB3A6'` (tono primario equilibrado).
     - `400: '#8dbfae'` (iconos y acentos interactivos).
     - `300: '#9ecbc0'`, `200: '#bfddd6'`, `100: '#ddede9'`, `50: '#f0f7f5'` (fuentes de texto, badges y estados hover con contraste superior a 10:1).
     - `600: '#639589'`, `700: '#48736a'`, `800: '#2F4A44'` (tono profundo requerido), `900: '#203430'`, `950: '#13211e'`.
  2. `caramel.css`: Variables maestras `--caramel-accent: #7FB3A6`, `--caramel-glow: rgba(127, 179, 166, 0.25)` y clase `.text-caramel-glow`.
  3. `explore.html`: Píldoras de filtro activo con texto oscuro `text-stone-950 font-bold` sobre el fondo `#7FB3A6` para contraste WCAG AAA (8.14:1).
  4. `profile.html`: Botón flotante de foto, tabs de avatar, botón de guardar y selector de slots del showcase optimizados con texto oscuro de alto contraste.
  5. `feed.html`: Insignia de pendientes con perfecta nitidez visual.
  6. `app.js` y demás vistas: Estrellas de valoración, bordes activos y barras de progreso renderizadas armónicamente en el nuevo matiz.

---

## 6. Homologación de Lenguaje y Microinteracciones en `/upload-material`

* **Tagline en Español Institucional:** Sustituido el encabezado en inglés por:
  `SIN DESESPERO CASI INGENIERO` (con la palabra **INGENIERO** destacada en la paleta activa).
* **Pasos en Español:** Reemplazados los indicadores de paso por `PASO 1 DE 3`, `PASO 2 DE 3`, `PASO 3 DE 3` y `FINALIZADO`.
* **Animación Háptica 360° en Botón de Barajado:**
  * Al pulsar el botón de cambio aleatorio de cátedra, ejecuta un giro dinámico de 360° con elevación elástica (`scale-125`) y genera una micro-transición táctil en la tarjeta del slot.
* **Integración del Matiz Crema Cálido `#E6D4BA`:**
  * Incorporado en `tailwind.config` y CSS variables para metadatos, sinopsis, descripciones de cátedras y autores, garantizando legibilidad y calidez editorial (contraste 13.25:1).

---

## 7. Eliminación Total de Tonos Crema/Pastel en Estados Hover

* **Regla Visual Implementada:** Ningún elemento interactivo al pasar el cursor (`:hover`, `:focus`, `group-hover`) emitirá tonalidades crema o pastel.
* **Consolidación en `#7FB3A6`:** Todos los enlaces, bordes de tarjetas, títulos de catálogo, botones secundarios, pestañas y scrollbars adoptan exclusivamente el matiz `#7FB3A6` de la paleta activa:
  - Enlaces de retroceso y navegación secundaria (`hover:text-[#7FB3A6]`).
  - Bordes de tarjetas y dropzones en arrastre/hover (`hover:border-[#7FB3A6]`).
  - Títulos de libros en catálogo y showcase (`group-hover:text-[#7FB3A6]`).
  - Pulgar de scrollbar en el sistema (`::-webkit-scrollbar-thumb:hover { background: #7FB3A6; }`).
  - Botones secundarios (`.btn-caramel-secondary:hover { border-color: #7FB3A6; color: #7FB3A6; }`).
* **Pénsum Restringido al Eje de Programación:** Mapeado con exactitud desde el documento oficial UNIMAR (`pensumunimar.pdf`).

---

## 8. Mapeo del Eje de Programación (Pénsum UNIMAR) y Limpieza de UI

* **Eliminación Total de Textos Guía Obvios:** Se eliminó por completo el subtítulo explicativo *«Haz clic en la materia deseada o pulsa la flecha de intercambio...»* en el Paso 1 de `/upload-material`, dejando una tarjeta visualmente despejada y minimalista enfocada en la pregunta central.
* **Restricción Estricta al Eje de Programación y Sistemas:** Se descartaron todas las materias no afines (matemáticas generales, físicas, dibujos, humanidades) y se integraron formalmente las 14 asignaturas solicitadas con sus códigos oficiales y trimestres correspondientes:
  1. `Técnicas de Programación` (3º Trimestre — `TEP0304341`)
  2. `Programación I` (4º Trimestre — `PRO0405341`)
  3. `Programación II` (5º Trimestre — `PRO0505341`)
  4. `Estructura de Datos` (5º Trimestre — `ESD0504341`)
  5. `Programación III` (6º Trimestre — `PRO0605341`)
  6. `Sistemas I` (6º Trimestre — `SIS0605341`)
  7. `Base de Datos I` (6º Trimestre — `BAD0604341`)
  8. `Programación IV` (7º Trimestre — `PRO0705341`)
  9. `Sistemas II` (7º Trimestre — `SIS0705341`)
  10. `Base de Datos II` (7º Trimestre — `BAD0705341`)
  11. `Sistemas III` (8º Trimestre — `SIS0805341`)
  12. `Sistemas Operativos` (9º Trimestre — `SIO0904341`)
  13. `Sistemas de Información Gerencial` (9º Trimestre — `SIG0905341`)
  14. `Metodología de Desarrollo de Software` (10º Trimestre — `MDS1004241`)
* **Barajado Abierto en Todo el Eje de Programación:** Cada slot se inicializa recomendando las materias afines al trimestre del estudiante en sesión, pero al hacer clic en el botón de giro (spin 360°), el selector baraja libremente entre **todas las 14 asignaturas del eje de programación** de la carrera (`ejeProgramacion`), garantizando que nunca se dupliquen las 3 materias en pantalla ni se repita la que ya estaba en ese slot. Además, cada slot resalta con la insignia `• Tu Trimestre` si pertenece a la cohorte activa del estudiante.

---

## 9. Hardware Real en Vista Móvil y Preparación para Dominio/Hosting

* **Ocultación en Vista Escritorio:**
  - La barra superior simulada (`.mobile-status-bar`) queda **oculta por completo** en vista de escritorio (`body.view-desktop`), evitando duplicidad de relojes e iconos en pantallas de computadora.
* **Integración de Hardware Real en Móvil:**
  - **Reloj Dinámico del Dispositivo:** Eliminado el texto estático `9:41`. Se enlaza al reloj interno del sistema operativo (`new Date()`) actualizándose segundo a segundo.
  - **Batería Real del Dispositivo (Web Battery API):** Mediante `navigator.getBattery()`, detecta el porcentaje real de carga del teléfono o equipo, ajusta el nivel visual en la barra y despliega el icono de rayo cargando en tiempo real.
* **Persistencia de Usuarios para Producción:**
  - El sistema de registro en `/register` y autenticación en `/login` cuenta con hashing criptográfico `bcrypt`, vinculación a roles y guardado directo en la base de datos (compatible con SQLite y PostgreSQL / Supabase para despliegue en dominio y hosting público).

---

## 10. Diagnóstico y Corrección: Error al Cargar Paquetes ZIP

* **Causa Raíz:** En [documents.py](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/routes/documents.py), la función `upload_material_submit` accedía a `current_user.nombre_completo`. Como el modelo `User` en [models.py](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/models.py) nombraba ese campo `full_name`, se generaba un `AttributeError` en el servidor produciendo un código HTTP 500 no capturado. La respuesta de texto plano (*"Internal Server Error"*) rompía el parseo de JSON en el navegador y activaba el mensaje genérico *«Error de comunicación con el servidor. Revisa tu conexión a internet»*.
* **Solución Aplicada:**
  1. Se implementó la propiedad `@property def nombre_completo` en la clase `User` en `app/models.py` para compatibilidad universal.
  2. En `app/routes/documents.py`, se robusteció la asignación del autor usando `getattr(current_user, 'full_name', None) or getattr(current_user, 'nombre_completo', None)`.
  3. En [upload_material.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/upload_material.html), se aisló el parseo de JSON con bloque `try/catch` para reportar códigos HTTP de forma transparente.
  4. Se ejecutó una prueba funcional completa enviando un archivo `.zip` real vía HTTP multipart, verificando respuesta exitosa `HTTP 200` y guardado automático en el directorio `/uploads/` y en la base de datos.

---

## 11. Módulo de Inspección y Descarga en el Panel de Validación Docente

* **Objetivo:** Permitir que los profesores y curadores académicos evalúen exhaustivamente los recursos antes de aprobarlos en el catálogo.
* **Componentes Incorporados en [validation_panel.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/validation_panel.html):**
  1. **Archivos ZIP de Proyecto:**
     - Identificador visual con icono de paquete comprimido y título del archivo.
     - Botón directo **«Descargar Archivo ZIP»** con atributo HTML5 `download` que enlaza a la ruta estática `/uploads/{archivo}.zip`.
  2. **Documentos PDF y Guías:**
     - Botón **«Leer PDF»** que abre el documento en una pestaña nueva del navegador para inspección previa.
     - Botón **«Descargar»** para guardarlo localmente.
  3. **Videos y Clases Audiovisuales:**
     - Reproductor embebido de YouTube (`youtube-nocookie.com`) en formato panorámico (aspect-ratio 16:9).
     - Enlace de acceso rápido **«Abrir en YouTube ↗»**.
  4. **Trazabilidad del Aportador:**
     - Despliega el nombre del estudiante (`Oscar Alvarez`), carrera académica y trimestre cursado.

---

## 12. Protocolo de Comprobación Docente y Autorización Exclusiva del CEO

* **Objetivo:** Prevenir el acceso indiscriminado a funciones de curaduría y mantener el control riguroso de validación institucional sobre los recursos de la Universidad de Margarita.
* **Mecánica Implementada:**
  1. **Registro con Roles Privilegiados (`Docente de Cátedra` / `Curador` / `Administrador`):**
     - En [auth.py](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/routes/auth.py), los nuevos usuarios con `id_rol >= 2` se registran con `validado_por_ceo = 0` (estado pendiente).
     - El badge de **«VALIDAR»** permanece oculto hasta que el CEO verifique la identidad del usuario.
     - El acceso directo a `/validation-panel` queda protegido: si un docente no validado o estudiante intenta acceder por URL, es redirigido automáticamente.
  2. **Pop-Up Modal en el Menú Principal ([feed.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/feed.html)):**
     - Al ingresar al inicio, se despliega una ventana modal con fondo difuminado y el mensaje institucional requerido:
       *«Se está comprobando su identidad como especialista o preparador de las cátedras de la Universidad de Margarita dispuestas en este software, ¡aguante un pelo! Gracias sr. Docente {Nombre y Apellido}»*.
     - Permite cerrar para explorar el catálogo mientras espera la confirmación, dejando un botón de estado (*«Espera CEO»*) en la cabecera.
  3. **Módulo de Autorización para el CEO ([validation_panel.html](file:///C:/Users/Admin/Downloads/Caramel/Caramel-main/app/templates/validation_panel.html)):**
     - El CEO (**Oscar Alvarez**) cuenta con un panel exclusivo de **«Control CEO: Solicitudes Docentes»** en la parte superior del panel de validación.
     - Permite revisar los datos del solicitante y accionar con 1 clic **«Aprobar Docente ✓»** (habilita instantáneamente su badge de validación) o **«Reasignar a Alumno»**.
