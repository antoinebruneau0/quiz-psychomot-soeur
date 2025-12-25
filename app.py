import streamlit as st

import random



# --- CONFIGURATION DE LA PAGE ---

st.set_page_config(page_title="Psychomot' Master - Partiels Blancs", page_icon="🧠", layout="wide")



# --- CSS PRO & STYLE ---

st.markdown("""

<style>

    .stButton>button {

        width: 100%;

        border-radius: 8px;

        height: 3em;

        font-weight: bold;

        transition: all 0.3s;

    }

    .stButton>button:hover {

        transform: scale(1.02);

    }

    .correction-box {

        padding: 20px;

        border-radius: 10px;

        margin-top: 15px;

        background-color: #e3f2fd;

        border-left: 5px solid #1565c0;

        color: #0d47a1;

        font-size: 1.05em;

    }

    .question-card {

        background-color: #ffffff;

        padding: 25px;

        border-radius: 15px;

        box-shadow: 0 4px 15px rgba(0,0,0,0.05);

        margin-bottom: 25px;

        border: 1px solid #eee;

    }

    h1, h2, h3 { color: #2c3e50; }

    .tag-badge {

        background-color: #e0e0e0;

        color: #333;

        padding: 2px 8px;

        border-radius: 12px;

        font-size: 0.75em;

        margin-left: 10px;

    }

</style>

""", unsafe_allow_html=True)



# --- BASE DE DONNÉES MASSIVE (Générée depuis les PDF) ---

