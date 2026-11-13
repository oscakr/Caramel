# Requerimientos y Especificaciones Técnicas - Plataforma Web Colaborativa (Caramel - UNIMAR)

> **Documento fuente:** `PROMPTexcelenciatesisCARAMEL.docx`  
> **Universidad:** Universidad de Margarita (UNIMAR) - Decanato de Ingeniería y Afines  
> **Área:** Gestión del Capital Intelectual en el Eje de Programación  

---

Corrobora que el andamiaje sociocognitivo de Vygotsky (1978), la preservación de activos de software (Surco Salinas, 2023) y el capital intelectual de educación superior (Escorcia y Barros, 2020) encuentra en la plataforma web colaborativa su vehículo de materialización técnica por excelencia.

4.2. Requerimientos funcionales y no funcionales de la plataforma web colaborativa para la gestión del capital intelectual en el eje de programación.

El segundo objetivo de la presente investigación reside en la determinación rigurosa de los requerimientos funcionales y no funcionales de la plataforma web colaborativa. Para alcanzar esta meta metodológica, se sistematizaron los aportes conceptuales, normativos y técnicos obtenidos de la Guía de Entrevista Semiestructurada aplicada a los informantes clave del decanato, con especial énfasis en el dictamen del Ing. Flavio Rosales Serrano, Decano de Ingeniería y Afines de la UNIMAR. El análisis de contenido se estructuró en torno a los cinco (5) bloques temáticos del instrumento:

1. Arquitectura de Roles y Accesos (Bloque 1): Los especialistas coincidieron unánimemente en la necesidad de estructurar tres roles jerárquicos principales: Estudiante, Docente de Cátedra y Curador/Administrador. Se estableció que el acceso debe restringirse a miembros activos del decanato mediante autenticación institucional, y se validó como indispensable la inclusión de un portafolio técnico personal visible en cada perfil donde el alumno exhiba sus códigos aprobados, proyectos destacados y métricas de reputación comunitaria.

2. Flujo de Información y Catalogación (Bloque 2): Se recomendó un procedimiento formal de recepción de proyectos que admita tanto ficheros de código fuente individuales (.py, .java, .cpp, .js, .sql) como proyectos completos empaquetados en formato .zip, con un tamaño máximo prudencial de hasta 25 MB por proyecto. Asimismo, se determinó como imperativo adoptar el estándar internacional Dublin Core (ISO 15836) para la catalogación por metadatos (título, autor, asignatura, lenguaje, fecha, resumen y palabras clave), asegurando que el motor de búsqueda interno permita filtros facetados multifactoriales por tecnología y período académico.

3. Interacción Social, Curaduría y Moderación (Bloque 3): Los informantes destacaron que el mecanismo de revisión por pares (peer review) debe organizarse mediante hilos técnicos constructivos vinculados a líneas específicas del código, promoviendo rúbricas de buenas prácticas de programación (legibilidad, modularidad y eficiencia algorítmica). Respecto a la publicación de recursos, se acordó un esquema híbrido de curaduría: los proyectos aprobados por los docentes pasan directamente al catálogo principal, mientras que la comunidad estudiantil modera y premia la excelencia mediante valoraciones ponderadas (upvotes) e insignias de reconocimiento técnico.

4. Experiencia de Usuario e Interfaz Frontend (Bloque 4): Se enfatizó la urgencia de garantizar un diseño plenamente responsivo bajo el enfoque Mobile-First, de manera que la plataforma sea intuitiva tanto en las computadoras de los laboratorios de la universidad como en teléfonos inteligente

A partir de la triangulación de estos requerimientos con los postulados del estándar internacional IEEE 830-1998

Cuadro Nº 20. Matriz de Requerimientos Funcionales de la Plataforma Web Colaborativa (Estándar IEEE 830)



