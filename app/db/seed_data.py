"""
Database seeding data for Caribou Coffee Audit System
"""

DEFAULT_COFFEES = [
    {"name": "ANFA", "location": "Casablanca", "active": True},
    {"name": "CASA VOYAGEUR", "location": "Casablanca", "active": True},
    {"name": "MAARIF", "location": "Casablanca", "active": True},
    {"name": "RABAT AGDAL", "location": "Rabat", "active": True},
]

DEFAULT_ADMIN = {
    "email": "admin@caribou.ma",
    "password": "admin",
    "full_name": "Admin",
}

AUDIT_CATEGORIES_DATA = {
    "Hygiène & Sécurité": {
        "description": "Normes d'hygiène, propreté et sécurité alimentaire",
        "icon": "health_and_safety",
        "questions": [
            {"text": "Zone de préparation propre et désinfectée", "weight": 2, "correct_answer": "oui"},
            {"text": "Plans de travail nettoyés entre chaque usage", "weight": 1, "correct_answer": "oui"},
            {"text": "Lavage de mains respecté (fréquence, technique, savon)", "weight": 2, "correct_answer": "oui"},
            {"text": "Produits alimentaires stockés à bonne température", "weight": 3, "correct_answer": "oui"},
            {"text": "Frigos / congélateurs propres, organisés et avec thermomètre visible", "weight": 2, "correct_answer": "oui"},
            {"text": "Produit périmé", "weight": 3, "correct_answer": "non"},
            {"text": "Produit mal emballé", "weight": 2, "correct_answer": "non"},
            {"text": "Poubelles fermées, propres et vidées régulièrement", "weight": 1, "correct_answer": "oui"},
            {"text": "Respect du FIFO (First In First Out)", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Personnel & Connaissance": {
        "description": "Apparence, compétences et attitude du personnel",
        "icon": "badge",
        "questions": [
            {"text": "Uniformes complets, propres, conformes à la charte de la marque", "weight": 2, "correct_answer": "oui"},
            {"text": "Badge prénom visible", "weight": 1, "correct_answer": "oui"},
            {"text": "Staff connaît les recettes, allergènes, options (Milk, syrup, etc.)", "weight": 2, "correct_answer": "oui"},
            {"text": "Sait répondre sur les promotions / produits en cours", "weight": 1, "correct_answer": "oui"},
            {"text": "Réactivité, sourire, posture debout active", "weight": 2, "correct_answer": "oui"},
            {"text": "Connaissance des procédures sécurité / hygiène", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Qualité des produits": {
        "description": "Conformité et qualité des boissons et aliments servis",
        "icon": "local_cafe",
        "questions": [
            {"text": "Boissons conformes aux standards visuels (look, topping, dose)", "weight": 3, "correct_answer": "oui"},
            {"text": "Température des boissons chaude / froide conforme", "weight": 2, "correct_answer": "oui"},
            {"text": "Goût des boissons conforme (recette respectée)", "weight": 3, "correct_answer": "oui"},
            {"text": "Présentation des viennoiseries et snacks conforme", "weight": 2, "correct_answer": "oui"},
            {"text": "Traçabilité des produits ouverts", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Maintenance & Matériel": {
        "description": "État et entretien des équipements et installations",
        "icon": "build",
        "questions": [
            {"text": "TDS", "weight": 1, "correct_answer": "oui"},
            {"text": "PH", "weight": 1, "correct_answer": "oui"},
            {"text": "Machines à café nettoyées et fonctionnelles", "weight": 2, "correct_answer": "oui"},
            {"text": "Blender, fours, frigos : fonctionnels, propres, sans fuites/bruits", "weight": 2, "correct_answer": "oui"},
            {"text": "Ampoule grillée / prise cassée / câble apparent", "weight": 1, "correct_answer": "non"},
            {"text": "Aération / clim / chauffage fonctionnels", "weight": 2, "correct_answer": "oui"},
            {"text": "Autres", "weight": 1, "correct_answer": "oui"},
        ]
    },
    "Zone client & ambiance": {
        "description": "Propreté, confort et ambiance de la salle",
        "icon": "weekend",
        "questions": [
            {"text": "Sols propres, pas de déchets ni liquides visibles", "weight": 2, "correct_answer": "oui"},
            {"text": "Tables et chaises propres et bien positionnées", "weight": 1, "correct_answer": "oui"},
            {"text": "Musique de fond conforme aux playlists / ambiance calme", "weight": 1, "correct_answer": "oui"},
            {"text": "Odeur agréable (pas de cuisson excessive ou de déchets)", "weight": 1, "correct_answer": "oui"},
            {"text": "Présentoir propre et bien garni", "weight": 2, "correct_answer": "oui"},
            {"text": "Toilettes propres, fournies, avec check-list signée", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Gestion / Système": {
        "description": "Gestion de la caisse, systèmes et procédures opérationnelles",
        "icon": "point_of_sale",
        "questions": [
            {"text": "Fond De Caisse", "weight": 2, "correct_answer": "oui"},
            {"text": "Ticket supports fait pour tout les maintenance", "weight": 1, "correct_answer": "oui"},
            {"text": "Checklist mise à jour et complétée", "weight": 1, "correct_answer": "oui"},
            {"text": "Gestion de la salle, contrôle et suivi", "weight": 1, "correct_answer": "oui"},
            {"text": "Stratégie d'upselling, gestion des déchets", "weight": 1, "correct_answer": "oui"},
            {"text": "Caisse fonctionnelle avec fond de monnaie suffisant", "weight": 2, "correct_answer": "oui"},
            {"text": "TPE fonctionnel, tickets disponibles", "weight": 1, "correct_answer": "oui"},
            {"text": "Système Clyo / POS à jour (produits, prix, promos)", "weight": 1, "correct_answer": "oui"},
            {"text": "Procédures d'ouverture / fermeture respectées", "weight": 2, "correct_answer": "oui"},
            {"text": "Rapport de caisse / vente / stock bien tenu", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Stock / Réception": {
        "description": "Gestion du stock, réception et rangement des marchandises",
        "icon": "inventory",
        "questions": [
            {"text": "Réserve propre, rangée et sans carton au sol", "weight": 2, "correct_answer": "oui"},
            {"text": "Produits rangés sur étagères, non collés aux murs", "weight": 1, "correct_answer": "oui"},
            {"text": "Livraison vérifiée à réception (quantité, qualité, température)", "weight": 2, "correct_answer": "oui"},
            {"text": "Produits d'entretien séparés des produits alimentaires", "weight": 2, "correct_answer": "oui"},
        ]
    },
    "Marketing": {
        "description": "Outils marketing et communication en point de vente",
        "icon": "campaign",
        "questions": [
            {"text": "Tous les marketing Tools sont actualiser", "weight": 1, "correct_answer": "oui"},
        ]
    },
}