db_questions = {

    "MODULE 1: Santé Pub, Pharma, Hygiène": [

        # PHARMACOLOGIE

        {"q": "Dans le système ADME, à quoi correspond la lettre 'D' ?", "options": ["Digestion", "Dilution", "Distribution", "Dynamisation"], "answer": "Distribution", "type": "qcm", "explanation": "ADME = Absorption, Distribution (transport dans le sang vers les tissus), Métabolisme, Élimination.", "tag": "Pharma"},

        {"q": "Quelle est la définition de la biodisponibilité ?", "options": ["La vitesse d'élimination du médicament", "La fraction de la dose administrée qui atteint la circulation générale sous forme inchangée", "La toxicité du produit", "Le volume de distribution"], "answer": "La fraction de la dose administrée qui atteint la circulation générale sous forme inchangée", "type": "qcm", "explanation": "Par voie IV, la biodisponibilité est de 100%. Par voie orale, elle est < 100% à cause de l'effet de premier passage hépatique.", "tag": "Pharma"},

        {"q": "Qu'est-ce que l'effet de premier passage hépatique ?", "type": "ouverte", "answer": "La perte de principe actif lors de son premier passage par le foie (via la veine porte) avant d'atteindre la circulation générale.", "explanation": "Le foie métabolise/dégrade une partie du médicament absorbé par voie digestive.", "tag": "Pharma"},

        {"q": "Quelle est la différence entre un médicament Princeps et un Générique ?", "type": "ouverte", "answer": "Le Princeps est l'original breveté. Le Générique est sa copie (même principe actif, même dosage) commercialisée après la chute du brevet.", "explanation": "Les excipients peuvent changer, mais la bioéquivalence doit être prouvée.", "tag": "Pharma"},

        {"q": "Qu'est-ce qu'un excipient ?", "options": ["Le principe actif", "Une substance inactive aidant à la formulation (goût, forme, conservation)", "Un effet secondaire", "Un antidote"], "answer": "Une substance inactive aidant à la formulation (goût, forme, conservation)", "type": "qcm", "explanation": "Exemples : sucre, amidon, colorants. Certains ont des 'effets notoires' (allergies).", "tag": "Pharma"},

        {"q": "Définition de la demi-vie d'élimination (T1/2).", "type": "ouverte", "answer": "Temps nécessaire pour que la concentration plasmatique du médicament diminue de moitié (50%).", "explanation": "Il faut environ 5 à 7 demi-vies pour éliminer totalement le produit.", "tag": "Pharma"},

        {"q": "Qu'est-ce que la clairance ?", "options": ["Volume de plasma totalement épuré d'une substance par unité de temps", "Quantité d'urine par jour", "Vitesse de perfusion"], "answer": "Volume de plasma totalement épuré d'une substance par unité de temps", "type": "qcm", "explanation": "La clairance rénale (créatinine) évalue la fonction rénale.", "tag": "Pharma"},

        {"q": "Citez 3 voies d'administration parentérales.", "type": "ouverte", "answer": "Intraveineuse (IV), Intramusculaire (IM), Sous-cutanée (SC), Intradermique.", "explanation": "Parentérale = 'à côté du tube digestif' (injections).", "tag": "Pharma"},

        

        # SANTÉ PUBLIQUE & HISTOIRE

        {"q": "Loi Kouchner (4 mars 2002) : Apport principal ?", "options": ["Création de la Sécu", "Droits des malades (dossier médical, consentement) et qualité du système de santé", "Loi sur l'avortement"], "answer": "Droits des malades (dossier médical, consentement) et qualité du système de santé", "type": "qcm", "explanation": "Marque la fin du paternalisme médical. Le patient devient acteur.", "tag": "Loi"},

        {"q": "Quelle loi de 1838 a structuré la psychiatrie ?", "options": ["Loi sur les asiles (un par département)", "Loi sur les médicaments", "Loi HPST"], "answer": "Loi sur les asiles (un par département)", "type": "qcm", "explanation": "Loi Esquirol : obligation pour chaque département d'avoir un asile d'aliénés.", "tag": "Histoire"},

        {"q": "Lois Jules Ferry (1881-1882) : Que font-elles ?", "options": ["École laïque, gratuite et obligatoire", "Droit de vote des femmes", "Séparation Église/État"], "answer": "École laïque, gratuite et obligatoire", "type": "qcm", "explanation": "Fondement de l'école républicaine.", "tag": "Histoire"},

        {"q": "Définition de la santé selon l'OMS (1946).", "type": "ouverte", "answer": "État de complet bien-être physique, mental et social, et ne consiste pas seulement en une absence de maladie ou d'infirmité.", "explanation": "Définition positive et globale (bio-psycho-sociale).", "tag": "Concept"},

        {"q": "Qu'est-ce que la PMI ?", "options": ["Protection Médicale Interne", "Protection Maternelle et Infantile", "Pôle Médical Infirmier"], "answer": "Protection Maternelle et Infantile", "type": "qcm", "explanation": "Service départemental (créé en 1945) pour la santé des mères et des enfants (0-6 ans).", "tag": "Santé Pub"},

        

        # HYGIÈNE

        {"q": "Qu'est-ce qu'une Infection Associée aux Soins (IAS) ?", "type": "ouverte", "answer": "Infection acquise au cours d'une prise en charge (ni présente ni en incubation à l'admission). Délai > 48h.", "explanation": "Inclut les infections nosocomiales (hôpital) mais aussi en cabinet libéral, EHPAD, etc.", "tag": "Hygiène"},

        {"q": "Quelle est la durée d'une friction SHA (Solution Hydro-Alcoolique) ?", "options": ["10 sec", "30 sec (ou jusqu'à séchage)", "2 min"], "answer": "30 sec (ou jusqu'à séchage)", "type": "qcm", "explanation": "Efficacité maximale sur mains visuellement propres.", "tag": "Hygiène"},

        {"q": "Différence entre Asepsie et Antisepsie ?", "type": "ouverte", "answer": "Asepsie = Préventif (empêcher les microbes d'arriver). Antisepsie = Curatif/Action (éliminer les microbes sur tissus vivants).", "explanation": "On aseptise un bloc opératoire (l'environnement), on fait une antisepsie sur la peau du patient.", "tag": "Hygiène"},

        {"q": "Que signifie DASRI ?", "options": ["Déchets d'Activités de Soins à Risques Infectieux", "Déchets Alimentaires Sans Risque", "Déchets Assimilés aux Soins"], "answer": "Déchets d'Activités de Soins à Risques Infectieux", "type": "qcm", "explanation": "Poubelles jaunes (piquants, coupants, sang, risques bio).", "tag": "Hygiène"},

        {"q": "Quels sont les 5 moments de l'hygiène des mains (OMS) ?", "type": "ouverte", "answer": "1. Avant contact patient, 2. Avant geste aseptique, 3. Après risque liquide biologique, 4. Après contact patient, 5. Après contact environnement.", "explanation": "La friction SHA est la méthode de référence.", "tag": "Hygiène"},

        {"q": "Qu'est-ce qu'un biofilm ?", "type": "ouverte", "answer": "Communauté de micro-organismes adhérant entre eux et à une surface, sécrétant une matrice protectrice.", "explanation": "Très résistant aux désinfectants (ex: sur prothèses, cathéters).", "tag": "Hygiène"},

    ],



    "MODULE 2: Anatomie & Neuroanatomie": [

        # OSTEOLOGIE RACHIS & TRONC

        {"q": "Quelles sont les courbures du rachis dans le plan sagittal ?", "type": "ouverte", "answer": "Lordose cervicale, Cyphose thoracique, Lordose lombaire, Cyphose sacrée.", "explanation": "Lordose = creux (concave en arrière). Cyphose = bosse (convexe en arrière).", "tag": "Rachis"},

        {"q": "Combien de vertèbres cervicales ?", "options": ["5", "7", "12"], "answer": "7", "type": "qcm", "explanation": "C1 à C7. (Attention, il y a 8 nerfs cervicaux mais 7 vertèbres).", "tag": "Rachis"},

        {"q": "Quel est le nom de C1 et C2 ?", "options": ["Atlas et Axis", "Axis et Atlas", "Atlas et Prominens"], "answer": "Atlas et Axis", "type": "qcm", "explanation": "C1 Atlas porte la tête. C2 Axis possède la dent (processus odontoïde) pour la rotation.", "tag": "Rachis"},

        {"q": "Qu'est-ce que le médiastin ?", "type": "ouverte", "answer": "La région médiane du thorax, située entre les deux poumons.", "explanation": "Contient le cœur, l'œsophage, la trachée, les gros vaisseaux.", "tag": "Thorax"},

        

        # MEMBRE SUPÉRIEUR

        {"q": "Citez les os du Carpe (poignet).", "type": "ouverte", "answer": "Scaphoïde, Lunatum, Triquetrum, Pisiforme (Rangée 1) / Trapèze, Trapézoïde, Capitatum, Hamatum (Rangée 2).", "explanation": "Mnémotechnique : 'Sous Le Temps Pluvieux, Tu Te Captures Hâtivement' (ou autre).", "tag": "Membre Sup"},

        {"q": "Quels sont les muscles de la coiffe des rotateurs ?", "type": "ouverte", "answer": "Supra-épineux, Infra-épineux, Petit rond, Subscapulaire.", "explanation": "Ils stabilisent la tête humérale dans la glène.", "tag": "Membre Sup"},

        {"q": "Où se situe le nerf ulnaire au niveau du coude ?", "options": ["Dans la gouttière épitrochléenne (médial)", "En avant du biceps", "En dehors"], "answer": "Dans la gouttière épitrochléenne (médial)", "type": "qcm", "explanation": "C'est le 'petit juif' quand on se cogne le coude.", "tag": "Membre Sup"},

        {"q": "Quel mouvement permet le Biceps Brachial ?", "options": ["Extension coude", "Flexion coude + Supination", "Pronation"], "answer": "Flexion coude + Supination", "type": "qcm", "explanation": "C'est le principal supinateur coude fléchi.", "tag": "Myologie"},



        # MEMBRE INFÉRIEUR

        {"q": "Quels os forment l'os coxal (bassin) ?", "options": ["Ilion, Ischion, Pubis", "Sacrum, Coccyx", "Fémur, Tibia"], "answer": "Ilion, Ischion, Pubis", "type": "qcm", "explanation": "Ils se réunissent au niveau de l'acétabulum (cotyle) à la puberté.", "tag": "Membre Inf"},

        {"q": "Qu'est-ce que l'acétabulum ?", "type": "ouverte", "answer": "La cavité articulaire de l'os coxal qui reçoit la tête du fémur.", "explanation": "Forme une énarthrose (sphéroïde).", "tag": "Membre Inf"},

        {"q": "Quels sont les ligaments croisés du genou ?", "type": "ouverte", "answer": "LCA (Antérieur) et LCP (Postérieur).", "explanation": "Ils assurent la stabilité antéro-postérieure (pivot central).", "tag": "Genou"},

        {"q": "Quel os est sésamoïde dans le genou ?", "options": ["La Patella (Rotule)", "Le Fémur", "Le Tibia"], "answer": "La Patella (Rotule)", "type": "qcm", "explanation": "Inclus dans le tendon du quadriceps.", "tag": "Genou"},

        {"q": "Classification de Garden (Fractures col fémur) : Garden III ?", "options": ["Non déplacée", "Engrenée valgus", "Déplacée en varus, charnière conservée", "Totalement déplacée, tête libre"], "answer": "Déplacée en varus, charnière conservée", "type": "qcm", "explanation": "Risque de nécrose de la tête fémorale.", "tag": "Trauma"},



        # CRÂNE & NEUROANATOMIE

        {"q": "Combien d'os composent le crâne (boîte crânienne) ?", "options": ["8", "14", "22"], "answer": "8", "type": "qcm", "explanation": "Frontal, Occipital, 2 Pariétaux, 2 Temporaux, Sphénoïde, Ethmoïde.", "tag": "Crâne"},

        {"q": "Quel est le seul os mobile de la face ?", "answer": "La Mandibule", "type": "qcm", "options": ["Maxillaire", "Mandibule", "Zygomatique"], "explanation": "Articulée avec l'os temporal (ATM).", "tag": "Face"},

        {"q": "Où se situe le Liquide Cérébro-Spinal (LCS) ?", "options": ["Espace épidural", "Espace sous-arachnoïdien", "Espace sous-dural"], "answer": "Espace sous-arachnoïdien", "type": "qcm", "explanation": "Entre l'arachnoïde et la pie-mère.", "tag": "Neuro"},

        {"q": "Quel lobe cérébral gère la vision ?", "options": ["Frontal", "Pariétal", "Occipital", "Temporal"], "answer": "Occipital", "type": "qcm", "explanation": "Cortex visuel primaire (V1).", "tag": "Neuro"},

        {"q": "Rôle du Cervelet ?", "type": "ouverte", "answer": "Équilibre, Coordination des mouvements, Tonus, Apprentissage moteur.", "explanation": "C'est le 'chef d'orchestre' de la motricité fine.", "tag": "Neuro"},

        {"q": "De quoi est composé le Système Nerveux Central (SNC) ?", "options": ["Cerveau + Nerfs", "Encéphale + Moelle épinière", "Juste le cerveau"], "answer": "Encéphale + Moelle épinière", "type": "qcm", "explanation": "L'encéphale comprend Cerveau, Cervelet, Tronc cérébral.", "tag": "Neuro"},

    ],



    "MODULE 3: Physiologie": [

        # CELLULE & NERF

        {"q": "Qu'est-ce que l'homéostasie ?", "type": "ouverte", "answer": "Maintien de la stabilité du milieu intérieur (équilibre) malgré les variations extérieures.", "explanation": "Concerne pH, température, glycémie, etc.", "tag": "Général"},

        {"q": "Potentiel d'action : Quel ion entre massivement lors de la dépolarisation ?", "options": ["Sodium (Na+)", "Potassium (K+)", "Chlore (Cl-)"], "answer": "Sodium (Na+)", "type": "qcm", "explanation": "Entrée rapide de Na+ rend l'intérieur de la cellule positif.", "tag": "Neurophy"},

        {"q": "Qu'est-ce qu'une synapse ?", "type": "ouverte", "answer": "Zone de contact fonctionnelle entre deux neurones (ou neurone/muscle) permettant la transmission de l'influx.", "explanation": "Peut être électrique ou chimique (neurotransmetteurs).", "tag": "Neurophy"},



        # MUSCLE & CARDIO

        {"q": "Protéines contractiles du muscle ?", "options": ["Actine et Myosine", "Collagène", "Kératine"], "answer": "Actine et Myosine", "type": "qcm", "explanation": "Le glissement des têtes de myosine sur l'actine raccourcit le sarcomère.", "tag": "Muscle"},

        {"q": "Définition Systole / Diastole.", "type": "ouverte", "answer": "Systole = Contraction (éjection). Diastole = Relâchement (remplissage).", "explanation": "La pression artérielle se note Systolique/Diastolique.", "tag": "Cardio"},

        {"q": "Où se situe le nœud sinusal (pacemaker naturel) ?", "options": ["Oreillette Droite", "Ventricule Gauche", "Septum"], "answer": "Oreillette Droite", "type": "qcm", "explanation": "Il donne le rythme de base (60-100 bpm).", "tag": "Cardio"},

        {"q": "Quel vaisseau ramène le sang oxygéné des poumons au cœur ?", "options": ["Artère pulmonaire", "Veine pulmonaire", "Aorte"], "answer": "Veine pulmonaire", "type": "qcm", "explanation": "Piège ! C'est la seule veine riche en O2.", "tag": "Cardio"},



        # RESPI, DIGESTIF, RENAL

        {"q": "Qu'est-ce que l'hématose ?", "type": "ouverte", "answer": "Échanges gazeux (O2/CO2) entre l'air alvéolaire et le sang capillaire pulmonaire.", "explanation": "Le sang devient rouge vif (oxygéné).", "tag": "Respi"},

        {"q": "Quel est le muscle inspirateur principal ?", "answer": "Le Diaphragme", "type": "qcm", "options": ["Intercostaux", "Diaphragme", "Abdominaux"], "explanation": "Innervé par le nerf phrénique.", "tag": "Respi"},

        {"q": "Rôle de la bile ?", "options": ["Digérer les protéines", "Émulsionner les graisses (lipides)", "Réguler le sucre"], "answer": "Émulsionner les graisses (lipides)", "type": "qcm", "explanation": "Produite par le foie, stockée dans la vésicule.", "tag": "Digestif"},

        {"q": "Unité fonctionnelle du rein ?", "options": ["Le néphron", "Le hile", "L'uretère"], "answer": "Le néphron", "type": "qcm", "explanation": "1 million par rein. Filtre le sang.", "tag": "Rénal"},

        {"q": "Quelle hormone rénale stimule la production de globules rouges ?", "options": ["Rénine", "EPO (Érythropoïétine)", "Insuline"], "answer": "EPO (Érythropoïétine)", "type": "qcm", "explanation": "C'est pourquoi l'insuffisance rénale cause une anémie.", "tag": "Rénal"},

        {"q": "Qu'est-ce que le DFG ?", "type": "ouverte", "answer": "Débit de Filtration Glomérulaire. Volume de sang filtré par le rein par minute.", "explanation": "Normal > 90 ml/min. Évalue le stade de l'insuffisance rénale.", "tag": "Rénal"},

    ],



    "MODULE 4: Psychologie": [

        # PSYCHANALYSE FREUDIENNE

        {"q": "Stade Oral (Freud) : Âge et enjeux ?", "type": "ouverte", "answer": "0-1 an. Zone buccale. Enjeux : Incorporation, relation à la mère (sein), plaisir/frustration.", "explanation": "Mode de relation anaclitique (dépendance).", "tag": "Freud"},

        {"q": "Stade Anal : Âge et enjeux ?", "type": "ouverte", "answer": "1-3 ans. Contrôle sphinctérien. Enjeux : Maîtrise/Emprise, Don/Retenue, Autonomie/Opposition ('Non').", "explanation": "Pulsion sadique-anale.", "tag": "Freud"},

        {"q": "Complexe d'Oedipe : Quel stade ?", "options": ["Oral", "Anal", "Phallique", "Latence"], "answer": "Phallique", "type": "qcm", "explanation": "3-6 ans. Désir pour le parent de sexe opposé, rivalité avec l'autre. Angoisse de castration.", "tag": "Freud"},

        {"q": "Instances de la personnalité (2ème topique) ?", "options": ["Inconscient/Préconscient/Conscient", "Ça/Moi/Surmoi"], "answer": "Ça/Moi/Surmoi", "type": "qcm", "explanation": "Ça = Pulsions. Moi = Réalité/Médiateur. Surmoi = Interdits/Morale.", "tag": "Freud"},



        # AUTEURS & CONCEPTS

        {"q": "Stade du miroir : Auteur et concept ?", "type": "ouverte", "answer": "Wallon (et Lacan). 6-18 mois. L'enfant reconnaît son image, unifie son corps morcelé et construit son 'Je'.", "explanation": "Moment jubilatoire fondateur de l'identité.", "tag": "Wallon"},

        {"q": "Qu'est-ce que l'Objet Transitionnel (Winnicott) ?", "type": "ouverte", "answer": "Première possession 'non-moi' (doudou) qui permet de supporter l'absence de la mère et de faire le lien entre réalité interne et externe.", "explanation": "Aire transitionnelle.", "tag": "Winnicott"},

        {"q": "La préoccupation maternelle primaire (Winnicott) ?", "type": "ouverte", "answer": "État de sensibilité accrue de la mère (fin grossesse/début vie) lui permettant de s'identifier aux besoins du bébé.", "explanation": "Une 'maladie normale'.", "tag": "Winnicott"},

        {"q": "Positions de Mélanie Klein ?", "options": ["Schizo-paranoïde puis Dépressive", "Orale puis Anale", "Sécure puis Insécure"], "answer": "Schizo-paranoïde puis Dépressive", "type": "qcm", "explanation": "Schizo-paranoïde (clivage bon/mauvais objet). Dépressive (objet total, culpabilité, réparation).", "tag": "Klein"},

        {"q": "Fonction Alpha (Bion) ?", "type": "ouverte", "answer": "Capacité de la mère (rêverie) à transformer les éléments Bêta (sensations brutes, angoisses) du bébé en éléments Alpha (pensables, assimilables).", "explanation": "Le bébé introjecte cette fonction pour apprendre à penser.", "tag": "Bion"},

        {"q": "Théorie de l'Attachement (Bowlby) : Définition.", "type": "ouverte", "answer": "Besoin primaire de lien affectif durable et sécurisant avec une figure de soin pour assurer la survie et la sécurité.", "explanation": "Base de sécurité pour explorer le monde.", "tag": "Bowlby"},

        {"q": "Les 3 organisateurs de Spitz ?", "options": ["Sourire, Angoisse 8 mois, Le Non", "Marche, Parole, Propreté"], "answer": "Sourire, Angoisse 8 mois, Le Non", "type": "qcm", "explanation": "Étapes clés de la structuration du Moi.", "tag": "Spitz"},

        {"q": "Piaget : Stade Sensorimoteur ?", "options": ["0-2 ans", "2-7 ans", "7-12 ans"], "answer": "0-2 ans", "type": "qcm", "explanation": "Intelligence pratique, basée sur l'action et les sens. Permanence de l'objet.", "tag": "Piaget"},

    ],



    "MODULE 5: Psychiatrie": [

        # HISTOIRE & CADRE

        {"q": "Qui a 'libéré les fous' de leurs chaînes (1793) ?", "options": ["Freud", "Pinel", "Charcot"], "answer": "Pinel", "type": "qcm", "explanation": "Naissance de la psychiatrie et du traitement moral.", "tag": "Histoire"},

        {"q": "Loi de 1838 ?", "options": ["Création du secteur", "Création des asiles départementaux"], "answer": "Création des asiles départementaux", "type": "qcm", "explanation": "Esquirol. Institutionnalise l'enfermement.", "tag": "Histoire"},

        {"q": "Qu'est-ce que la Sectorisation (1960) ?", "type": "ouverte", "answer": "Organisation géodémographique : une même équipe soigne la population d'une zone (secteur) à l'hôpital et à l'extérieur (CMP).", "explanation": "Continuité des soins, proximité, 'hors les murs'.", "tag": "Orga"},

        {"q": "Différence HDT / HO (Loi 1990) devenus ASPDT / ASPBRE (Loi 2011) ?", "type": "ouverte", "answer": "Soins à la demande d'un tiers (famille) vs Soins sur décision du représentant de l'état (Préfet/Maire) pour ordre public.", "explanation": "Soins Sans Consentement.", "tag": "Loi"},



        # SEMIOLOGIE & NOSOGRAPHIE

        {"q": "Différence Névrose / Psychose (Classique) ?", "type": "ouverte", "answer": "Névrose : Conflit intrapsychique, réalité conservée, conscience du trouble. Psychose : Perte de contact avec la réalité, anosognosie, délire.", "explanation": "Névrose = Refoulement. Psychose = Déni/Forclusion.", "tag": "Nosographie"},

        {"q": "Qu'est-ce qu'un délire ?", "type": "ouverte", "answer": "Conviction inébranlable en une idée fausse, en désaccord avec la réalité.", "explanation": "Mécanismes : Hallucinatoire, Interprétatif, Intuitif, Imaginatif.", "tag": "Sémio"},

        {"q": "Symptômes négatifs de la schizophrénie ?", "type": "ouverte", "answer": "Apragmatisme (inactivité), Aboulie (manque de volonté), Émoussement affectif, Retrait social, Alogie.", "explanation": "Opposés aux symptômes positifs (délires, hallucinations).", "tag": "Schizo"},

        {"q": "Triade de l'Autisme (ou Dyade DSM-5) ?", "type": "ouverte", "answer": "1. Déficit communication/interactions sociales. 2. Caractère restreint et répétitif des comportements/intérêts.", "explanation": "On ajoute souvent les particularités sensorielles.", "tag": "TSA"},

        {"q": "Qu'est-ce que l'anhédonie ?", "options": ["Perte de l'élan vital", "Incapacité à ressentir du plaisir", "Tristesse"], "answer": "Incapacité à ressentir du plaisir", "type": "qcm", "explanation": "Symptôme clé de la dépression mélancolique.", "tag": "Sémio"},

        {"q": "Qu'est-ce qu'une dysharmonie évolutive ?", "type": "ouverte", "answer": "Concept français (CFTMEA). Pathologie limite de l'enfant. Développement hétérogène, failles narcissiques, angoisses de séparation, instabilité.", "explanation": "Ni tout à fait névrose, ni psychose.", "tag": "Pédopsy"},

        {"q": "Définition de l'addiction ?", "type": "ouverte", "answer": "Impossibilité répété de contrôler un comportement et la poursuite de ce comportement malgré la connaissance de ses conséquences négatives.", "explanation": "Circuit de la récompense perturbé. Craving.", "tag": "Addicto"},

    ],



    "MODULE 6: Psychomotricité Théorique": [

        # DÉFINITIONS & CONCEPTS

        {"q": "Définition de la Psychomotricité (Globale).", "type": "ouverte", "answer": "Discipline qui considère l'homme dans sa globalité, liant fonctions motrices, cognitives et affectives. Agir sur le corps pour agir sur le psychisme.", "explanation": "Lien soma-psyché.", "tag": "Déf"},

        {"q": "Dialogue Tonique (Wallon/Ajuriaguerra) ?", "type": "ouverte", "answer": "Mode fondamental de communication et d'échange émotionnel mère-enfant passant par les variations du tonus musculaire.", "explanation": "Le tonus est la toile de fond de l'émotion.", "tag": "Concept"},

        {"q": "Différence Schéma Corporel / Image du Corps (Dolto) ?", "type": "ouverte", "answer": "Schéma = Réalité physiologique, universel, conscient, évolutif. Image = Inconsciente, propre à l'histoire affective du sujet, relationnelle.", "explanation": "On peut avoir un schéma corporel intact mais une image du corps blessée.", "tag": "Concept"},

        {"q": "Loi Céphalo-caudale ?", "options": ["Contrôle du centre vers les extrémités", "Contrôle de la tête vers les pieds"], "answer": "Contrôle de la tête vers les pieds", "type": "qcm", "explanation": "Tenu de tête -> Assis -> Debout.", "tag": "Dvlpmt"},

        {"q": "Loi Proximo-distale ?", "options": ["Contrôle du centre vers les extrémités", "Contrôle de la tête vers les pieds"], "answer": "Contrôle du centre vers les extrémités", "type": "qcm", "explanation": "Épaules -> Mains -> Doigts.", "tag": "Dvlpmt"},

        

        # HISTOIRE & CADRE PRO

        {"q": "Qui a créé la première chaire de psychomotricité en 1947 ?", "options": ["Giselle Soubiran", "Julian de Ajuriaguerra", "Henri Wallon"], "answer": "Julian de Ajuriaguerra", "type": "qcm", "explanation": "À l'hôpital Henri Rousselle (Sainte-Anne). Avec Soubiran pour la pratique.", "tag": "Histoire"},

        {"q": "Date du Diplôme d'État (DE) ?", "options": ["1960", "1974", "1988"], "answer": "1974", "type": "qcm", "explanation": "15 Février 1974.", "tag": "Cadre"},

        {"q": "Date du Décret de Compétence (Actes) ?", "options": ["1974", "1988", "2004"], "answer": "1988", "type": "qcm", "explanation": "Définit ce qu'on a le droit de faire (bilan, rééducation...).", "tag": "Cadre"},

        {"q": "Le bilan psychomoteur est-il obligatoire ?", "options": ["Oui, avant toute prise en charge", "Non, facultatif"], "answer": "Oui, avant toute prise en charge", "type": "qcm", "explanation": "Prescrit par le médecin, il permet le diagnostic psychomoteur et le projet thérapeutique.", "tag": "Pratique"},

        

        # CLINIQUE

        {"q": "Qu'est-ce qu'une médiation thérapeutique ?", "type": "ouverte", "answer": "Utilisation d'un tiers (objet, matière, activité) pour faciliter la relation, l'expression et contourner les défenses.", "explanation": "Médium malléable (Roussillon). Ex: Eau, Argile, Cheval.", "tag": "Pratique"},

        {"q": "Qu'est-ce que la paratonie ?", "options": ["Absence de tonus", "Freinage tonique involontaire lors de la mobilisation passive", "Tremblement"], "answer": "Freinage tonique involontaire lors de la mobilisation passive", "type": "qcm", "explanation": "Signe d'une difficulté de relâchement liée à l'anxiété ou au vieillissement.", "tag": "Sémio"},

        {"q": "Réflexes archaïques : Citez-en 3.", "type": "ouverte", "answer": "Agrippement (Grasping), Moro, Marche automatique, Succion, RTAC (Escrimeur).", "explanation": "Témoignent de la maturation du système sous-cortical. Doivent s'intégrer.", "tag": "Dvlpmt"},

        {"q": "Qu'est-ce que la sensori-motricité ?", "type": "ouverte", "answer": "Lien indissociable entre la sensation (afférence) et le mouvement (efférence). Le mouvement crée la sensation et la sensation guide le mouvement.", "explanation": "Boucle sensori-motrice (Bullinger, Piaget).", "tag": "Concept"},

    ]

}