| Código | Requerimiento | Descripción Técnica Detallada | Actor | Prioridad |
| --- | --- | --- | --- | --- |
| RF-01 | Autenticación y Control de Accesos Institucional | El sistema debe autenticar a los usuarios mediante credenciales institucionales seguras y restringir las operaciones según el rol asignado (Estudiante, Docente de Cátedra, Curador/Administrador), gestionando sesiones mediante tokens criptográficos JWT. | Todos los usuarios | Esencial (Must Have) |
| RF-02 | Gestión de Perfiles y Portafolio Técnico | La plataforma debe permitir a cada estudiante configurar su perfil académico, visualizando su historial de proyectos aprobados, insignias obtenidas, métricas de reputación comunitaria y registro de colaboraciones técnicas. | Estudiante / Docente | Importante (Should Have) |
| RF-03 | Carga y Recepción de Proyectos de Software | El sistema debe proveer una interfaz de carga que admita archivos de código fuente individuales (.py, .java, .cpp, .js, .sql) y paquetes comprimidos (.zip) con límite parametrizado de hasta 25 MB por proyecto, validando el tipo MIME antes del almacenamiento. | Estudiante | Esencial (Must Have) |
| RF-04 | Catalogación Estandarizada bajo Dublin Core | La plataforma debe exigir y registrar un esquema estandarizado de metadatos basado en Dublin Core para cada proyecto publicado: Título, Creador (autoría), Unidad Curricular, Fecha de Elaboración, Lenguaje/Tecnología, Palabras Clave, Resumen Descriptivo y Derechos de Uso. | Estudiante / Curador | Esencial (Must Have) |
| RF-05 | Motor de Búsqueda Avanzada y Filtros Facetados | El sistema debe permitir la localización ágil de proyectos mediante búsquedas por texto libre y filtros multifactoriales combinables: unidad curricular del eje, lenguaje de programación, nivel de valoración comunitaria y período académico. | Estudiante / Docente | Esencial (Must Have) |
| RF-06 | Visualizador Interactivo de Código Fuente | La interfaz debe incorporar un visor de código integrado en navegador que ofrezca resaltado de sintaxis (syntax highlighting) para múltiples lenguajes, numeración de líneas, navegación jerárquica de archivos y función de copiado seguro de fragmentos. | Estudiante / Docente | Esencial (Must Have) |
| RF-07 | Módulo de Revisión por Pares (Peer Review) | La plataforma debe permitir a los estudiantes formular revisiones técnicas constructivas organizadas por hilos de discusión, vinculando comentarios a líneas específicas de código o emitiendo evaluaciones globales bajo rúbricas de buenas prácticas. | Estudiante | Importante (Should Have) |
| RF-08 | Sistema de Valoración Social y Reputación | El sistema debe permitir emitir votos de utilidad (+1 / -1) y clasificar las publicaciones mediante un algoritmo de reputación ponderada que destaque las soluciones de mayor excelencia técnica y otorgue puntos al autor. | Estudiante / Docente | Importante (Should Have) |
| RF-09 | Panel de Curaduría y Moderación Docente | La plataforma debe proporcionar a los docentes y administradores un panel de moderación para revisar proyectos pendientes, aprobar publicaciones para el catálogo oficial, marcar recursos como 'Referente Académico' o solicitar correcciones. | Docente / Curador | Esencial (Must Have) |
| RF-10 | Sistema de Notificaciones Contextuales | El sistema debe generar notificaciones internas en tiempo real al usuario cuando su proyecto sea evaluado, reciba una revisión por pares, obtenga una insignia de reputación o sea aprobado por el docente de cátedra. | Estudiante / Docente | Deseable (Could Have) |


Fuente: Guía de entrevista aplicada a expertos y docentes de UNIMAR (2026)

Cuadro Nº 21. Matriz de Requerimientos No Funcionales de la Plataforma Web Colaborativa (Estándar IEEE 830)



| Código | Atributo / Categoría | Criterio y Métrica de Aceptación | Justificación Arquitectónica |
| --- | --- | --- | --- |
| RNF-01 | Rendimiento y Concurrencia | El tiempo de respuesta del sistema para peticiones de consulta y renderizado de código no debe superar los 2,0 segundos para el 95 % de las transacciones bajo una carga de hasta 50 usuarios concurrentes en períodos de entrega trimestral. | Garantiza una navegación fluida en los laboratorios de computación de la UNIMAR y evita cuellos de botella durante las fechas de mayor demanda evaluativa. |
| RNF-02 | Seguridad Lógica OWASP | El backend debe sanitizar rigurosamente todas las entradas de datos contra inyecciones SQL (SQLi), ataques de Cross-Site Scripting (XSS) y falsificación de peticiones (CSRF), implementando validación de esquemas con librerías tipadas. | Mitiga los principales riesgos de seguridad web identificados por el consorcio OWASP Top 10 y protege la integridad de los activos almacenados. |
| RNF-03 | Criptografía y Control de Acceso | Las contraseñas deben almacenarse bajo funciones de hashing robustas (bcrypt con factor de costo >= 12 o Argon2). Las comunicaciones deben cifrarse mediante HTTPS/TLS 1.3 y los tokens JWT deben firmarse con algoritmos HMAC-SHA256. | Asegura la confidencialidad de las credenciales y previene la intercepción de sesiones en redes compartidas o inalámbricas universitarias. |
| RNF-04 | Usabilidad y Accesibilidad | La interfaz debe ser totalmente responsiva (Mobile-First) con soporte fluido en pantallas desde 360px hasta 1920px, cumpliendo con las 10 Heurísticas de Usabilidad de Nielsen y los lineamientos de accesibilidad WCAG 2.1 nivel AA. | Permite la operabilidad del software tanto en computadores de escritorio de los laboratorios como en dispositivos móviles y tabletas de los estudiantes. |
| RNF-05 | Disponibilidad y Persistencia | La arquitectura de la base de datos PostgreSQL debe contemplar un esquema de respaldos automatizados diarios (pg_dump comprimido) con un Objetivo de Punto de Recuperación (RPO) < 24 horas y Tiempo de Recuperación (RTO) < 2 horas. | Elimina de raíz el riesgo de pérdida irreversible de código detectado en el diagnóstico empírico, garantizando la preservación histórica del capital intelectual. |
| RNF-06 | Conformidad Legal y Derechos de Autor | La plataforma debe consignar de forma inmutable los derechos morales de autoría del estudiante sobre su código, de estricta conformidad con el Artículo 18 de la Ley Sobre el Derecho de Autor y la Ley Especial Contra los Delitos Informáticos de Venezuela. | Brinda respaldo jurídico, certeza académica e incentivo profesional a los creadores de software dentro de la Universidad de Margarita. |




