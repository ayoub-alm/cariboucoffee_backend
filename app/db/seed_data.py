"""
Database seeding data for Caribou Coffee Audit System
"""

# Default Coffee Shops
DEFAULT_COFFEES = [
    {"name": "ANFA", "location": "Casablanca", "active": True},
    {"name": "CASA VOYAGEUR", "location": "Casablanca", "active": True},
    {"name": "MAARIF", "location": "Casablanca", "active": True},
    {"name": "RABAT AGDAL", "location": "Rabat", "active": True},
]

# Default Admin User
DEFAULT_ADMIN = {
    "email": "admin@caribou.ma",
    "password": "admin",
    "full_name": "Admin",
}

# Audit Categories with Questions
# Format: {category_name: {description, questions: [{text, weight}]}}
AUDIT_CATEGORIES_DATA = {
    "Hygiène et Propreté": {
        "description": "Audit des normes d'hygiène et de propreté",
        "questions": [
            {"text": "Les surfaces de travail sont propres et désinfectées", "weight": 2},
            {"text": "Les équipements sont en bon état de fonctionnement", "weight": 1},
            {"text": "Le personnel porte des vêtements propres et appropriés", "weight": 2},
            {"text": "Les produits alimentaires sont stockés à la bonne température", "weight": 3},
            {"text": "Les frigos et congélateurs sont propres, organisés avec thermomètre visible", "weight": 2},
            {"text": "Absence de produits périmés en stock ou en zone de préparation", "weight": 3},
            {"text": "Tous les produits sont bien emballés et stockés", "weight": 1},
            {"text": "Les poubelles sont fermées, propres et vidées", "weight": 1},
            {"text": "Le principe du FIFO (First In, First Out) est bien appliqué", "weight": 2},
        ]
    },
    "Service Client": {
        "description": "Audit de la qualité du service client",
        "questions": [
            {"text": "L'accueil client est chaleureux et professionnel", "weight": 3},
            {"text": "Les commandes sont prises avec précision", "weight": 2},
            {"text": "Le temps d'attente est raisonnable", "weight": 2},
            {"text": "Le personnel connaît bien le menu et peut conseiller", "weight": 2},
            {"text": "Les réclamations sont gérées avec professionnalisme", "weight": 3},
        ]
    },
    "Qualité des Produits": {
        "description": "Audit de la qualité et présentation des produits",
        "questions": [
            {"text": "Les boissons sont préparées selon les standards", "weight": 3},
            {"text": "La température des boissons est correcte", "weight": 2},
            {"text": "La présentation des produits est soignée", "weight": 2},
            {"text": "Les ingrédients utilisés sont frais et de qualité", "weight": 3},
            {"text": "Les portions respectent les standards établis", "weight": 2},
        ]
    },
    "Ambiance et Propreté du Local": {
        "description": "Audit de l'ambiance et de la propreté générale",
        "questions": [
            {"text": "Le local est propre et bien rangé", "weight": 2},
            {"text": "Les tables et chaises sont propres", "weight": 1},
            {"text": "Les toilettes sont propres et approvisionnées", "weight": 2},
            {"text": "L'éclairage est adéquat", "weight": 1},
            {"text": "La musique d'ambiance est appropriée", "weight": 1},
            {"text": "La température du local est confortable", "weight": 1},
        ]
    },
}
