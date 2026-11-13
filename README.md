# Caramel - Plataforma de Recomendación de Documentos Académicos

Plataforma web con motor de recomendación híbrido para estudiantes universitarios, desarrollada en Python (FastAPI + Jinja2 + Tailwind CSS + Alpine.js + Scikit-Learn), replicando fielmente el diseño y flujo del prototipo de Figma:
[Caramel Figma Prototype](https://www.figma.com/proto/HENzhk9zdmNOt8vP13dkxQ/Caramel-Prototype?node-id=36-21)

---

## Inicio Rápido

Para iniciar la plataforma ejecuta el script automatizado:

```bash
cd /home/oscar/Proyectos/Caramel
./run.sh
```

O manualmente:
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

* **Plataforma Web:** [http://localhost:8001](http://localhost:8001)
* **Laboratorio del Algoritmo:** [http://localhost:8001/recommender-lab](http://localhost:8001/recommender-lab)
* **Documentación Interactiva Swagger / OpenAPI:** [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Pantallas y Componentes de Figma Replicados

1. **Pantalla 1: Registro & Onboarding (`/register` y `/login`)**:
   - Cabecera con collage de ambiente universitario.
   - Monograma de marca Caramel en tonos caramelo cálidos (`#C6864D` / `#DCA067`).
   - Captura de **Carrera Académica**, **Trimestre / Semestre en curso**, correo y credenciales.
   - Botón píldora característico y selector de acceso rápido con perfiles de prueba.

2. **Pantalla 2: Feed Principal (`/`)**:
   - Saludo personalizado: *"Hola, Oscar! Explora o califica algún material reciente..."*.
   - Badge de carrera y trimestre del estudiante activo.
   - **Populares en este trimestre**: Carrusel horizontal interactivo filtrado por el trimestre del estudiante.
   - **Listas que podrían servirte**: Stacks de colecciones (*Mejores libros de Matemáticas II*, *Programación en Kotlin, papayita*, *Lenguaje SQL y consultas*).
   - **Recomendados para ti con IA**: Tarjetas con porcentaje de afinidad y etiqueta explicable (*"Clave para tu 3º Trimestre de Ingeniería de Sistemas"*).
   - **Reviews recientes de tus amigos**: Feed social con valoraciones con estrellas, comentarios reales y miniaturas de las portadas de los libros.
   - Barra de navegación flotante inferior tipo dock con efecto glassmorphism.

3. **Pantalla 3: Detalle de Documento (`/document/{id}`)**:
   - Banner superior temático y portada del libro (ej. *Cálculo* de Larson & Edwards).
   - Botones de acción: *Leer en línea*, *Guardar en lista*, *Calificar*.
   - Puntuación global destacada (ej. `4.6 `).
   - **Histograma de 5 estrellas escalonado**: Representación visual de barras por nivel (5a 1) idéntica al prototipo.
   - Avatares solapados de *"Varios de tus amigos lo han leído"*.
   - Feed de reseñas comunitarias y modal interactivo para publicar nuevas calificaciones que actualizan el recomendador en tiempo real.

4. **Selector de Vistas**:
   - En la barra superior puedes alternar entre **Vista Móvil (Figma)** (contenedor centrado de teléfono con notch simulado) o **Vista Expandida Web**.

---

## Arquitectura del Algoritmo de Recomendación

El motor de recomendación implementado en `app/recommender.py` utiliza un modelo híbrido multidimensional:

$$\text{Score} = (0.35 \times S_{\text{acad}}) + (0.25 \times S_{\text{social}}) + (0.25 \times S_{\text{content}}) + (0.15 \times S_{\text{bayes}})$$

### 1. Afinidad Académica Curricular ($S_{\text{acad}}$ - 35%)
Evalúa si las materias, áreas y nivel del documento coinciden con la carrera y el trimestre actual que cursa el estudiante.

### 2. Filtrado Colaborativo y Social ($S_{\text{social}}$ - 25%)
Pondera las interacciones de los amigos agregados del usuario y compañeros de la misma cohorte. Si los amigos han valorado positivamente un material ($\ge 4$ estrellas), recibe un multiplicador de confianza social.

### 3. Filtrado Basado en Contenido con TF-IDF ($S_{\text{content}}$ - 25%)
Construye un espacio vectorial a partir de las sinopsis, materias, descriptores y autores usando `TfidfVectorizer` (con n-gramas 1-2 y stop words en español). Compara el vector de intereses del estudiante con el catálogo mediante **Similitud Coseno** de `scikit-learn`.

### 4. Ponderación Bayesiana de Calidad ($S_{\text{bayes}}$ - 15%)
Suaviza las calificaciones para evitar que un documento con un solo voto de 5 estrellas supere a uno con decenas de reseñas positivas:
$$WR = \frac{v}{v + m} R + \frac{m}{v + m} C$$
(donde $v$ es el total de votos, $m=3$ es el umbral mínimo, $R$ el promedio del libro y $C$ la media de la facultad).

### 5. Explicabilidad en Lenguaje Natural (Explainable AI)
Cada recomendación muestra un motivo transparente generado automáticamente (ej. *"Clave para tu 3º Trimestre de Ingeniería de Sistemas"*, *"Recomendado por 3 de tus amigos con 5"*, *"94% de afinidad con tus temas de estudio"*).

---

## Perfiles de Demostración Disponibles

Puedes alternar entre estos perfiles desde el menú superior o en `/demo-switch/{id}` para ver cómo el feed se adapta automáticamente:
* **Oscar Rodríguez** (ID: 1): Ing. de Sistemas • 3er Trimestre (Usuario por defecto)
* **Carlos Mendoza** (ID: 2): Ing. de Sistemas • 4to Trimestre
* **Valentina Castro** (ID: 3): Ing. de Sistemas • 3er Trimestre
* **Andrés Morales** (ID: 4): Computación • 3er Trimestre
* **Sofía Paredes** (ID: 5): Ing. de Sistemas • 2do Trimestre
* **David Silva** (ID: 6): Ing. Civil • 4to Trimestre

---

## Estructura del Código

```
Caramel/
├── app/
│   ├── main.py                  # Servidor FastAPI y montaje de rutas
│   ├── database.py              # Conexión SQLAlchemy y base de datos SQLite
│   ├── models.py                # Modelos ORM (User, Document, Review, CuratedList, etc.)
│   ├── recommender.py           # Motor matemático híbrido (TF-IDF, Coseno, Bayesiano)
│   ├── seed_data.py             # Datos iniciales con textos e imágenes del Figma
│   ├── routes/
│   │   ├── auth.py              # Registro, Login, Switch de perfiles
│   │   ├── feed.py              # Feed principal, Populares, Listas, Explorar
│   │   ├── documents.py         # Detalle de libro, Histograma, Reseñas, Guardados
│   │   └── api_recommender.py   # API REST JSON
│   ├── static/
│   │   ├── css/caramel.css      # Paleta caramelo/café oscuro, glassmorphism, scrollbars
│   │   └── js/app.js            # Interacciones de cliente (carruseles, rating, vistas)
│   └── templates/
│       ├── base.html            # Shell base responsivo con dock inferior
│       ├── feed.html            # Pantalla 2 Figma (Hola, Oscar!)
│       ├── document_detail.html # Pantalla 3 Figma (Cálculo, histograma, reviews)
│       ├── register.html        # Pantalla 1 Figma (Caramel Regístrate)
│       ├── login.html           # Iniciar sesión
│       ├── explore.html         # Buscador y filtros de materias
│       ├── profile.html         # Perfil universitario y libros guardados
│       └── recommender_lab.html # Simulador del algoritmo con desglose de métricas
├── run.sh                       # Script de ejecución en un solo paso
├── requirements.txt             # Dependencias de Python
└── README.md
```