| Indicador | Criterio Observable | SI | NO | Observaciones Técnicas |
| --- | --- | --- | --- | --- |
| Requerimientos de Hardware y Servidor | 1. Cuenta el entorno de despliegue con servidores de aplicación con capacidad de procesamiento multinúcleo y un mínimo de 8 GB de memoria RAM para ejecución concurrente. | X |  | Verificado en la infraestructura de servidores virtuales del Decanato de Ingeniería y en entornos cloud estándar. |
| Requerimientos de Hardware y Servidor | 2. Dispone la infraestructura de almacenamiento de un volumen en estado sólido (SSD) escalable para el resguardo de proyectos y repositorios de código. | X |  | Almacenamiento en volúmenes SSD NVMe con alta tasa de operaciones de entrada/salida por segundo (IOPS). |
| Conectividad y Red | 3. Posee la institución una infraestructura de red y enlace de internet con ancho de banda suficiente para garantizar accesibilidad remota continua. | X |  | Enlace corporativo de fibra óptica de la UNIMAR con ancho de banda dedicado a servicios académicos. |
| Conectividad y Red | 4. Cuenta el servidor con protocolos establecidos para copias de seguridad periódicas y recuperación ante desastres de hardware o fallas de energía. | X |  | Se define script cron de snapshot y respaldo automatizado en almacenamiento secundario desacoplado. |
| Arquitectura Frontend | 5. Estructura el frontend una arquitectura modular basada en componentes desacoplados y reutilizables mediante frameworks modernos (React.js / Next.js). | X |  | Implementación con React.js / Next.js bajo paradigma de componentes funcionales y renderizado óptimo. |
| Arquitectura Frontend | 6. Implementa el frontend un enrutamiento dinámico que facilita la navegación ágil entre cátedras, publicaciones, perfiles y foros técnicos. | X |  | Enrutamiento basado en Next.js App Router con carga bajo demanda (lazy loading) y rutas dinámicas tipadas. |
| Arquitectura Backend | 7. Posee el backend una arquitectura de servicios desacoplada con controladores y modelos organizados para el procesamiento estructurado de peticiones HTTP. | X |  | Arquitectura en capas (Controller-Service-Repository) en Node.js garantizando alta modularidad y mantenibilidad. |
| Arquitectura Backend | 8. Integra el backend una interfaz de programación de aplicaciones (API RESTful) para el intercambio de datos en formato estandarizado JSON. | X |  | Endpoints RESTful conformes a especificaciones OpenAPI con payloads y respuestas serializadas en JSON. |
| Base de Datos Relacional | 9. Implementa la persistencia de datos mediante un sistema gestor de base de datos relacional (PostgreSQL / MySQL) normalizado en tercera forma normal. | X |  | PostgreSQL 15 desplegado con modelo entidad-relación estrictamente normalizado en 3FN sin redundancias. |
| Base de Datos Relacional | 10. Integra la base de datos un modelo entidad-relación coherente que vincula usuarios, roles, publicaciones de proyectos, asignaturas, comentarios y calificaciones. | X |  | Esquema relacional con 7 tablas centrales e integridad referencial forzada mediante claves foráneas y cascada controlada. |
| Base de Datos Relacional | 11. Cuenta con procedimientos y transacciones estructuradas para garantizar la integridad referencial y consistencia de los registros en la base de datos. | X |  | Cumplimiento estricto de propiedades ACID mediante transacciones controladas en operaciones críticas de publicación y votación. |
| Catalogación y Metadatos | 12. Dispone de un esquema estandarizado de metadatos (Dublin Core) para catalogar cada proyecto (título, autor, asignatura, fecha, lenguaje, descripción). | X |  | Campos normalizados compatibles con los elementos esenciales del estándar Dublin Core Metadata Element Set (ISO 15836). |
| Seguridad y Autenticación | 13. Implementa mecanismos de autenticación robusta mediante tokens criptográficos (JSON Web Tokens - JWT) o sesiones seguras para el control de acceso. | X |  | Tokens JWT firmados con secret de 256 bits, expiración de 2 horas y refresh tokens rotativos en cookies HTTP-only. |
| Seguridad y Roles | 14. Posee un sistema de autorización basado en perfiles y roles diferenciados (Estudiante, Docente, Curador/Administrador) con permisos estrictamente delimitados. | X |  | Control de acceso basado en roles (RBAC) con middlewares específicos que protegen cada endpoint del backend. |
| Seguridad Lógica | 15. Dispone de mecanismos de validación, sanitización y filtrado de datos en servidor para prevenir inyecciones SQL y ataques Cross-Site Scripting (XSS). | X |  | Uso de consultas parametrizadas vía ORM/QueryBuilder y saneamiento de entradas HTML mediante DOMPurify. |
| Seguridad Lógica | 16. Cuenta con políticas de restricción de tipos MIME y extensiones autorizadas para impedir la carga de scripts maliciosos o archivos ejecutables dañinos. | X |  | Lista blanca estricta (.py, .java, .cpp, .js, .sql, .zip) y validación de cabeceras mágicas de archivos en backend. |
| Seguridad de Credenciales | 17. Implementa algoritmos de hashing seguro unidireccional con sal (bcrypt/Argon2) para el almacenamiento cifrado de contraseñas de usuario. | X |  | Cifrado irreversible de contraseñas con bcrypt utilizando factor de coste 12 y generación aleatoria de sal. |
| Seguridad de Sesiones | 18. Presenta caducidad y cierre automático de sesiones por inactividad prolongada para resguardar la seguridad en estaciones de trabajo compartidas. | X |  | Invalidez automática de sesión tras 30 minutos de inactividad, crucial para computadores de laboratorios UNIMAR. |
| Módulo de Publicación | 19. Integra un módulo de publicación donde el estudiante registra títulos, descripciones, adjunta archivos de código y asigna etiquetas temáticas. | X |  | Formulario multipaso con validación en tiempo real y selector facetado de cátedras y tecnologías. |
| Visualizador de Código | 20. Dispone de un visualizador de código fuente embebido en interfaz que incorpora resaltado de sintaxis (syntax highlighting) y numeración de líneas. | X |  | Visor interactivo con soporte multilinguaje basado en Prism.js / Monaco Editor con temas claro y oscuro. |
| Curaduría y Valoración | 21. Cuenta con un sistema de valoración social (upvotes / puntuación ponderada) que permite a los usuarios calificar la utilidad y calidad técnica de los proyectos. | X |  | Mecanismo de votación ponderada con restricción de un voto por usuario y recálculo dinámico de reputación. |
| Revisión por Pares | 22. Presenta un módulo interactivo de comentarios técnicos estructurado por hilos para facilitar la retroalimentación constructiva y la revisión por pares. | X |  | Hilos anidados de discusión con posibilidad de vincular feedback técnico a bloques de código específicos. |
| Búsqueda y Filtros | 23. Posee un motor de búsqueda con filtros avanzados por unidad curricular del eje, tecnología/lenguaje de programación, fecha y valoración. | X |  | Búsqueda semántica y filtros combinables con indexación Full-Text Search nativa de PostgreSQL. |
| Portafolio del Estudiante | 24. Integra un panel o portafolio personal donde el usuario visualiza el historial de sus códigos subidos, valoraciones recibidas y métricas de interacción. | X |  | Dashboard personalizado con bitácora de actividad, badges otorgados y métricas acumuladas de impacto técnico. |
| Usabilidad y Heurísticas | 25. Presenta una interfaz gráfica organizada con jerarquía visual clara, tipografía legible y navegación coherente con las heurísticas de Nielsen. | X |  | Diseño basado en Atomic Design y Design System cohesivo con contrastes tipográficos conformes a WCAG. |
| Diseño Responsivo | 26. Cuenta con diseño responsivo que adapta la presentación de forma óptima a pantallas de escritorio, laptops y dispositivos móviles o tabletas. | X |  | Grid fluido implementado con Tailwind CSS que reconfigura los paneles según el viewport del dispositivo. |
| Interactividad y Feedback | 27. Proporciona retroalimentación visual inmediata (indicadores de progreso, alertas contextuales, confirmaciones) ante eventos de subida, edición o error. | X |  | Barras de progreso en subidas, tooltips informativos y notificaciones toast ante cualquier interacción de estado. |
| Manejo de Errores UX | 28. Dispone de mensajes informativos y de error claros y pedagógicos que asisten al usuario en la resolución de problemas durante su interacción con el sistema. | X |  | Manejo amigable de excepciones 400/404/500 con instrucciones de resolución guiada sin exponer trazas técnicas. |
| Derechos de Autor | 29. Muestra visiblemente los términos de uso y las cláusulas de propiedad intelectual que garantizan el reconocimiento de los derechos morales de autor del estudiante. | X |  | Inclusión de licencias abiertas de tipo Creative Commons (CC BY-NC-SA) y cláusulas de autoría protegida. |
| Marco Legal Informático | 30. Cumple con los requerimientos de confidencialidad y protección de datos exigidos por el marco legal venezolano (Ley Especial Contra los Delitos Informáticos). | X |  | Auditoría de logs de acceso, consentimiento informado de tratamiento de datos y protección contra accesos indebidos. |