# --- LOGIQUE DE L'APPLICATION ---

st.sidebar.image("https://img.icons8.com/color/96/000000/brain--v1.png", width=80)

st.sidebar.title("🩺 Psychomot' Master")

st.sidebar.markdown("**Mode Révision Partiel**")

st.sidebar.info("Coche les modules que tu veux bosser aujourd'hui.")



# Sélection du module

module_choisi = st.sidebar.selectbox("📚 Choisir un module :", list(db_questions.keys()))



# Initialisation des variables de session pour stocker les résultats

if 'answers' not in st.session_state:

    st.session_state.answers = {}

if 'show_explanation' not in st.session_state:

    st.session_state.show_explanation = {}



st.title(f"🎓 {module_choisi}")

st.write("Réponds aux questions pour vérifier tes connaissances. Prends ton temps, c'est comme au partiel !")

st.write("---")



questions = db_questions[module_choisi]

score_module = 0



for i, q in enumerate(questions):

    st.markdown(f"<div class='question-card'><h3>Question {i+1} <span class='tag-badge'>{q['tag']}</span></h3>", unsafe_allow_html=True)

    st.write(f"**{q['q']}**")

    

    # --- GESTION DES QCM ---

    if q["type"] == "qcm":

        key_radio = f"radio_{module_choisi}_{i}"

        user_choice = st.radio("Ta réponse :", q["options"], key=key_radio, index=None)

        

        if st.button(f"Valider Q{i+1}", key=f"btn_{module_choisi}_{i}"):

            st.session_state.show_explanation[f"{module_choisi}_{i}"] = True

        

        if st.session_state.show_explanation.get(f"{module_choisi}_{i}"):

            if user_choice == q["answer"]:

                st.success("✅ Bonne réponse !")

            else:

                st.error(f"❌ Faux. La réponse était : {q['answer']}")

            

            st.markdown(f"<div class='correction-box'>💡 <b>Explication :</b> {q['explanation']}</div>", unsafe_allow_html=True)



    # --- GESTION DES QUESTIONS OUVERTES ---

    elif q["type"] == "ouverte":

        st.text_area("Écris ta réponse ici (pour toi) :", key=f"text_{module_choisi}_{i}", height=100)

        

        if st.button(f"Voir la correction Q{i+1}", key=f"btn_open_{module_choisi}_{i}"):

             st.session_state.show_explanation[f"{module_choisi}_{i}"] = True

        

        if st.session_state.show_explanation.get(f"{module_choisi}_{i}"):

            st.info("Compare ta réponse avec le corrigé type ci-dessous :")

            st.markdown(f"<div class='correction-box'>✅ <b>Réponse attendue :</b> {q['answer']}<br><br>💡 <b>Détail :</b> {q['explanation']}</div>", unsafe_allow_html=True)

            st.write("*(Si tu as les mots-clés, compte-toi le point !)*")



    st.markdown("</div>", unsafe_allow_html=True)



# --- BOUTON RESET ---

if st.sidebar.button("🗑️ Effacer mes réponses et recommencer"):

    st.session_state.show_explanation = {}

    st.session_state.answers = {}

    st.rerun()



st.sidebar.write("---")

st.sidebar.caption("Généré par ton Assistant IA 🤖 - Basé sur tes cours officiels.")