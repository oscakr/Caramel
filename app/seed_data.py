"""
Initial database seeder with realistic academic documents, users, friendships,
curated lists, and peer reviews matching the Caramel Figma prototype.
"""

from sqlalchemy.orm import Session
from .models import User, Document, Review, CuratedList, Friendship, Bookmark, UserInteraction
from .database import SessionLocal, engine, Base

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("Database already contains records. Skipping seed.")
        db.close()
        return

    print("Seeding Caramel database with Figma prototype data...")

    # 1. Create Users
    users_data = [
        {
            "username": "oscar",
            "email": "oscar@universidad.edu",
            "password": "password123",
            "full_name": "Oscar Rodríguez",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 3,
            "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        },
        {
            "username": "carlos_dev",
            "email": "carlos@universidad.edu",
            "password": "password123",
            "full_name": "Carlos Mendoza",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 4,
            "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150"
        },
        {
            "username": "valentina_c",
            "email": "valentina@universidad.edu",
            "password": "password123",
            "full_name": "Valentina Castro",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 3,
            "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150"
        },
        {
            "username": "andres_code",
            "email": "andres@universidad.edu",
            "password": "password123",
            "full_name": "Andrés Morales",
            "carrera": "Computación",
            "trimestre": 3,
            "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"
        },
        {
            "username": "sofia_m",
            "email": "sofia@universidad.edu",
            "password": "password123",
            "full_name": "Sofía Paredes",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 2,
            "avatar_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150"
        },
        {
            "username": "david_arq",
            "email": "david@universidad.edu",
            "password": "password123",
            "full_name": "David Silva",
            "carrera": "Ingeniería Civil",
            "trimestre": 4,
            "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"
        }
    ]

    users_created = []
    for u_data in users_data:
        user = User(**u_data)
        db.add(user)
        users_created.append(user)
    db.commit()

    # 2. Friendships (Connecting Oscar with Carlos, Valentina, Andrés, Sofía)
    oscar = users_created[0]
    for friend in users_created[1:]:
        db.add(Friendship(user_id=oscar.id, friend_id=friend.id))
    db.commit()

    # 3. Create Documents (textbooks & academic papers matching Figma)
    docs_data = [
        {
            "title": "Cálculo: Trascendentes Tempranas",
            "subtitle": "Cálculo Diferencial e Integral en una y varias variables",
            "edition": "10ma Edición",
            "authors": "Ron Larson & Bruce Edwards",
            "publisher": "Cengage Learning",
            "cover_url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1000",
            "carreras": "Ingeniería de Sistemas,Ingeniería Civil,Computación,Ingeniería Industrial",
            "trimestres": "2,3,4",
            "materias": "Cálculo II,Matemáticas II,Cálculo Diferencial,Integrales",
            "tags": "derivadas, integrales, series infinitas, cálculo multivariable, vectores, límites",
            "description": "El texto canónico de cálculo más utilizado en facultades de ingeniería. Presenta de manera rigurosa pero pedagógica el cálculo diferencial e integral, con demostraciones geométricas, aplicaciones en física e ingeniería, y un compendio exhaustivo de ejercicios resueltos paso a paso.",
            "pages": 1184,
            "year": 2022,
            "rating_avg": 4.6,
            "ratings_count": 48,
            "star_5_count": 34,
            "star_4_count": 10,
            "star_3_count": 3,
            "star_2_count": 1,
            "star_1_count": 0,
        },
        {
            "title": "Cálculo Vectorial",
            "subtitle": "Geometría diferencial de curvas y campos vectoriales",
            "edition": "6ta Edición",
            "authors": "Jerrold E. Marsden & Anthony Tromba",
            "publisher": "Pearson Educación",
            "cover_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1000",
            "carreras": "Ingeniería de Sistemas,Ingeniería Civil,Computación",
            "trimestres": "3,4",
            "materias": "Cálculo III,Matemáticas III,Cálculo Vectorial",
            "tags": "gradiente, divergencia, rotacional, teorema de stokes, integrales de linea, green",
            "description": "Obra de referencia internacional para el estudio de funciones de varias variables, diferenciación en Rn, integrales múltiples y los teoremas fundamentales del análisis vectorial (Green, Stokes y Gauss).",
            "pages": 680,
            "year": 2019,
            "rating_avg": 4.7,
            "ratings_count": 32,
            "star_5_count": 24,
            "star_4_count": 6,
            "star_3_count": 2,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Investigación de Operaciones",
            "subtitle": "Modelos cuantitativos, optimización y teoría de colas",
            "edition": "10ma Edición",
            "authors": "Hamdy A. Taha",
            "publisher": "Pearson",
            "cover_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1000",
            "carreras": "Ingeniería de Sistemas,Ingeniería Industrial",
            "trimestres": "3,4,5",
            "materias": "Investigación Operativa,Optimización de Sistemas",
            "tags": "programacion lineal, simplex, transporte, redes, cadenas de markov, simulacion",
            "description": "Una guía completa y práctica que combina teoría matemática y aplicaciones en optimización y toma de decisiones empresariales e informáticas.",
            "pages": 840,
            "year": 2021,
            "rating_avg": 4.5,
            "ratings_count": 29,
            "star_5_count": 18,
            "star_4_count": 8,
            "star_3_count": 2,
            "star_2_count": 1,
            "star_1_count": 0,
        },
        {
            "title": "Fundamentos de Sistemas de Bases de Datos",
            "subtitle": "Modelado relacional, SQL avanzado y diseño de índices",
            "edition": "7ma Edición",
            "authors": "Abraham Silberschatz, Henry F. Korth & S. Sudarshan",
            "publisher": "McGraw-Hill",
            "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1000",
            "carreras": "Ingeniería de Sistemas,Computación",
            "trimestres": "3,4,5",
            "materias": "Bases de Datos I,Sistemas de Información",
            "tags": "sql, normalizacion, postgresql, algebra relacional, transacciones acid, indexacion",
            "description": "El clásico absoluto de la literatura informática para bases de datos relacionales y no relacionales. Incluye álgebra relacional pura y optimización de consultas SQL.",
            "pages": 1130,
            "year": 2020,
            "rating_avg": 4.8,
            "ratings_count": 55,
            "star_5_count": 42,
            "star_4_count": 11,
            "star_3_count": 2,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Programación en Kotlin: Papayita",
            "subtitle": "Guía práctica de desarrollo moderno y limpio para estudiantes",
            "edition": "2da Edición",
            "authors": "DevClub Universitario & Antonio Leiva",
            "publisher": "TechAcademic Press",
            "cover_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1000",
            "carreras": "Ingeniería de Sistemas,Computación",
            "trimestres": "3,4,5",
            "materias": "Programación Orientada a Objetos,Desarrollo Móvil",
            "tags": "kotlin, java, corrutinas, android, programacion funcional, oop",
            "description": "Aprende Kotlin de forma directa y sin complicaciones. Explicaciones concisas pensadas especialmente para alumnos que vienen de C++ o Java y quieren dominar desarrollo moderno.",
            "pages": 380,
            "year": 2023,
            "rating_avg": 4.9,
            "ratings_count": 40,
            "star_5_count": 36,
            "star_4_count": 4,
            "star_3_count": 0,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Python para Análisis de Datos y Algoritmos",
            "subtitle": "Tratamiento de datos con NumPy, Pandas y visualización",
            "edition": "3ra Edición",
            "authors": "Wes McKinney",
            "publisher": "O'Reilly Media",
            "cover_url": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1000",
            "carreras": "Ingeniería de Sistemas,Computación,Ingeniería Industrial",
            "trimestres": "2,3,4",
            "materias": "Algoritmos y Programación,Estructuras de Datos",
            "tags": "python, numpy, pandas, matplotlib, algoritmos, jupyter, machine learning",
            "description": "Instrucciones paso a paso para manipular, procesar, limpiar y procesar conjuntos de datos en Python de la mano del creador de la librería Pandas.",
            "pages": 560,
            "year": 2023,
            "rating_avg": 4.8,
            "ratings_count": 61,
            "star_5_count": 49,
            "star_4_count": 9,
            "star_3_count": 3,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Lenguaje SQL y Consultas Complejas",
            "subtitle": "Desde SELECT básico hasta Window Functions y CTEs",
            "edition": "4ta Edición",
            "authors": "Alan Beaulieu",
            "publisher": "O'Reilly",
            "cover_url": "https://images.unsplash.com/photo-1507842229451-79b1be88bb8e?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=1000",
            "carreras": "Ingeniería de Sistemas,Computación",
            "trimestres": "2,3",
            "materias": "Bases de Datos I,Programación Web",
            "tags": "sql, joins, group by, cte, window functions, indices, subconsultas",
            "description": "Manual conciso y didáctico para escribir consultas SQL eficientes, optimizar tiempos de respuesta y dominar las funciones de ventana en PostgreSQL y MySQL.",
            "pages": 340,
            "year": 2021,
            "rating_avg": 4.6,
            "ratings_count": 35,
            "star_5_count": 25,
            "star_4_count": 8,
            "star_3_count": 2,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Estructuras de Datos y Algoritmos en C++",
            "subtitle": "Complejidad algorítmica, árboles, grafos y tablas hash",
            "edition": "4ta Edición",
            "authors": "Mark Allen Weiss",
            "publisher": "Pearson",
            "cover_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1000",
            "carreras": "Ingeniería de Sistemas,Computación",
            "trimestres": "3,4",
            "materias": "Estructuras de Datos,Algoritmos",
            "tags": "c++, memoria dinamica, arboles binarios, avl, dijkstra, grafos, pilas, colas",
            "description": "Enfoque riguroso en el análisis de algoritmos Big-O, estructuras de memoria dinámicas y algoritmos clásicos de grafos.",
            "pages": 650,
            "year": 2020,
            "rating_avg": 4.7,
            "ratings_count": 28,
            "star_5_count": 20,
            "star_4_count": 6,
            "star_3_count": 2,
            "star_2_count": 0,
            "star_1_count": 0,
        },
        {
            "title": "Álgebra Lineal y sus Aplicaciones",
            "subtitle": "Espacios vectoriales, transformaciones y autovalores",
            "edition": "5ta Edición",
            "authors": "David C. Lay, Steven R. Lay & Judi J. McDonald",
            "publisher": "Pearson",
            "cover_url": "https://images.unsplash.com/photo-1532012164546-f432f2e3777f?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=1000",
            "carreras": "Ingeniería de Sistemas,Ingeniería Civil,Computación",
            "trimestres": "2,3",
            "materias": "Álgebra Lineal,Matemáticas I",
            "tags": "matrices, determinantes, espacios vectoriales, autovalores, ortogonalidad",
            "description": "Una introducción moderna al álgebra lineal que conecta la abstracción matemática con aplicaciones concretas en computación gráfica, machine learning y sistemas de ecuaciones.",
            "pages": 570,
            "year": 2021,
            "rating_avg": 4.5,
            "ratings_count": 45,
            "star_5_count": 28,
            "star_4_count": 12,
            "star_3_count": 4,
            "star_2_count": 1,
            "star_1_count": 0,
        },
        {
            "title": "Física para Ciencias e Ingeniería (Volumen 1)",
            "subtitle": "Mecánica, oscilaciones y ondas térmicas",
            "edition": "10ma Edición",
            "authors": "Raymond A. Serway & John W. Jewett",
            "publisher": "Cengage",
            "cover_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400",
            "header_banner_url": "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=1000",
            "carreras": "Ingeniería Civil,Ingeniería de Sistemas",
            "trimestres": "2,3",
            "materias": "Física I,Mecánica Clásica",
            "tags": "cinematica, leyes de newton, energia, cantidad de movimiento, rotacion",
            "description": "El texto fundamental de física universitaria para ingeniería. Explicaciones con diagramas detallados y problemas que incentivan el razonamiento físico.",
            "pages": 810,
            "year": 2021,
            "rating_avg": 4.4,
            "ratings_count": 38,
            "star_5_count": 22,
            "star_4_count": 11,
            "star_3_count": 4,
            "star_2_count": 1,
            "star_1_count": 0,
        }
    ]

    docs_created = []
    for d_data in docs_data:
        doc = Document(**d_data)
        db.add(doc)
        docs_created.append(doc)
    db.commit()

    # 4. Create Curated Lists ("Listas que podrían servirte" from Figma)
    doc_calculus = docs_created[0]
    doc_vector = docs_created[1]
    doc_io = docs_created[2]
    doc_db = docs_created[3]
    doc_kotlin = docs_created[4]
    doc_python = docs_created[5]
    doc_sql = docs_created[6]
    doc_ds = docs_created[7]

    lists_data = [
        {
            "title": "Mejores libros de Matemáticas II",
            "description": "La selección definitiva de Cálculo diferencial, integral y geometría para salvar el trimestre.",
            "creator_name": "Prof. Ramírez",
            "creator_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 3,
            "badge_color": "border-amber-500/40",
            "docs": [doc_calculus, doc_vector]
        },
        {
            "title": "Programación en Kotlin, papayita",
            "description": "Desde cero hasta apps modernas con corrutinas y arquitectura limpia.",
            "creator_name": "DevClub Universitario",
            "creator_avatar": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150",
            "carrera": "Computación",
            "trimestre": 3,
            "badge_color": "border-emerald-500/40",
            "docs": [doc_kotlin, doc_python]
        },
        {
            "title": "Lenguaje SQL y consultas, básico",
            "description": "Domina el modelo relacional, JOINs y diseño de esquemas para tus proyectos de Bases de Datos.",
            "creator_name": "Valentina Castro",
            "creator_avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            "carrera": "Ingeniería de Sistemas",
            "trimestre": 3,
            "badge_color": "border-sky-500/40",
            "docs": [doc_sql, doc_db]
        }
    ]

    for l_data in lists_data:
        docs = l_data.pop("docs")
        curated = CuratedList(**l_data)
        curated.documents = docs
        db.add(curated)
    db.commit()

    # 5. Create Realistic Friend Reviews (Mirroring Figma reviews verbatim!)
    carlos = users_created[1]
    valentina = users_created[2]
    andres = users_created[3]
    sofia = users_created[4]

    reviews_data = [
        {
            "user_id": carlos.id,
            "document_id": doc_calculus.id,
            "rating": 5,
            "content": "Excelente libro para entender cálculo diferencial y series. Los ejercicios resueltos de la sección 4 son clave para el parcial. Muy recomendado.",
            "likes_count": 14
        },
        {
            "user_id": valentina.id,
            "document_id": doc_db.id,
            "rating": 5,
            "content": "Para la segunda mitad del curso este libro es súper específico. Lo recomiendo con los ojos cerrados para bases de datos relacionales sin morir en el intento.",
            "likes_count": 19
        },
        {
            "user_id": andres.id,
            "document_id": doc_kotlin.id,
            "rating": 5,
            "content": "Los ejemplos de Kotlin van directos al grano y son súper didácticos. Perfecto para quien viene de C++ o Java y necesita arrancar rápido en Android.",
            "likes_count": 9
        },
        {
            "user_id": sofia.id,
            "document_id": doc_python.id,
            "rating": 5,
            "content": "Salvó mi trimestre con Pandas y NumPy. Las explicaciones de manipulación de arrays son las más claras que he leído.",
            "likes_count": 11
        },
        {
            "user_id": carlos.id,
            "document_id": doc_vector.id,
            "rating": 4,
            "content": "Los teoremas de Stokes y Gauss están muy bien ilustrados geométricamente. Imprescindible para Cálculo III.",
            "likes_count": 8
        },
        {
            "user_id": valentina.id,
            "document_id": doc_calculus.id,
            "rating": 5,
            "content": "Explica con mucha paciencia el paso a paso de las integrales por partes y sustitución trigonométrica. Me ayudó a sacar 20.",
            "likes_count": 16
        }
    ]

    for r_data in reviews_data:
        rev = Review(**r_data)
        db.add(rev)
    db.commit()

    # Recalculate stats on documents
    for doc in docs_created:
        doc.update_rating_stats()
    db.commit()

    # 6. Add initial bookmarks and interactions for Oscar
    db.add(Bookmark(user_id=oscar.id, document_id=doc_calculus.id))
    db.add(UserInteraction(user_id=oscar.id, document_id=doc_calculus.id, interaction_type="read"))
    db.add(UserInteraction(user_id=oscar.id, document_id=doc_sql.id, interaction_type="save"))
    db.commit()

    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