Fuente: Lista de cotejo técnica evaluada por expertos en ingeniería (2026).

Arquitectura General del Sistema y Capa de Persistencia

Con base en los treinta (30) criterios técnicos verificados positivamente en la Lista de Cotejo, se diseñó una arquitectura de software desacoplada de tres capas (3-Tier Architecture) con separación total entre la capa de presentación (Frontend), la capa lógica de negocio (Backend RESTful API) y la capa de almacenamiento persistente (Base de Datos Relacional):

1. Capa de Presentación (Frontend): Desarrollada mediante React.js y Next.js, implementando un diseño modular basado en componentes reutilizables (Atomic Design) y estilizado con Tailwind CSS. La gestión del estado global se articula a través de Context API / Zustand, asegurando tiempos de carga inmediatos y renderizado en servidor (SSR) para las vistas públicas, lo que maximiza la indexación y la experiencia de usuario.

2. Capa de Servicios y Lógica de Negocio (Backend): Construida sobre Node.js con Express / NestJS bajo un patrón arquitectónico Controller-Service-Repository. Esta capa expone una API RESTful completamente documentada bajo estándares OpenAPI/Swagger, integrando middlewares de sanitización (DOMPurify, Helmet), validadores tipados de esquemas de datos (Zod/Joi) y un módulo de autenticación criptográfica basado en JSON Web Tokens (JWT) con expiración y rotación de refresh tokens.

3. Capa de Persistencia (Base de Datos): Implementada en el sistema gestor relacional PostgreSQL 15, normalizado rigurosamente en Tercera Forma Normal (3FN). Este diseño garantiza la eliminación de anomalías de inserción, actualización y borrado, forzando la integridad referencial y las transacciones ACID para operaciones concurrentes de carga, calificación y revisión de proyectos.

Cuadro Nº 23. Diccionario de Datos del Modelo Entidad-Relación de la Plataforma Web Colaborativa



| Tabla | Campo | Tipo Dato | Nulo | Clave | Descripción Semántica |
| --- | --- | --- | --- | --- | --- |
| USUARIOS | id_usuario | UUID | NO | PK | Identificador único global del usuario registrado. |
| USUARIOS | nombre_completo | VARCHAR(150) | NO | - | Nombres y apellidos del estudiante o docente. |
| USUARIOS | correo_institucional | VARCHAR(120) | NO | UNIQUE | Correo electrónico institucional @unimar.edu.ve. |
| USUARIOS | password_hash | VARCHAR(255) | NO | - | Hash criptográfico de la contraseña (bcrypt factor 12). |
| USUARIOS | id_rol | INTEGER | NO | FK | Referencia al rol de usuario (FK -> ROLES.id_rol). |
| USUARIOS | puntos_reputacion | INTEGER | NO | DEFAULT 0 | Puntaje acumulado por valoraciones y revisiones positivas. |
| USUARIOS | fecha_registro | TIMESTAMP | NO | DEFAULT NOW() | Fecha y hora exacta de creación de la cuenta. |
| ROLES | id_rol | SERIAL | NO | PK | Identificador secuencial del rol. |
| ROLES | nombre_rol | VARCHAR(50) | NO | UNIQUE | Nombre del rol: Estudiante, Docente, Curador/Admin. |
| ROLES | permisos | JSONB | NO | - | Objeto JSON con matriz de privilegios y acciones autorizadas. |
| CATEDRAS | id_catedra | SERIAL | NO | PK | Identificador de la unidad curricular. |
| CATEDRAS | codigo_materia | VARCHAR(20) | NO | UNIQUE | Código de catálogo académico en UNIMAR. |
| CATEDRAS | nombre_catedra | VARCHAR(100) | NO | - | Nombre (ej. Algoritmos y Programación I, II, Estructuras). |
| CATEDRAS | trimestre | INTEGER | NO | - | Trimestre curricular en que se imparte (I al IX). |
| PROYECTOS | id_proyecto | UUID | NO | PK | Identificador único global del proyecto de software. |
| PROYECTOS | titulo | VARCHAR(200) | NO | - | Título descriptivo del proyecto (Dublin Core: Title). |
| PROYECTOS | descripcion | TEXT | NO | - | Resumen técnico de la solución (Dublin Core: Description). |
| PROYECTOS | id_autor | UUID | NO | FK | Autor principal del proyecto (FK -> USUARIOS.id_usuario). |
| PROYECTOS | id_catedra | INTEGER | NO | FK | Asignatura a la que pertenece (FK -> CATEDRAS.id_catedra). |
| PROYECTOS | lenguaje_principal | VARCHAR(50) | NO | - | Tecnología o lenguaje primario (Python, Java, C++, JS, SQL). |
| PROYECTOS | estado_curaduria | VARCHAR(30) | NO | DEFAULT 'Pendiente' | Estado: Pendiente, Aprobado, Destacado, Rechazado. |
| PROYECTOS | fecha_publicacion | TIMESTAMP | NO | DEFAULT NOW() | Fecha de carga formal en la plataforma. |
| ARCHIVOS_CODIGO | id_archivo | UUID | NO | PK | Identificador único del archivo o script adjunto. |
| ARCHIVOS_CODIGO | id_proyecto | UUID | NO | FK | Proyecto al que pertenece (FK -> PROYECTOS.id_proyecto). |
| ARCHIVOS_CODIGO | nombre_archivo | VARCHAR(120) | NO | - | Nombre del archivo con su extensión correspondiente. |
| ARCHIVOS_CODIGO | extension | VARCHAR(10) | NO | - | Extensión normalizada (.py, .java, .cpp, .js, .sql, .zip). |
| ARCHIVOS_CODIGO | contenido_codigo | TEXT | SI | - | Texto plano del código fuente para visualización y búsqueda. |
| ARCHIVOS_CODIGO | tamanio_bytes | BIGINT | NO | - | Tamaño del archivo en bytes. |
| ARCHIVOS_CODIGO | ruta_almacenamiento | VARCHAR(255) | NO | - | Ruta segura en el volumen persistente de almacenamiento. |
| REVISIONES_PARES | id_revision | UUID | NO | PK | Identificador único de la revisión técnica o comentario. |
| REVISIONES_PARES | id_proyecto | UUID | NO | FK | Proyecto objeto de revisión (FK -> PROYECTOS.id_proyecto). |
| REVISIONES_PARES | id_revisor | UUID | NO | FK | Usuario evaluador (FK -> USUARIOS.id_usuario). |
| REVISIONES_PARES | comentario_tecnico | TEXT | NO | - | Observación cualitativa y sugerencia de optimización. |
| REVISIONES_PARES | calificacion_criterio | INTEGER | SI | - | Puntuación en escala 1 a 5 según rúbrica de buenas prácticas. |
| REVISIONES_PARES | linea_referencia | INTEGER | SI | - | Línea específica del código asociada a la observación. |
| REVISIONES_PARES | fecha_revision | TIMESTAMP | NO | DEFAULT NOW() | Fecha y hora de registro de la retroalimentación. |
| VALORACIONES | id_valoracion | UUID | NO | PK | Identificador de la votación comunitaria. |
| VALORACIONES | id_proyecto | UUID | NO | FK | Proyecto calificado (FK -> PROYECTOS.id_proyecto). |
| VALORACIONES | id_usuario | UUID | NO | FK | Usuario emisor del voto (FK -> USUARIOS.id_usuario). |
| VALORACIONES | tipo_voto | SMALLINT | NO | - | Valor numérico del voto (+1 utilidad / -1 desfavorable). |
| VALORACIONES | fecha_voto | TIMESTAMP | NO | DEFAULT NOW() | Momento del sufragio técnico (UNIQUE id_proy, id_usr). |


Fuente: Modelado de datos del proyecto de ingeniería (2026).

Diseño de Interfaces de Usuario (UI/UX) y Prototipado Estructural

El diseño de las interfaces de usuario se fundamentó en los principios del diseño centrado en el usuario (DCU) y las directrices de Nielsen Norman Group, concibiendo cuatro (4) vistas clave que articulan los flujos operativos de la plataforma:

• Vista 1: Panel Principal y Feed de Proyectos Destacados (Dashboard): Dispone de una cabecera con navegación superior institucional, barra de búsqueda semántica con autocompletado y un panel lateral de filtros facetados (por unidad curricular del eje, tecnología y rango de valoraciones). El cuerpo central presenta tarjetas modulares de proyectos que exhiben el título bajo Dublin Core, autor, cátedra, lenguaje principal, etiquetas técnicas, conteo de votos de utilidad y badge de estado de curaduría.

• Vista 2: Visualizador Interactivo de Código Fuente y Catalogación: Integra un explorador jerárquico de archivos a la izquierda y un editor de sólo lectura en el panel central dotado de resaltado de sintaxis (syntax highlighting), numeración de líneas y temas adaptables (claro/oscuro). En la sección superior se exhibe la ficha técnica formal de metadatos Dublin Core (Creador, Fecha, Cátedra, Licencia de Derechos Morales de Autor) y botones de acción para descarga segura y copiado de fragmentos.

• Vista 3: Módulo de Discusión Técnica y Revisión por Pares (Peer Review): Diseñado para el intercambio constructivo de retroalimentación. Permite anclar comentarios y sugerencias a líneas específicas de código o emitir reseñas globales sobre arquitectura y optimización. Incluye formularios estructurados con criterios de evaluación (1 a 5 estrellas) y botones para valorar la utilidad de las respuestas de los compañeros.

• Vista 4: Portafolio Técnico y Perfil Académico del Estudiante: Funciona como la bitácora profesional del estudiante en la UNIMAR. Refleja su nivel de reputación acumulado, el repositorio de sus proyectos aprobados, las revisiones técnicas en las que ha participado y las insignias de honor obtenidas por excelencia en desarrollo de software, consolidando su identidad en el capital relacional universitario.

Validación Heurística de Usabilidad y Accesibilidad Web

Para asegurar que las interfaces desarrolladas satisfagan los más elevados estándares ergonómicos y normativos, se realizó una evaluación sistemática frente a las diez (10) Heurísticas de Usabilidad de Jakob Nielsen y los criterios de conformidad WCAG 2.1 nivel AA.

Cuadro Nº 24. Matriz de Validación Frente a las 10 Heurísticas de Usabilidad de Jakob Nielsen



| Nº | Heurística de Nielsen | Implementación en la Plataforma Colaborativa | Evaluación |
| --- | --- | --- | --- |
| 1 | Visibilidad del estado del sistema | Indicadores visuales de carga, barras de progreso en subida de código y alertas toast de confirmación. | Conforme (100 %) |
| 2 | Correspondencia con el mundo real | Uso de terminología técnica de ingeniería (cátedras UNIMAR, repositorios, commit, revisión por pares). | Conforme (100 %) |
| 3 | Control y libertad del usuario | Botones de cancelar edición, descarte de borradores y confirmación modal previa al borrado definitivo. | Conforme (100 %) |
| 4 | Consistencia y estándares | Patrones UI coherentes en todas las vistas (paleta institucional, tipografía Inter/Roboto, botones estándar). | Conforme (100 %) |
| 5 | Prevención de errores | Validación en tiempo real en formularios de carga, bloqueo de extensiones inválidas antes de enviar. | Conforme (100 %) |
| 6 | Reconocimiento antes que recuerdo | Menús desplegables facetados, sugerencias visuales de etiquetas y visualización previa de código. | Conforme (100 %) |
| 7 | Flexibilidad y eficiencia de uso | Atajos de teclado en el visualizador, filtros combinados y función de copiado rápido al portapapeles. | Conforme (100 %) |
| 8 | Diseño estético y minimalista | Disposición limpia sin sobrecarga cognitiva, jerarquía visual basada en espacios negativos y tarjetas. | Conforme (100 %) |
| 9 | Ayuda para reconocer errores | Mensajes explicativos claros en español neutro, orientando cómo subsanar el campo o archivo observado. | Conforme (100 %) |
| 10 | Ayuda y documentación | Sección de preguntas frecuentes (FAQ), guía de estilo de código y rúbrica para revisión por pares. | Conforme (100 %) |


Fuente: Evaluación de interfaces frente a heurísticas de Nielsen (2026).

Cuadro Nº 25. Matriz de Cumplimiento de Accesibilidad Web (Estándar WCAG 2.1 Nivel AA)



| Principio WCAG | Pauta Específica | Mecanismo de Conformidad Técnica | Nivel |
| --- | --- | --- | --- |
| 1. Perceptible | Contraste y texto alternativo | Ratio de contraste superior a 4.5:1 en textos y etiquetas ARIA en todos los elementos interactivos. | AA (Conforme) |
| 2. Operable | Accesibilidad por teclado | Navegación completa vía tabulación de teclado con indicador visual de foco (focus visible ring). | AA (Conforme) |
| 3. Comprensible | Previsibilidad y asistencia | Estructura semántica HTML5 (header, nav, main, section, footer) y mensajes de validación descriptivos. | AA (Conforme) |
| 4. Robusto | Compatibilidad tecnológica | Soporte transversal en navegadores modernos (Chrome, Firefox, Edge, Safari) y lectores de pantalla. | AA (Conforme) |


Fuente: Auditoría técnica de accesibilidad bajo lineamientos WCAG 2.1 (2026).

Triangulación Metodológica y Síntesis General de los Resultados

La triangulación metodológica implementada en la investigación articuló dialécticamente los hallazgos cuantitativos del diagnóstico estudiantil (Objetivo 1), los requerimientos de ingeniería derivados de la entrevista a las autoridades académicas (Objetivo 2) y las especificaciones arquitectónicas y de diseño validadas mediante la lista de cotejo técnica (Objetivo 3). Esta convergencia de fuentes y técnicas permitió contrastar la vivencia empírica del aula con la visión directiva y los estándares formales del desarrollo de software.

En primer término, el diagnóstico cuantitativo evidenció una asimetría crítica: mientras que los estudiantes de UNIMAR poseen un elevado capital humano expresado en la creación autónoma de algoritmos (84 % y 88 %), este potencial se diluye drásticamente ante la carencia de capital estructural (88 % sin canales de consulta y 92 % de proyectos fuera del alcance de nuevas cohortes) y la fragilidad del capital relacional (76 % sin retroalimentación técnica y dependencia masiva de mensajería efímera). Esta fractura confirmó la hipótesis diagnóstica de la pérdida sistemática de activos de conocimiento en el decanato.

En segundo término, la consulta a los informantes clave ofreció el marco normativo y operativo para subsanar dicha brecha, delineando con precisión los requerimientos funcionales (RF-01 al RF-10) y no funcionales (RNF-01 al RNF-06). Las entrevistas permitieron definir la estructura tripartita de roles, la adopción del estándar Dublin Core para evitar el caos documental y la imperiosa necesidad de un modelo híbrido de curaduría que combine la autoridad pedagógica del docente con la dinamización comunitaria de la revisión por pares.

Finalmente, la evaluación observacional técnica constató la plena viabilidad de implementar una arquitectura de tres capas desacopladas (React/Next.js en el frontend, Node.js en el backend y PostgreSQL normalizada en 3FN), acompañada de interfaces que satisfacen al 100 % las 10 Heurísticas de Usabilidad de Nielsen y el nivel AA de las pautas WCAG 2.1. De este modo, la investigación demuestra que la plataforma web colaborativa propuesta no solo es factible desde la perspectiva de infraestructura y código, sino que constituye el catalizador indispensable para transformar el esfuerzo disperso de los estudiantes en un capital intelectual permanente, institucionalizado y de alto valor formativo para la Universidad de Margarita.

REFERENCIAS

Alas, W. (2025). Desarrollo de un módulo de gestión de actividades deportivas y culturales integrado al portal web de la Universidad de Margarita en el estado Nueva Esparta. (Trabajo de Grado). Universidad de Margarita, El Valle del Espíritu Santo.

Arias, F. (2012). El proyecto de investigación: Introducción a la metodología científica. (6ta ed.). Caracas: Episteme.

Balestrini, M. (2006). Cómo se formula el proyecto de investigación. (7ma ed.). Caracas: BL Consultores Asociados.

Bhargava, R. (2009). Manifesto for the Content Curator. Lulupress.

Cardona, A. y Montoya, L. (2024). La gestión del conocimiento en bibliotecas universitarias: de repositorios estáticos a centros de innovación colaborativa. (Trabajo de Grado). Universidad Nacional de Colombia, Bogotá.

Cerveró-Carrascosa, A., Vidal Prades, S. y Martí-Puig, M. (2024). El uso de Padlet como herramienta para la co-construcción de saberes y el aprendizaje colaborativo. Revista de Educación Virtual, 12(2), 150-165.

Chávez, N. (2007). Introducción a la investigación educativa. (4ta ed.). Maracaibo: Gráfica González.

Constitución de la República Bolivariana de Venezuela. (1999). Gaceta Oficial de la República Bolivariana de Venezuela, N° 36.860. (Extraordinaria), Diciembre 30, 1999.

Cortés, J. y Sierra, M. (2024). Aprendizaje colaborativo y desarrollo de competencias transversales en estudiantes de ingeniería de sistemas. Revista Iberoamericana de Ingeniería de Software, 8(1), 25-38.

Creswell, J. (2014). Research Design: Qualitative, Quantitative, and Mixed Methods Approaches. (4ta ed.). California: SAGE Publications.

Escorcia, J. y Barros, D. (2020). Gestión del conocimiento y capital intelectual en las Instituciones de Educación Superior. Revista de Ciencias Sociales, 26(1), 54-68.

García, J. (2014). El marco teórico en la investigación científica. México: Limusa.

García-Chitiva, M. P. (2021). El aprendizaje colaborativo en entornos virtuales en la educación superior venezolana: tendencias y desafíos. Revista de Pedagogía Universitaria, 42(3), 420-435.

Guallar, J. y Leiva-Aguilera, J. (2013). El content curator: Guía básica para la curación de contenidos en la web. Barcelona: Editorial UOC.

Hernández, R., Fernández, C. y Baptista, M. (2014). Metodología de la investigación. (6ta ed.). México: McGraw-Hill.

Hernández-Sellés, N., Muñoz-Carril, P. C. y González-Sanmamed, M. (2024). Roles del docente en la gestión del aprendizaje colaborativo en entornos digitales universitarios. Revista de Educación a Distancia, 24(1), 85-102.

Ley Especial Contra los Delitos Informáticos. (2001). Gaceta Oficial de la República Bolivariana de Venezuela, N° 37.313. Octubre 30, 2001.

Ley Orgánica de Telecomunicaciones. (2011). Gaceta Oficial de la República Bolivariana de Venezuela, N° 39.610. Febrero 7, 2011.

Ley Sobre el Derecho de Autor. (1993). Gaceta Oficial de la República de Venezuela, N° 4.638. (Extraordinaria), Octubre 1, 1993.

Medina, N., Nogueira, D. y Hernández, A. (2020). La necesidad de compartir conocimiento en las universidades públicas contemporáneas. Revista de Educación Superior y Sociedad, 31(2), 60-78.

Muñoz Moreno, J. A. y Ospina Rozo, L. M. (2024). Modelos de gestión y capital intelectual universitario: componentes estratégico para las IES. Bogotá: Ediciones USTA.

Nonaka, I. y Takeuchi, H. (1995). The Knowledge-Creating Company: How Japanese Companies Create the Dynamics of Innovation. Oxford University Press.

Palella, S. y Martins, F. (2012). Metodología de la investigación cuantitativa. (3ra ed.). Caracas: FEDUPEL.

Ramírez Chávez, T. (2001). Cómo diseñar y realizar un proyecto de investigación. (3ra ed.). Caracas: Panapo.

Roa Guerrero, D. A., et al. (2021). La gestión del conocimiento aplicada a los proyectos integradores en la formación del ingeniero de sistemas. Revista de Educación en Ingeniería, 16(31), 85-94.

Ruiz Bolívar, C. (2002). Instrumentos de investigación educativa: diseño y validación. Barquisimeto: CIDEG.

Surco Salinas, M. (2023). Gestión del conocimiento tácito y explícito entre cohortes estudiantiles en facultades de ingeniería en Venezuela. Revista Venezolana de Educación, 27(80), 165-180.
