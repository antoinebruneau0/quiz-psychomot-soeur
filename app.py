import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
import json
import re
import collections
import copy
from pathlib import Path

try:
    import PyPDF2
except Exception:
    PyPDF2 = None


def _shorten_option_for_display(text: str, max_len: int = 110) -> str:
    """Dans cette version, on n'abrège plus les propositions à l'affichage.
    On traite le problème via des distracteurs plus crédibles (même longueur)."""
    return str(text)


# --- CSS PRO ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #4e73df; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .feedback-box { padding: 15px; border-radius: 10px; margin-top: 10px; background-color: #e8f4f8; border-left: 5px solid #2e86de; color: #1e3799; }
    .question-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e0e0e0; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DONNÉES MASSIVE (INTEGRALE) ---
db_questions = {
   "MODULE 1: Santé Pub, Pharma, Hygiène": [
       
        # --- NIVEAU BASIQUE (25%) ---
        {
            "q": "Quelle est la définition exacte de la biodisponibilité d'un médicament ?",
        "options": [
            "La vitesse à laquelle le médicament est éliminé par les reins",
            "La proportion de principe actif qui atteint la circulation générale inchangée et la vitesse à laquelle cela se produit",
            "La quantité totale de médicament ingérée par le patient",
            "La capacité du médicament à se fixer aux protéines plasmatiques"
        ],
        "answer": "La proportion de principe actif qui atteint la circulation générale inchangée et la vitesse à laquelle cela se produit",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une notion clé[cite: 38]. Pour la voie intraveineuse (IV), la biodisponibilité est par définition de 100% car il n'y a pas de barrière à franchir. Pour la voie orale, elle est souvent inférieure à cause de l'effet de premier passage hépatique.",
        "tag": "Pharmacocinétique"
    },
    {
        "q": "Qu'est-ce qu'un médicament générique par rapport au princeps ?",
        "type": "ouverte",
        "answer": "C'est une copie d'un médicament original (princeps) dont le brevet est tombé dans le domaine public. Il a la même composition qualitative et quantitative en principe actif et la même forme pharmaceutique.",
        "level": "Basique",
        "explanation": "Le générique doit prouver sa bioéquivalence[cite: 34]. Attention, les excipients peuvent être différents, ce qui peut changer le goût ou la couleur, mais pas l'efficacité thérapeutique.",
        "tag": "Définition"
    },
    {
        "q": "Parmi les voies d'administration suivantes, laquelle permet d'éviter l'effet de premier passage hépatique ?",
        "options": ["La voie orale (per os)", "La voie intraveineuse", "La voie rectale (partiellement)", "La voie sublinguale"],
        "answer": "La voie intraveineuse",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La voie IV injecte le produit directement dans le sang[cite: 41]. La voie sublinguale évite aussi le foie (passage direct dans la veine cave supérieure). La voie orale oblige le médicament à passer par le foie (via la veine porte) avant d'atteindre le cœur.",
        "tag": "Pharmacocinétique"
    },
    {
        "q": "Quelle est la fonction principale d'un excipient dans un médicament ?",
        "options": ["Soigner la maladie", "Donner une forme, un goût et assurer la stabilité sans avoir d'activité thérapeutique", "Augmenter le prix du médicament", "Remplacer le principe actif"],
        "answer": "Donner une forme, un goût et assurer la stabilité sans avoir d'activité thérapeutique",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'excipient sert à la fabrication, à la conservation et à l'acceptabilité (goût, couleur)[cite: 15]. Certains excipients dits 'à effet notoire' (sucre, lactose) peuvent toutefois être mal tolérés par certains patients.",
        "tag": "Galénique"
    },
    {
        "q": "Que signifie l'acronyme ADME en pharmacocinétique ?",
        "options": ["Administration, Distribution, Médication, Efficacité", "Absorption, Distribution, Métabolisme, Élimination", "Absorption, Digestion, Mastication, Excrétion", "Action, Durée, Mesure, Évaluation"],
        "answer": "Absorption, Distribution, Métabolisme, Élimination",
        "type": "qcm",
        "level": "Basique",
       "explanation": "Ce sont les 4 étapes du devenir du médicament dans l'organisme[cite: 50]. L'organisme agit sur le médicament (Pharmacocinétique), contrairement à la Pharmacodynamie où c'est le médicament qui agit sur l'organisme.",
        "tag": "Pharmacocinétique"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Pourquoi la liaison aux protéines plasmatiques (ex: albumine) est-elle importante en pharmacologie ?",
        "type": "ouverte",
        "answer": "Car seule la fraction libre (non liée) du médicament est active, peut diffuser dans les tissus et être éliminée. La fraction liée sert de réserve.",
        "level": "Intermédiaire",
        "explanation": "Si deux médicaments entrent en compétition pour se lier à la même protéine, l'un peut chasser l'autre, augmentant brutalement sa fraction libre et donc le risque de surdosage toxique[cite: 81].",
        "tag": "Distribution"
    },
    {
        "q": "Qu'appelle-t-on un 'effet de premier passage hépatique' ?",
        "options": [
            "Le fait que le médicament passe d'abord par le cœur",
            "La perte de principe actif métabolisé par le foie avant d'atteindre la circulation générale lors d'une prise orale",
            "L'élimination rénale immédiate",
            "L'absorption par l'estomac"
        ],
        "answer": "La perte de principe actif métabolisé par le foie avant d'atteindre la circulation générale lors d'une prise orale",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Après absorption intestinale, le sang passe par la veine porte vers le foie. Le foie, véritable usine chimique, peut détruire une grande partie du médicament avant qu'il n'ait pu agir ailleurs[cite: 68].",
        "tag": "Pharmacocinétique"
    },
    {
        "q": "Quelle est la différence entre Pharmacocinétique et Pharmacodynamie ?",
        "type": "ouverte",
        "answer": "La Pharmacocinétique étudie l'effet de l'organisme sur le médicament (ADME). La Pharmacodynamie étudie l'effet du médicament sur l'organisme (mécanisme d'action, récepteurs).",
        "level": "Intermédiaire",
        "explanation": "Pour retenir : Cinétique = Mouvement du médicament dans le corps. Dynamique = Force/Action du médicament sur la maladie[cite: 46, 47].",
        "tag": "Définition"
    },
    {
        "q": "En quoi consiste l'induction enzymatique au niveau du foie ?",
        "options": [
            "Le médicament détruit les cellules du foie",
            "Un médicament stimule l'activité des enzymes hépatiques, accélérant ainsi la dégradation d'autres médicaments",
            "Le foie arrête de fonctionner",
            "Le médicament bloque les enzymes, augmentant la toxicité des autres produits"
        ],
        "answer": "Un médicament stimule l'activité des enzymes hépatiques, accélérant ainsi la dégradation d'autres médicaments",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Un 'inducteur' enzymatique (ex: alcool chronique, millepertuis) va rendre le foie plus performant pour détruire les médicaments. Résultat : les autres traitements deviennent MOINS efficaces car éliminés trop vite[cite: 100].",
        "tag": "Métabolisme"
    },
    {
        "q": "Quels sont les facteurs physiologiques pouvant modifier la biodisponibilité d'un médicament ?",
        "type": "ouverte",
        "answer": "L'âge (nourrisson/personne âgée), la grossesse, l'alimentation (à jeun ou non), et certaines pathologies (insuffisance hépatique).",
        "level": "Intermédiaire",
        "explanation": "Par exemple, chez la personne âgée, le métabolisme hépatique ralentit, ce qui augmente la biodisponibilité et le risque de surdosage[cite: 66].",
        "tag": "Variabilité"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le concept de 'Volume de distribution' (Vd) et son implication clinique.",
        "type": "ouverte",
        "answer": "C'est un volume fictif théorique représentant la capacité d'un médicament à diffuser dans les tissus. Un Vd élevé signifie que le médicament diffuse beaucoup dans les tissus (et peu dans le sang).",
        "level": "Avancé",
        "explanation": "Si le Vd est grand, le médicament est 'caché' dans les graisses ou les organes. Il sera difficile à éliminer par dialyse en cas d'intoxication. Si le Vd est petit, le médicament reste concentré dans le sang[cite: 77].",
        "tag": "Pharmacocinétique"
    },
    {
        "q": "Concernant le métabolisme des médicaments, quel est le rôle du cytochrome P450 (notamment CYP3A4) ?",
        "options": [
            "Il transporte le médicament dans le sang",
            "C'est une enzyme clé du foie responsable de la biotransformation de nombreux médicaments",
            "Il protège l'estomac de l'acidité",
            "Il permet l'élimination rénale directe"
        ],
        "answer": "C'est une enzyme clé du foie responsable de la biotransformation de nombreux médicaments",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le CYP3A4 est l'enzyme la plus sollicitée. Elle est au cœur de nombreuses interactions médicamenteuses : si elle est inhibée (ex: par le jus de pamplemousse), les médicaments qu'elle dégrade vont s'accumuler et devenir toxiques[cite: 103].",
        "tag": "Métabolisme"
    },
    {
        "q": "Un patient sous AVK (anticoagulant) prend un inhibiteur enzymatique. Quelle est la conséquence clinique probable ?",
        "options": [
            "Diminution de l'effet anticoagulant -> Risque de thrombose",
            "Augmentation de la concentration d'AVK -> Risque hémorragique majeur",
            "Aucun effet, les AVK ne sont pas métabolisés",
            "Amélioration de la digestion"
        ],
        "answer": "Augmentation de la concentration d'AVK -> Risque hémorragique majeur",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'inhibiteur empêche le foie de dégrader l'AVK. L'AVK s'accumule donc dans le sang (surdosage), fluidifiant le sang à l'excès. C'est une urgence iatrogène[cite: 101].",
        "tag": "Iatrogénie"
    },
    {
        "q": "Quelle est la nuance précise entre 'Iatrogénie' et 'Erreur médicale' ?",
        "type": "ouverte",
        "answer": "La iatrogénie désigne les conséquences indésirables d'un acte médical ou médicament, même s'il a été correctement prescrit/réalisé (sans erreur). L'erreur médicale implique une faute (négligence, mauvaise dose).",
        "level": "Avancé",
        "explanation": "Une chute suite à un médicament qui donne des vertiges (effet secondaire connu) est de la iatrogénie. Donner le mauvais médicament est une erreur. La iatrogénie est souvent évitable mais pas toujours fautive[cite: 894].",
        "tag": "Législation"
    },
    {
        "q": "Dans le cadre de l'élimination rénale, qu'est-ce que la 'Clairance' ?",
        "options": [
            "La couleur des urines",
            "Le volume de plasma totalement épuré d'une substance par unité de temps",
            "La quantité de médicament avalée",
            "Le temps de demi-vie"
        ],
        "answer": "Le volume de plasma totalement épuré d'une substance par unité de temps",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le meilleur indicateur de la fonction rénale (ex: Clairance de la créatinine). Si la clairance baisse (insuffisance rénale), il faut réduire les doses de médicaments pour éviter le surdosage[cite: 95].",
        "tag": "Élimination"
    },
    {
        "q": "Analysez le risque particulier des médicaments à 'Marge Thérapeutique Étroite'.",
        "type": "ouverte",
        "answer": "Ce sont des médicaments où la dose efficace est très proche de la dose toxique. Une légère variation de concentration (due à une interaction ou un problème rénal) peut avoir des conséquences graves.",
        "level": "Avancé",
        "explanation": "Exemples : Lithium, Digoxine, AVK, Antiépileptiques. Ils nécessitent souvent un dosage plasmatique régulier pour vérifier qu'on est dans la bonne zone.",
        "tag": "Sécurité"
    },
    {
        "q": "Quel est le mécanisme de l'interaction médicament-aliment avec le jus de pamplemousse ?",
        "options": [
            "Il augmente l'acidité gastrique",
            "C'est un puissant inhibiteur enzymatique intestinal (CYP3A4) qui augmente l'absorption de certains médicaments",
            "Il est inducteur enzymatique",
            "Il empêche l'absorption des médicaments"
        ],
        "answer": "C'est un puissant inhibiteur enzymatique intestinal (CYP3A4) qui augmente l'absorption de certains médicaments",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "En bloquant les enzymes de la paroi intestinale, le jus de pamplemousse laisse passer beaucoup plus de médicament dans le sang que prévu (effet de premier passage réduit), créant un surdosage parfois mortel (ex: avec certains immunosuppresseurs)[cite: 100].",
        "tag": "Interaction"
    },
    {
        "q": "Définissez la 'Demi-vie' (T1/2) et son utilité pour atteindre l'état d'équilibre (Steady State).",
        "type": "ouverte",
        "answer": "Temps nécessaire pour éliminer 50% du médicament. Il faut environ 5 demi-vies à posologie constante pour atteindre l'état d'équilibre (concentration stable dans le sang).",
        "level": "Avancé",
        "explanation": "Si T1/2 = 4h, l'équilibre est atteint en 20h. C'est crucial pour savoir quand le traitement sera pleinement efficace.",
        "tag": "Pharmacocinétique"
    },
    {
        "q": "Pourquoi les personnes âgées sont-elles plus sensibles aux psychotropes (Benzodiazépines) sur le plan pharmacocinétique ?",
        "options": [
            "Elles sont plus stressées",
            "Leur volume de distribution change (plus de graisse, moins d'eau) et leur élimination rénale/hépatique diminue",
            "Elles ne boivent pas assez",
            "Leurs récepteurs ne fonctionnent plus"
        ],
        "answer": "Leur volume de distribution change (plus de graisse, moins d'eau) et leur élimination rénale/hépatique diminue",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Les BZD sont lipophiles (aiment le gras). Comme la personne âgée a plus de masse grasse relative, les BZD s'y stockent (Vd augmente) et s'éliminent moins vite (T1/2 augmente), entraînant somnolence et chutes[cite: 233].",
        "tag": "Gériatrie"
    },
    {
        "q": "Qu'est-ce qu'un médicament tératogène ?",
        "options": [
            "Qui provoque le cancer",
            "Qui provoque des malformations chez le fœtus s'il est pris pendant la grossesse",
            "Qui agit sur la terre",
            "Qui est périmé"
        ],
        "answer": "Qui provoque des malformations chez le fœtus s'il est pris pendant la grossesse",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'exemple tristement célèbre est la Thalidomide. La période la plus critique est le premier trimestre (organogenèse). C'est une contre-indication absolue.",
        "tag": "Toxicité"
    },
    {
        "q": "Quel est le délai minimum pour qu'une infection soit qualifiée d'Infection Associée aux Soins (IAS) ou nosocomiale après une admission ?",
        "options": ["12 heures", "24 heures", "48 heures", "7 jours"],
        "answer": "48 heures",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Pour être reconnue comme IAS, un délai de 48h est à observer entre l'admission et la survenue de l'infection. Si elle apparaît avant, elle était probablement déjà en incubation à l'arrivée.",
        "tag": "Hygiène - Définition"
    },
    {
        "q": "Quelle est la différence d'efficacité entre le lavage simple (eau + savon) et la friction hydro-alcoolique (SHA) ?",
        "options": [
            "Le savon tue 100% des bactéries, la SHA 50%",
            "C'est équivalent",
            "Le lavage élimine environ 50% de la flore, la SHA élimine quasiment 100% de la flore",
            "La SHA ne fait que parfumer les mains"
        ],
        "answer": "Le lavage élimine environ 50% de la flore, la SHA élimine quasiment 100% de la flore",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le lavage est mécanique (il enlève les souillures). La SHA est chimique (elle tue les germes). La SHA est donc plus efficace microbiologiquement, sauf sur les mains souillées macroscopiquement.",
        "tag": "Hygiène des mains"
    },
    {
        "q": "Quels sont les pré-requis indispensables pour une hygiène des mains efficace ?",
        "type": "ouverte",
        "answer": "Avant-bras dégagés (manches courtes), ongles courts et sans vernis (ni faux ongles), et absence totale de bijoux (bagues, montres, bracelets).",
        "level": "Basique",
        "explanation": "Les bijoux et les faux ongles sont des nids à bactéries que ni le savon ni la SHA ne peuvent atteindre correctement.",
        "tag": "Hygiène des mains"
    },
    {
        "q": "À qui s'appliquent les Précautions Standard ?",
        "options": [
            "Uniquement aux patients infectés par le VIH",
            "Uniquement aux patients porteurs de BMR",
            "À tout patient, quel que soit son statut infectieux, pour tout soin et par tout professionnel",
            "Uniquement en chirurgie"
        ],
        "answer": "À tout patient, quel que soit son statut infectieux, pour tout soin et par tout professionnel",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la règle d'or. On considère *a priori* que tout patient et tout liquide biologique est potentiellement contaminant. C'est le socle de la prévention.",
        "tag": "Précautions Standard"
    },
    {
        "q": "Que sont les DASRI ?",
        "options": ["Déchets Alimentaires Sans Risque Infectieux", "Déchets d'Activités de Soins à Risques Infectieux", "Dispositifs d'Aide aux Soins et Rééducation Infirmière", "Déchets Anatomiques Stériles Réutilisables"],
        "answer": "Déchets d'Activités de Soins à Risques Infectieux",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Ils incluent les objets piquants/coupants, les produits sanguins, les déchets anatomiques ou tout déchet présentant un risque infectieux.",
        "tag": "Déchets"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la distinction entre une infection endogène et une infection exogène ?",
        "type": "ouverte",
        "answer": "Endogène : l'infection provient des propres germes du patient (sa flore). Exogène : l'infection est transmise par l'extérieur (soignant, autre patient, environnement, matériel).",
        "level": "Intermédiaire",
        "explanation": "Une infection urinaire sur sonde est souvent endogène (les bactéries remontent). Une grippe attrapée à l'hôpital est exogène (transmission croisée).",
        "tag": "Microbiologie"
    },
    {
        "q": "Pour une prothèse ou un implant chirurgical, quel est le délai pour considérer une infection comme nosocomiale (IAS) ?",
        "options": ["48 heures", "30 jours", "1 an", "10 ans"],
        "answer": "1 an",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Si du matériel étranger est posé (prothèse de hanche, pacemaker), le délai est étendu à 1 an après l'intervention, car les germes peuvent se développer très lentement sur ces matériaux.",
        "tag": "Réglementation IAS"
    },
    {
        "q": "Qu'est-ce qu'un 'Biofilm' bactérien ?",
        "type": "ouverte",
        "answer": "C'est une communauté de micro-organismes qui adhèrent entre eux et à une surface, protégés par une matrice qu'ils sécrètent. Cela les rend très résistants aux désinfectants et aux antibiotiques.",
        "level": "Intermédiaire",
        "explanation": "Le biofilm se forme sur les cathéters, les prothèses, ou même les robinets. C'est une forteresse pour les bactéries.",
        "tag": "Microbiologie"
    },
    {
        "q": "Quelle est la particularité biologique des Prions par rapport aux virus et bactéries ?",
        "options": [
            "Ce sont des champignons géants",
            "Ce sont des protéines infectieuses sans acide nucléique (ADN/ARN)",
            "Ce sont des parasites visibles à l'œil nu",
            "Ils ne sont pas pathogènes"
        ],
        "answer": "Ce sont des protéines infectieuses sans acide nucléique (ADN/ARN)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le prion est une protéine mal repliée qui transmet son anomalie. Ils résistent aux méthodes classiques de stérilisation (autoclave standard). Ex: Maladie de Creutzfeldt-Jakob.",
        "tag": "Microbiologie"
    },
    {
        "q": "Dans la gestion des déchets (DASRI), quel est le délai limite d'évacuation si la production est supérieure à 100 kg par semaine ?",
        "options": ["24 heures", "72 heures", "7 jours", "1 mois"],
        "answer": "72 heures",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Plus on produit de déchets, plus il faut les évacuer vite. >100kg/semaine = 72h. Entre 15kg/mois et 100kg/semaine = 7 jours.",
        "tag": "Déchets"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Pourquoi la friction hydro-alcoolique (SHA) est-elle inefficace contre le Clostridium difficile et la Gale, et que faut-il faire ?",
        "options": [
            "Elle fixe le germe sur la peau -> Il faut mettre de l'alcool pur",
            "Ces germes sont sporulés ou protégés (parasites) et résistent à l'alcool -> Il faut laver les mains (action mécanique) et porter des gants",
            "Elle est efficace, c'est une légende",
            "Il faut utiliser de l'eau de Javel sur les mains"
        ],
        "answer": "Ces germes sont sporulés ou protégés (parasites) et résistent à l'alcool -> Il faut laver les mains (action mécanique) et porter des gants",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'exception majeure. En cas de Clostridium (diarrhée) ou de Gale, le lavage des mains au savon est OBLIGATOIRE pour éliminer physiquement les spores/parasites, suivi éventuellement d'une friction.",
        "tag": "Précautions Complémentaires"
    },
    {
        "q": "Citez les 4 facteurs combinés du 'Cercle de Sinner' indispensables pour un bionettoyage efficace.",
        "type": "ouverte",
        "answer": "Action Chimique (produit), Action Mécanique (frotter), Température, et Temps d'action.",
        "level": "Avancé",
        "explanation": "Si l'un diminue (ex: on frotte moins fort), il faut compenser par les autres (ex: laisser agir plus longtemps ou mettre plus de produit).",
        "tag": "Hygiène Environnement"
    },
    {
        "q": "Qu'est-ce qu'une BMR et quel type de précaution impose-t-elle ?",
        "options": [
            "Bactérie Morte Récemment -> Aucune précaution",
            "Bactérie Multi-Résistante aux antibiotiques -> Précautions Complémentaires CONTACT (Gants/Surblouse si soin direct)",
            "Bactérie Mutante Rare -> Isolement d'air strict",
            "Bonne Méthode de Rééducation -> Aucune"
        ],
        "answer": "Bactérie Multi-Résistante aux antibiotiques -> Précautions Complémentaires CONTACT (Gants/Surblouse si soin direct)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Ex: SARM (Staphylocoque doré) ou BLSE. Le risque est l'impasse thérapeutique. On isole le patient 'techniquement' (chambre seule si possible, matériel dédié) pour éviter la transmission croisée.",
        "tag": "Microbiologie"
    },
    {
        "q": "En cas d'Accident d'Exposition au Sang (AES) par piqûre, quelle est la procédure immédiate exacte ?",
        "type": "ouverte",
        "answer": "Ne pas faire saigner. Laver immédiatement à l'eau et au savon. Rincer. Désinfecter (Dakin ou Javel diluée ou Alcool 70°) en assurant un temps de contact d'au moins 5 minutes.",
        "level": "Avancé",
        "explanation": "Le temps de contact de 5 minutes est crucial pour inactiver les virus potentiels (VIH, VHC). Ensuite, direction les Urgences/Médecine du travail pour évaluation du risque.",
        "tag": "Sécurité"
    },
    {
        "q": "Quelle est la différence fondamentale entre les précautions 'Gouttelettes' et 'Air' ?",
        "options": [
            "C'est la même chose",
            "Gouttelettes = transmission courte distance (>5µm), masque chirurgical suffisant. Air = particules fines (<5µm) en suspension, masque FFP2 obligatoire",
            "Gouttelettes = masque FFP2. Air = masque chirurgical",
            "Air = transmission par la peau"
        ],
        "answer": "Gouttelettes = transmission courte distance (>5µm), masque chirurgical suffisant. Air = particules fines (<5µm) en suspension, masque FFP2 obligatoire",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La grippe est 'Gouttelettes' (elle tombe par terre après 1m). La tuberculose ou la rougeole sont 'Air' (elles flottent dans la pièce, il faut filtrer l'air inspiré avec un FFP2).",
        "tag": "Précautions Complémentaires"
    },
    {
        "q": "Pourquoi ne faut-il jamais recapuchonner une aiguille souillée ?",
        "type": "ouverte",
        "answer": "C'est la cause principale d'AES (piqûre accidentelle). Il faut jeter l'aiguille directement dans le collecteur OPCT (jaune) situé à portée de main.",
        "level": "Avancé",
        "explanation": "Le geste de 'recapuchonner' amène souvent les doigts vers la pointe de l'aiguille. C'est strictement interdit par les bonnes pratiques.",
        "tag": "Sécurité"
    },
    {
        "q": "Quels sont les trois facteurs de risque principaux favorisant la survenue d'une infection nosocomiale (IAS) ?",
        "options": [
            "La météo, la nourriture, le sommeil",
            "Les actes invasifs (sondes, cathéters), l'état pathologique du patient (immunodépression) et l'environnement de soins",
            "Le manque de personnel uniquement",
            "La visite des familles"
        ],
        "answer": "Les actes invasifs (sondes, cathéters), l'état pathologique du patient (immunodépression) et l'environnement de soins",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Plus on est envahi de tuyaux (portes d'entrée), plus on est fragile (défenses basses), et plus on est exposé à des germes résistants, plus le risque est élevé.",
        "tag": "Hygiène"
    },
    {
        "q": "Dans le tri des déchets, où doit-on jeter une couche d'un patient non infecté ?",
        "options": ["DASRI (Sac jaune)", "DAOM (Déchets Ménagers - Sac noir/blanc)", "Filière papier", "Filière radioactive"],
        "answer": "DAOM (Déchets Ménagers - Sac noir/blanc)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Sauf si le patient a une infection transmissible par les selles ou est à l'isolement, les déchets d'hygiène classiques vont en DAOM. Mettre trop de choses en DASRI coûte très cher et pollue (incinération spécifique).",
        "tag": "Déchets"
    },
    {
        "q": "Définissez la 'flore résidente' (commensale) par rapport à la 'flore transitoire' sur les mains.",
        "type": "ouverte",
        "answer": "La flore résidente est celle qui vit naturellement sur notre peau (peu pathogène). La flore transitoire est celle qu'on ramasse au contact des patients/surfaces (souvent pathogène).",
        "level": "Avancé",
        "explanation": "Le but de l'hygiène des mains est surtout d'éliminer la flore transitoire avant de passer à un autre patient. La friction SHA préserve mieux la flore résidente que le lavage répété qui abîme la peau.",
        "tag": "Microbiologie"
    },
    {
        "q": "Quelle est la particularité des déchets issus de la médecine nucléaire (ex: patients traités à l'Iode 131) ?",
        "options": [
            "Ils vont en DASRI classiques",
            "Ils doivent être stockés en décroissance radioactive avant d'être éliminés",
            "On les jette dans l'évier",
            "Ils sont recyclables"
        ],
        "answer": "Ils doivent être stockés en décroissance radioactive avant d'être éliminés",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Ils sont isolés dans des locaux plombés le temps que la radioactivité baisse en dessous des seuils légaux, puis ils rejoignent la filière classique ou DASRI.",
        "tag": "Déchets Spéciaux"
    },
    {
        "q": "Quelle est la différence fondamentale entre un 'Symptôme' et un 'Signe' en sémiologie ?",
        "options": [
            "C'est la même chose",
            "Le symptôme est subjectif (décrit par le patient), le signe est objectif (constaté par le soignant)",
            "Le symptôme est grave, le signe est bénin",
            "Le signe vient avant le symptôme"
        ],
        "answer": "Le symptôme est subjectif (décrit par le patient), le signe est objectif (constaté par le soignant)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La douleur est un symptôme (ressenti). Une rougeur ou une tachycardie mesurée sont des signes (observables). L'ensemble permet de poser un diagnostic[cite: 904, 908].",
        "tag": "Sémiologie"
    },
    {
        "q": "En histoire de l'éducation, qu'ont apporté les lois Jules Ferry de 1881-1882 ?",
        "options": [
            "L'école maternelle obligatoire",
            "L'école laïque, gratuite et obligatoire",
            "L'université pour tous",
            "L'interdiction du châtiment corporel"
        ],
        "answer": "L'école laïque, gratuite et obligatoire",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le fondement de l'école républicaine moderne en France, rendant l'instruction primaire obligatoire pour tous les enfants[cite: 1380].",
        "tag": "Histoire Éducation"
    },
    {
        "q": "Que signifie étymologiquement le terme 'Épidémiologie' ?",
        "options": ["L'étude de la peau", "L'étude de ce qui arrive 'sur le peuple'", "La science des épidémies uniquement", "Le traitement des virus"],
        "answer": "L'étude de ce qui arrive 'sur le peuple'",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Du grec 'Epi' (sur), 'Demos' (peuple) et 'Logos' (étude). Elle étudie la distribution des problèmes de santé dans les populations [cite: 870-872].",
        "tag": "Santé Publique"
    },
    {
        "q": "Quel est le principe central de la pédagogie Montessori ?",
        "type": "ouverte",
        "answer": "L'enfant est acteur de son développement ('Aide-moi à faire seul'). L'éducateur observe et fournit un environnement stimulant mais n'intervient pas directement pour diriger.",
        "level": "Basique",
        "explanation": "Maria Montessori, première femme médecin en Italie, a basé sa méthode sur l'autonomie et le respect du rythme individuel de l'enfant [cite: 1366-1368].",
        "tag": "Pédagogie"
    },
    {
        "q": "Qu'est-ce que l'anamnèse lors d'une consultation médicale ?",
        "options": ["L'examen physique", "L'interrogatoire du patient pour retracer l'histoire de sa maladie et ses antécédents", "La prescription de médicaments", "L'analyse de sang"],
        "answer": "L'interrogatoire du patient pour retracer l'histoire de sa maladie et ses antécédents",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la première étape cruciale de la démarche clinique. Elle recueille les informations subjectives (plaintes) et objectives (antécédents)[cite: 916].",
        "tag": "Sémiologie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quels sont les trois éléments constituant le 'Triangle Pédagogique' de Jean Houssaye ?",
        "type": "ouverte",
        "answer": "L'Enseignant, L'Apprenant, et Le Savoir.",
        "level": "Intermédiaire",
        "explanation": "Ce triangle définit les relations : Enseigner (Enseignant-Savoir), Former (Enseignant-Apprenant) et Apprendre (Apprenant-Savoir) [cite: 1347-1353].",
        "tag": "Pédagogie"
    },
    {
        "q": "Définissez le concept d'Iatrogénie (ou iatrogène).",
        "type": "ouverte",
        "answer": "Conséquences indésirables ou négatives sur l'état de santé provoquées par un acte médical ou un médicament, même en l'absence d'erreur du soignant.",
        "level": "Intermédiaire",
        "explanation": "Le terme vient de 'iatros' (médecin). Cela inclut les effets secondaires prévisibles mais aussi les complications imprévues d'un traitement justifié[cite: 894].",
        "tag": "Santé Publique"
    },
    {
        "q": "Quelle est la différence entre 'Didactique' et 'Pédagogie' ?",
        "options": [
            "La didactique concerne l'enfant, la pédagogie l'adulte",
            "La didactique se focalise sur la transmission du Savoir (contenu), la pédagogie se focalise sur la relation et l'Apprenant (méthode)",
            "C'est la même chose",
            "La pédagogie est une science exacte, pas la didactique"
        ],
        "answer": "La didactique se focalise sur la transmission du Savoir (contenu), la pédagogie se focalise sur la relation et l'Apprenant (méthode)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "La didactique s'intéresse à 'comment enseigner ce contenu spécifique' (transposition didactique). La pédagogie s'intéresse à 'comment l'enfant apprend et grandit'[cite: 1339, 1344].",
        "tag": "Pédagogie"
    },
    {
        "q": "En sémiologie, qu'appelle-t-on une 'Altération de l'État Général' (AEG) ? Citez les 3 signes majeurs (les 3 A).",
        "type": "ouverte",
        "answer": "Asthénie (fatigue), Anorexie (perte d'appétit), Amaigrissement (perte de poids).",
        "level": "Intermédiaire",
        "explanation": "La présence de ces trois signes simultanément est un signal d'alarme important pouvant indiquer une pathologie grave (cancer, tuberculose, dépression sévère) [cite: 990-993].",
        "tag": "Sémiologie"
    },
    {
        "q": "Selon Winslow (1920), quel est le but ultime de la Santé Publique ?",
        "options": [
            "Vendre des médicaments",
            "Prévenir les maladies, prolonger la vie et promouvoir la santé physique à travers des efforts communautaires",
            "Soigner uniquement les gens à l'hôpital",
            "Remplacer les médecins libéraux"
        ],
        "answer": "Prévenir les maladies, prolonger la vie et promouvoir la santé physique à travers des efforts communautaires",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est une définition fondatrice qui intègre l'assainissement, le contrôle des infections et l'éducation à l'hygiène[cite: 863].",
        "tag": "Santé Publique"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Quelle nuance précise votre cours fait-il entre 'Prévention' et 'Prophylaxie' ?",
        "type": "ouverte",
        "answer": "La prophylaxie désigne spécifiquement l'ensemble des méthodes pour protéger un individu/groupe contre l'apparition et la transmission d'une maladie (barrière active). La prévention est un terme plus large incluant l'éducation et la promotion de la santé.",
        "level": "Avancé",
        "explanation": "Le cours précise bien que ces termes ne sont pas interchangeables malgré l'usage courant [cite: 892-893]. La prophylaxie a souvent une connotation plus 'médicale/technique' (ex: prophylaxie du paludisme).",
        "tag": "Santé Publique"
    },
    {
        "q": "En sociologie du corps, qu'est-ce que Marcel Mauss appelle les 'Techniques du corps' ?",
        "options": [
            "Les méthodes de musculation",
            "Les façons dont les hommes, société par société, savent traditionnellement se servir de leur corps (marcher, nager, dormir)",
            "Les techniques chirurgicales",
            "La manière dont le cerveau contrôle les muscles"
        ],
        "answer": "Les façons dont les hommes, société par société, savent traditionnellement se servir de leur corps (marcher, nager, dormir)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Il n'y a pas de façon 'naturelle' de marcher ou de s'asseoir. Tout est acquis par éducation et mimétisme social. C'est le concept d'Habitus corporel [cite: 818-819].",
        "tag": "Sociologie"
    },
    {
        "q": "Expliquez la distinction sociologique entre les sociétés 'traditionnelles' et 'individualistes' concernant le corps.",
        "type": "ouverte",
        "answer": "Dans les sociétés traditionnelles, le corps n'est pas une frontière rigoureuse (il est relié au groupe/cosmos). Dans les sociétés individualistes, le corps fonctionne comme une frontière qui distingue et isole l'individu des autres.",
        "level": "Avancé",
        "explanation": "Cela influence la perception de la maladie et de la douleur. En occident (individualiste), 'mon' corps est ma propriété privée[cite: 801, 810].",
        "tag": "Sociologie"
    },
    {
        "q": "Qu'est-ce qu'un 'Diagnostic Différentiel' ?",
        "type": "ouverte",
        "answer": "C'est la méthode consistant à lister les pathologies présentant des symptômes similaires à ceux du patient, pour les éliminer une par une et trouver la bonne.",
        "level": "Avancé",
        "explanation": "Contrairement au diagnostic positif (ce que c'est), le diagnostic différentiel (ce que ce n'est pas) permet d'éviter les erreurs en envisageant toutes les hypothèses[cite: 878].",
        "tag": "Démarche Clinique"
    },
    {
        "q": "Dans la pédagogie de Janusz Korczak, quel est le rôle symbolique de la 'boîte aux lettres' ?",
        "options": [
            "Envoyer du courrier aux parents",
            "Permettre à l'enfant de différer sa réaction (ex: violence) en écrivant, favorisant ainsi la réflexion et la régulation émotionnelle",
            "Apprendre à écrire",
            "Dénoncer les autres élèves"
        ],
        "answer": "Permettre à l'enfant de différer sa réaction (ex: violence) en écrivant, favorisant ainsi la réflexion et la régulation émotionnelle",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Korczak utilisait l'écriture et le délai (24h avant une confrontation) pour pacifier les relations et responsabiliser les enfants [cite: 1375-1376].",
        "tag": "Pédagogie"
    },
    {
        "q": "Qu'est-ce que le 'Syndrome de Détresse Respiratoire Aiguë' (SDRA) et quels sont ses signes cliniques majeurs ?",
        "type": "ouverte",
        "answer": "C'est une défaillance pulmonaire grave (œdème lésionnel). Signes : Dyspnée brutale, Polypnée superficielle, Cyanose (hypoxie), Tirage intercostal et Râles crépitants.",
        "level": "Avancé",
        "explanation": "C'est l'exemple type d'un 'Syndrome' : un ensemble de signes cliniques et biologiques décrivant un état pathologique critique [cite: 1173, 1177-1180].",
        "tag": "Sémiologie"
    },
    {
        "q": "En sémiologie respiratoire, quelle est la différence entre une toux productive et une toux sèche ?",
        "options": [
            "La toux sèche fait plus mal",
            "La toux productive ramène des expectorations (mucus/pus), la toux sèche est irritative sans rejet",
            "La toux productive est virale, la sèche est bactérienne",
            "Aucune différence"
        ],
        "answer": "La toux productive ramène des expectorations (mucus/pus), la toux sèche est irritative sans rejet",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cette distinction oriente le diagnostic (bronchite bactérienne vs asthme/virus) et le traitement (ne pas bloquer une toux productive qui évacue les germes !) [cite: 1119-1120].",
        "tag": "Sémiologie"
    },
    {
        "q": "Définissez la 'Transposition Didactique'.",
        "type": "ouverte",
        "answer": "C'est le processus de transformation du 'Savoir Savant' (universitaire, complexe) en 'Savoir Enseigné' (accessible, adapté au niveau des élèves).",
        "level": "Avancé",
        "explanation": "C'est le cœur du métier d'enseignant ou de formateur : rendre digeste une information complexe sans la dénaturer[cite: 1342].",
        "tag": "Pédagogie"
    },
    {
        "q": "Quelle est la particularité de la méthode Steiner (Anthroposophie) concernant les cycles d'apprentissage ?",
        "options": [
            "Les cours changent toutes les heures",
            "On travaille par 'périodes' d'une même matière pendant 3 à 4 semaines, avec le même professeur sur plusieurs années",
            "Il n'y a pas de matières",
            "Tout est basé sur l'informatique"
        ],
        "answer": "On travaille par 'périodes' d'une même matière pendant 3 à 4 semaines, avec le même professeur sur plusieurs années",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Steiner vise une approche holistique (corps/esprit), rythmant l'apprentissage sur des cycles longs pour une imprégnation profonde, souvent avec un lien fort à l'artistique[cite: 1358, 1364].",
        "tag": "Pédagogie"
    },
    {
        "q": "En sémiologie urinaire, quelle est la différence entre 'Pollakiurie' et 'Polyurie' ?",
        "type": "ouverte",
        "answer": "Polyurie = Augmentation du VOLUME total des urines (>2L/24h). Pollakiurie = Augmentation de la FRÉQUENCE des mictions, mais avec de petits volumes (volume total normal).",
        "level": "Avancé",
        "explanation": "La polyurie évoque un diabète. La pollakiurie évoque une cystite (irritation) ou un problème de prostate (obstacle)[cite: 1134, 1150].",
        "tag": "Sémiologie"
    },
    {
        "q": "En sémiologie, qu'est-ce qu'une 'Hématémèse' ?",
        "options": [
            "Un vomissement de sang d'origine digestive",
            "Un crachat de sang lors d'une toux (origine pulmonaire)",
            "Du sang dans les urines",
            "Un saignement de nez"
        ],
        "answer": "Un vomissement de sang d'origine digestive",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le rejet de sang par la bouche au cours d'un effort de vomissement[cite: 1040]. À ne pas confondre avec l'hémoptysie (sang rejeté par la toux, origine respiratoire)[cite: 1121].",
        "tag": "Sémiologie Digestive"
    },
    {
        "q": "Quelle technique d'imagerie médicale utilise des ultrasons et ne présente aucune irradiation ?",
        "options": ["Le Scanner (TDM)", "La Radiographie standard", "L'Échographie", "La Scintigraphie"],
        "answer": "L'Échographie",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Mise au point vers 1955, elle utilise la réflexion des ultrasons[cite: 1230]. C'est l'examen de choix pour la grossesse car totalement inoffensif (pas de rayons X).",
        "tag": "Imagerie"
    },
    {
        "q": "Que signifie le terme 'Epistaxis' ?",
        "options": ["Un saignement de nez", "Un écoulement de pus par l'oreille", "Une difficulté à avaler", "Une paralysie du visage"],
        "answer": "Un saignement de nez",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le terme médical pour un saignement de nez[cite: 1005]. L'otorragie est le saignement par l'oreille[cite: 1009].",
        "tag": "Sémiologie ORL"
    },
    {
        "q": "Quelle est la contre-indication absolue à l'IRM (Imagerie par Résonance Magnétique) ?",
        "options": [
            "Être enceinte",
            "Avoir de la fièvre",
            "Porter un objet ferromagnétique (pacemaker, éclat métallique dans l'œil, certaines prothèses)",
            "Être claustrophobe (c'est juste une gêne, pas une interdiction vitale)"
        ],
        "answer": "Porter un objet ferromagnétique (pacemaker, éclat métallique dans l'œil, certaines prothèses)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'IRM est un aimant géant. Tout métal ferreux est attiré violemment ou s'échauffe, ce qui peut être mortel (déplacement du pacemaker, brûlure interne)[cite: 1269].",
        "tag": "Sécurité Imagerie"
    },
    {
        "q": "Définissez la 'Tachycardie'.",
        "options": [
            "Une fréquence cardiaque inférieure à 50 bpm",
            "Une fréquence cardiaque irrégulière",
            "Une fréquence cardiaque supérieure à 90-100 bpm au repos",
            "L'arrêt du cœur"
        ],
        "answer": "Une fréquence cardiaque supérieure à 90-100 bpm au repos",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'accélération du rythme cardiaque[cite: 1096]. À l'inverse, la bradycardie est un rythme lent (<50 bpm)[cite: 1099].",
        "tag": "Sémiologie Cardio"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la différence clinique entre 'Vomissement' et 'Régurgitation' ?",
        "type": "ouverte",
        "answer": "Le vomissement est un rejet actif avec effort de contraction (muscles abdominaux/diaphragme). La régurgitation est un rejet passif, sans effort, souvent lié à un reflux ou un obstacle œsophagien.",
        "level": "Intermédiaire",
        "explanation": "La régurgitation est fréquente chez le nourrisson (immaturité du cardia) ou en cas de méga-œsophage chez l'adulte[cite: 1033, 1041].",
        "tag": "Sémiologie Digestive"
    },
    {
        "q": "Qu'est-ce que le 'Méléna' et que signifie-t-il ?",
        "options": [
            "Du sang rouge dans les selles (origine basse)",
            "Des selles noires, goudronneuses et nauséabondes, signifiant une hémorragie digestive haute (sang digéré)",
            "Des selles grasses (malabsorption)",
            "L'absence de selles"
        ],
        "answer": "Des selles noires, goudronneuses et nauséabondes, signifiant une hémorragie digestive haute (sang digéré)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "La couleur noire vient de la digestion de l'hémoglobine par les sucs gastriques. Cela indique que le saignement vient de l'estomac ou de l'œsophage, pas du rectum [cite: 1083-1084].",
        "tag": "Sémiologie Digestive"
    },
    {
        "q": "En sémiologie urinaire, qu'est-ce qu'une 'Dysurie' ?",
        "options": [
            "Une douleur à la miction (brûlure)",
            "Une difficulté à uriner avec un jet faible, nécessitant de pousser",
            "Le fait d'uriner très souvent",
            "La présence de sang dans les urines"
        ],
        "answer": "Une difficulté à uriner avec un jet faible, nécessitant de pousser",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Attention au piège fréquent ! La brûlure mictionnelle (souvent appelée à tort dysurie dans le langage courant) n'est pas la définition médicale stricte. La dysurie est un trouble du débit (jet faible) lié à un obstacle (ex: prostate) [cite: 1153-1155].",
        "tag": "Sémiologie Urinaire"
    },
    {
        "q": "Quelle est la différence de principe physique entre la Radiographie (ou Scanner) et l'IRM ?",
        "type": "ouverte",
        "answer": "La radio et le scanner utilisent les Rayons X (absorption différentielle par les tissus, irradiant). L'IRM utilise un champ magnétique et des ondes radio (résonance des protons, non irradiant).",
        "level": "Intermédiaire",
        "explanation": "Le scanner voit bien l'os et le poumon[cite: 1229, 1251]. L'IRM est supérieure pour les tissus mous (cerveau, muscles, tendons)[cite: 1267].",
        "tag": "Imagerie"
    },
    {
        "q": "Que désigne le terme 'Pyrosis' ?",
        "options": [
            "Une fièvre élevée",
            "Une sensation de brûlure rétro-sternale ascendante",
            "Une infection de la peau",
            "Une envie impérieuse d'uriner"
        ],
        "answer": "Une sensation de brûlure rétro-sternale ascendante",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est le signe typique du Reflux Gastro-Œsophagien (RGO). La brûlure part de l'épigastre et remonte derrière le sternum[cite: 1058].",
        "tag": "Sémiologie Digestive"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le mécanisme et les signes cliniques du 'Collapsus' (état de choc).",
        "type": "ouverte",
        "answer": "C'est un désamorçage de la pompe cardiaque ou une chute brutale de tension (<60 mmHg). Signes : Pâleur, Froideur des extrémités, Marbrures, Tachycardie (pour compenser), et Anurie.",
        "level": "Avancé",
        "explanation": "Le corps sacrifie la périphérie (peau, reins) par vasoconstriction pour maintenir le sang vers les organes vitaux (cerveau, cœur). C'est une urgence vitale [cite: 1107-1112].",
        "tag": "Urgence Vitale"
    },
    {
        "q": "En sémiologie, qu'est-ce qu'une 'Stéatorrhée' ?",
        "options": [
            "La présence de sang dans les selles",
            "La présence anormale de graisses dans les selles (selles brillantes, flottantes, collantes)",
            "La présence de protéines dans les selles (Créatorrhée)",
            "Une diarrhée aqueuse"
        ],
        "answer": "La présence anormale de graisses dans les selles (selles brillantes, flottantes, collantes)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle traduit une malabsorption des graisses (ex: insuffisance pancréatique). Les selles collent à la cuvette ou font des 'yeux' d'huile [cite: 1079-1080].",
        "tag": "Sémiologie Digestive"
    },
    {
        "q": "Qu'est-ce qu'une 'Dyschésie' ?",
        "type": "ouverte",
        "answer": "C'est une 'fausse constipation' terminale. Les selles arrivent bien dans l'ampoule rectale (transit normal) mais le réflexe de défécation ne se déclenche pas (perte de sensibilité rectale).",
        "level": "Avancé",
        "explanation": "Fréquente chez la personne âgée, elle peut conduire à l'incontinence par regorgement ou à la formation de fécalomes, car le patient ne 'sent' pas qu'il doit aller à la selle [cite: 1085-1088].",
        "tag": "Sémiologie Digestive"
    },
    {
        "q": "Quelle est la particularité de la 'Médecine Nucléaire' (Scintigraphie, TEP-Scan) par rapport aux autres imageries ?",
        "options": [
            "Elle est en noir et blanc",
            "C'est une imagerie fonctionnelle/métabolique : on injecte un traceur radioactif qui se fixe sur les cellules actives, permettant de voir le fonctionnement de l'organe et non juste son anatomie",
            "Elle utilise des aimants",
            "Elle ne nécessite aucune injection"
        ],
        "answer": "C'est une imagerie fonctionnelle/métabolique : on injecte un traceur radioactif qui se fixe sur les cellules actives, permettant de voir le fonctionnement de l'organe et non juste son anatomie",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La radio montre l'os cassé (structure). La scintigraphie montre l'os qui se 'répare' ou une métastase active (fonction/métabolisme) [cite: 1271-1275].",
        "tag": "Imagerie"
    },
    {
        "q": "Qu'est-ce qu'un 'Globe Vésical' et comment le reconnaît-on cliniquement ?",
        "type": "ouverte",
        "answer": "C'est une rétention aiguë d'urine (la vessie est pleine mais ne peut se vider à cause d'un obstacle). On observe une douleur hypogastrique intense et une masse arrondie (convexité) palpable et mate à la percussion au-dessus du pubis.",
        "level": "Avancé",
        "explanation": "C'est une urgence urologique douloureuse nécessitant un sondage évacuateur. Attention : à distinguer de l'anurie (vessie vide car reins ne produisent rien) [cite: 1156-1157].",
        "tag": "Sémiologie Urinaire"
    },
    {
        "q": "En sociologie, quelle distinction fait-on entre 'Schéma Corporel' et 'Image du Corps' ?",
        "options": [
            "C'est la même chose",
            "Le Schéma Corporel est une réalité physiologique/neuro-motrice (repérage dans l'espace), l'Image du Corps est une représentation psycho-affective subjective (liée à l'histoire et aux émotions)",
            "Le Schéma Corporel change tout le temps, l'Image du Corps est fixe",
            "L'Image du Corps est innée"
        ],
        "answer": "Le Schéma Corporel est une réalité physiologique/neuro-motrice (repérage dans l'espace), l'Image du Corps est une représentation psycho-affective subjective (liée à l'histoire et aux émotions)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cette distinction est fondamentale en psychomotricité. On peut avoir un schéma corporel intact (je sais bouger) mais une image du corps défaillante (je me sens morcelé ou gros alors que je suis maigre) [cite: 791-792].",
        "tag": "Psychomotricité"
    },
    {
        "q": "Qu'est-ce qu'une 'Rhinorrhée' ?",
        "options": [
            "Un saignement de nez",
            "Un écoulement liquidien nasal (nez qui coule), séreux ou purulent",
            "Une obstruction nasale",
            "Une perte de l'odorat"
        ],
        "answer": "Un écoulement liquidien nasal (nez qui coule), séreux ou purulent",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle peut être antérieure (par les narines) ou postérieure (dans la gorge). Si c'est de l'eau claire = séreux (allergie/viral). Si c'est épais/jaune = purulent (surinfection) [cite: 1000-1004].",
        "tag": "Sémiologie ORL"
    },
    {
        "q": "Qu'est-ce que l'Ostéodensitométrie (DEXA) ?",
        "options": [
            "Un scanner du cerveau",
            "Une technique utilisant les rayons X pour mesurer spécifiquement la densité minérale osseuse",
            "Une prise de sang pour le calcium",
            "Une radio des dents"
        ],
        "answer": "Une technique utilisant les rayons X pour mesurer spécifiquement la densité minérale osseuse",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'examen de référence pour diagnostiquer l'ostéoporose et évaluer le risque de fracture[cite: 1256].",
        "tag": "Imagerie"
    },
    {
        "q": "Dans le cadre de l'examen clinique, pourquoi faut-il tester les fonctions de déglutition chez une personne âgée ou neurologique ?",
        "type": "ouverte",
        "answer": "Pour prévenir le risque de 'fausse route' (pneumopathie d'inhalation). Il faut tester avec une gorgée d'eau pour vérifier que le patient avale correctement sans tousser.",
        "level": "Avancé",
        "explanation": "Le cours précise ironiquement : 'Il vaut mieux tester avec une gorgée d'eau qu'avec le repas du soir !' [cite: 1202-1204].",
        "tag": "Sémiologie Pratique"
    },
    {
        "q": "Que permet d'observer une 'Fibroscopie' (Endoscopie) ?",
        "type": "ouverte",
        "answer": "Elle permet de visualiser l'intérieur des cavités ou conduits de l'organisme (estomac, bronches, colon) grâce à un tube souple muni d'une caméra et de faire des prélèvements (biopsies).",
        "level": "Avancé",
        "explanation": "C'est un examen invasif, contrairement à l'imagerie externe. Ex: Gastroscopie (estomac), Coloscopie (colon), Bronchoscopie (poumons)[cite: 1299, 1301].",
        "tag": "Imagerie Interventionnelle"
    },
    {
        "q": "Quel est le mécanisme d'action principal des Benzodiazépines (BZD) ?",
        "options": [
            "Elles stimulent le système nerveux (excitants)",
            "Elles sont uniquement placebo",
            "Elles potentialisent l'action inhibitrice du GABA (effet calmant, anxiolytique, sédatif)",
            "Elles bloquent la dopamine"
        ],
        "answer": "Elles potentialisent l'action inhibitrice du GABA (effet calmant, anxiolytique, sédatif)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le GABA est le principal neurotransmetteur inhibiteur du cerveau ('le frein'). Les BZD appuient sur ce frein. Effets : anxiolytique, sédatif, myorelaxant, anticonvulsivant [cite: 214-215].",
        "tag": "Pharmacologie Psychotrope"
    },
    {
        "q": "En évaluation de la douleur, qu'est-ce que l'EVA ?",
        "options": [
            "Évaluation Verbale Autonome",
            "Échelle Visuelle Analogique (la réglette)",
            "Échelle de Vie Active",
            "Examen Visuel Approfondi"
        ],
        "answer": "Échelle Visuelle Analogique (la réglette)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'outil de référence pour l'auto-évaluation. Le patient déplace un curseur entre 'Pas de douleur' et 'Douleur maximale imaginable'[cite: 292, 305].",
        "tag": "Douleur"
    },
    {
        "q": "Quelle est la définition clinique d'une épilepsie ?",
        "options": [
            "Une crise de nerfs",
            "Une affection neurologique chronique caractérisée par la répétition de crises dues à des décharges électriques neuronales excessives",
            "Une maladie musculaire",
            "Une simple perte de connaissance"
        ],
        "answer": "Une affection neurologique chronique caractérisée par la répétition de crises dues à des décharges électriques neuronales excessives",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un 'orage électrique' dans le cerveau. Elle peut être partielle (focale) ou généralisée[cite: 120].",
        "tag": "Neurologie"
    },
    {
        "q": "En histoire de l'éducation, qu'a créé Pauline Kergomard en 1881 ?",
        "options": ["Le lycée", "L'école maternelle", "L'université", "L'école des loisirs"],
        "answer": "L'école maternelle",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elle a transformé les 'salles d'asile' (garderies) en véritables écoles maternelles éducatives, respectueuses du développement de l'enfant[cite: 1380].",
        "tag": "Histoire Éducation"
    },
    {
        "q": "Qu'est-ce qu'un médicament 'Psycholeptique' ?",
        "options": ["Un stimulant (ex: amphétamines)", "Un calmant qui diminue l'activité mentale (ex: anxiolytiques, hypnotiques, neuroleptiques)", "Un hallucinogène", "Un antidépresseur"],
        "answer": "Un calmant qui diminue l'activité mentale (ex: anxiolytiques, hypnotiques, neuroleptiques)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Classification de Delay et Deniker : Psycholeptiques (calmants), Psychoanaleptiques (stimulants), Psychodysleptiques (perturbateurs)[cite: 219].",
        "tag": "Pharmacologie Psychotrope"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la différence entre une douleur nociceptive et une douleur neuropathique ?",
        "type": "ouverte",
        "answer": "Nociceptive : signal d'alarme normal suite à une lésion tissulaire (coupure, brûlure), système nerveux intact. Neuropathique : lésion du système nerveux lui-même (nerf coupé, zona), douleur anormale (décharges, fourmillements).",
        "level": "Intermédiaire",
        "explanation": "Les antalgiques classiques (paracétamol) marchent bien sur le nociceptif, mais très mal sur le neuropathique (qui nécessite des antiépileptiques ou antidépresseurs) [cite: 245-251].",
        "tag": "Douleur"
    },
    {
        "q": "Quels sont les effets secondaires majeurs des Benzodiazépines à surveiller chez le patient ?",
        "type": "ouverte",
        "answer": "Somnolence diurne, troubles de la mémoire (amnésie antérograde), risque de chute (myorelaxation), et risque de dépendance/accoutumance.",
        "level": "Intermédiaire",
        "explanation": "C'est pourquoi la durée de prescription est limitée légalement (ex: 12 semaines pour l'anxiété)[cite: 227, 233].",
        "tag": "Iatrogénie"
    },
    {
        "q": "Qu'est-ce qu'une crise d'épilepsie 'Absence' (Petit Mal) ?",
        "options": [
            "Une crise convulsive violente",
            "Une suspension brève de la conscience (quelques secondes), l'enfant s'arrête, regard fixe, puis reprend son activité",
            "Une paralysie du bras",
            "Une crise de colère"
        ],
        "answer": "Une suspension brève de la conscience (quelques secondes), l'enfant s'arrête, regard fixe, puis reprend son activité",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Typique de l'enfant. Souvent confondu avec de la rêverie à l'école. Il n'y a pas de chute ni de convulsions [cite: 126, 173-176].",
        "tag": "Neurologie"
    },
    {
        "q": "En sociologie, comment Émile Durkheim définit-il les 'faits sociaux' ?",
        "type": "ouverte",
        "answer": "Ce sont des manières d'agir, de penser et de sentir, extérieures à l'individu et qui s'imposent à lui par la coercition (pression sociale).",
        "level": "Intermédiaire",
        "explanation": "Exemple : la mode, la politesse, les rituels. On croit choisir, mais la société nous dicte inconsciemment ces comportements[cite: 777].",
        "tag": "Sociologie"
    },
    {
        "q": "Quelle loi de 2005 a marqué un tournant pour l'inclusion scolaire des enfants handicapés ?",
        "options": ["La loi Hôpital Patient Santé Territoire", "La loi pour l'égalité des droits et des chances, la participation et la citoyenneté des personnes handicapées", "La loi Leonetti", "La loi Kouchner"],
        "answer": "La loi pour l'égalité des droits et des chances, la participation et la citoyenneté des personnes handicapées",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Elle pose le principe de scolarisation en milieu ordinaire comme priorité et crée les MDPH[cite: 1380].",
        "tag": "Législation Handicap"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Décrivez la séquence typique d'une crise d'épilepsie généralisée Tonico-Clonique (Grand Mal).",
        "type": "ouverte",
        "answer": "1. Phase Tonique (raideur, chute, cri, apnée). 2. Phase Clonique (secousses musculaires rythmées). 3. Phase Résolutive (coma stertoreux, relâchement sphincters) avec confusion au réveil.",
        "level": "Avancé",
        "explanation": "C'est la forme la plus impressionnante. Le danger immédiat est la chute et l'obstruction des voies aériennes, pas la crise elle-même (le cerveau 'disjoncte' pour se protéger) [cite: 183-186].",
        "tag": "Neurologie"
    },
    {
        "q": "Pourquoi les traitements de la douleur neuropathique incluent-ils des antiépileptiques ou des antidépresseurs ?",
        "options": [
            "Car le patient est souvent dépressif à cause de la douleur",
            "Car ces médicaments agissent sur l'excitabilité des neurones et les voies de modulation de la douleur, indépendamment de leur effet sur l'humeur",
            "C'est une erreur de prescription",
            "Pour faire dormir le patient"
        ],
        "answer": "Car ces médicaments agissent sur l'excitabilité des neurones et les voies de modulation de la douleur, indépendamment de leur effet sur l'humeur",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La douleur neuropathique est une 'épilepsie du nerf'. Les antiépileptiques (Lyrica, Neurontin) calment cette hyperexcitabilité électrique[cite: 263].",
        "tag": "Pharmacologie Douleur"
    },
    {
        "q": "En histoire de l'éducation, qu'est-ce que la 'Loi Falloux' (1850) ?",
        "options": [
            "Elle interdit l'école aux filles",
            "Elle proclame la liberté d'enseignement, permettant à l'Église (congrégations religieuses) de prendre une place très influente dans l'éducation secondaire",
            "Elle crée les lycées publics",
            "Elle rend l'école obligatoire"
        ],
        "answer": "Elle proclame la liberté d'enseignement, permettant à l'Église (congrégations religieuses) de prendre une place très influente dans l'éducation secondaire",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'était une réaction conservatrice. Les lois Ferry viendront plus tard (1881) pour laïciser l'école publique en réaction à cette influence[cite: 1380].",
        "tag": "Histoire Éducation"
    },
    {
        "q": "Qu'est-ce que l'effet 'Antabuse' parfois recherché ou redouté en pharmacologie ?",
        "type": "ouverte",
        "answer": "C'est une réaction violente (chaleur, vomissements, malaise) lors de la prise d'alcool concomitante à certains médicaments qui bloquent la dégradation de l'alcool.",
        "level": "Avancé",
        "explanation": "Utilisé jadis pour le sevrage alcoolique (le patient est malade s'il boit). C'est aussi un effet indésirable de certains antibiotiques (métronidazole).",
        "tag": "Pharmacologie"
    },
    {
        "q": "Dans la prise en charge de la Douleur Chronique (> 3 mois), quel est le changement de paradigme thérapeutique ?",
        "type": "ouverte",
        "answer": "On passe d'une visée curative (supprimer la cause) à une visée ré-adaptative (vivre avec, réduire l'impact). L'approche devient pluridisciplinaire (biopsycho-sociale) et non plus seulement médicamenteuse.",
        "level": "Avancé",
        "explanation": "La douleur chronique devient une maladie en soi ('Douleur maladie'). Le traitement purement pharmacologique est souvent échec. Il faut traiter la dépression associée et rééduquer [cite: 281-287].",
        "tag": "Douleur"
    },
    {
        "q": "Quelle est la définition de la 'Santé' selon l'OMS (1946) ?",
        "options": [
            "L'absence de maladie ou d'infirmité",
            "Un état de complet bien-être physique, mental et social, et ne consiste pas seulement en une absence de maladie",
            "La capacité à travailler",
            "Avoir de bonnes analyses de sang"
        ],
        "answer": "Un état de complet bien-être physique, mental et social, et ne consiste pas seulement en une absence de maladie",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une définition idéaliste mais qui a révolutionné la médecine en incluant le psychique et le social, fondant ainsi la psychomotricité [cite: 863-865].",
        "tag": "Santé Publique"
    },
    {
        "q": "En sociologie, qu'est-ce que le 'Stigmate' selon Erving Goffman ?",
        "type": "ouverte",
        "answer": "C'est un attribut qui discrédite l'individu et le réduit, aux yeux des autres, d'une personne entière à une personne 'gâtée' ou disqualifiée (ex: handicap visible, maladie mentale).",
        "level": "Avancé",
        "explanation": "Le stigmate perturbe les interactions sociales. La personne stigmatisée doit sans cesse gérer son 'identité abîmée' (cacher le stigmate ou le revendiquer).",
        "tag": "Sociologie"
    },
    {
        "q": "Quel est le risque majeur d'un arrêt brutal des Benzodiazépines ?",
        "options": [
            "Une simple insomnie",
            "Un syndrome de sevrage sévère pouvant aller jusqu'à des crises convulsives (effet rebond)",
            "Une prise de poids",
            "Aucun risque"
        ],
        "answer": "Un syndrome de sevrage sévère pouvant aller jusqu'à des crises convulsives (effet rebond)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le cerveau, habitué au 'frein' chimique, s'emballe si on l'enlève d'un coup. La décroissance doit toujours être progressive[cite: 227].",
        "tag": "Sécurité Pharmaco"
    },
    {
        "q": "Quelle est la différence entre une 'Maladie' (Disease) et la 'Maladie du malade' (Illness) en sociologie de la santé ?",
        "type": "ouverte",
        "answer": "'Disease' est la pathologie biologique vue par le médecin (lésion). 'Illness' est l'expérience subjective du malade (comment il se sent, son vécu, ses croyances).",
        "level": "Avancé",
        "explanation": "Le soignant doit traiter la Disease tout en prenant soin de l'Illness. Parfois il y a Illness sans Disease (douleur sine materia) ou Disease sans Illness (HTA silencieuse).",
        "tag": "Sociologie"
    },
    {
        "q": "En pédagogie, qu'est-ce que la 'Zone Prochaine de Développement' (Vygotski) ?",
        "options": [
            "La salle de classe",
            "Ce que l'enfant sait faire seul",
            "L'écart entre ce que l'enfant sait faire seul et ce qu'il peut faire avec de l'aide (étayage). C'est là que se joue l'apprentissage.",
            "Ce que l'enfant ne saura jamais faire"
        ],
        "answer": "L'écart entre ce que l'enfant sait faire seul et ce qu'il peut faire avec de l'aide (étayage). C'est là que se joue l'apprentissage.",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le bon pédagogue n'enseigne pas ce qui est déjà acquis, ni ce qui est impossible, mais ce qui est 'juste après' (le challenge réalisable avec aide).",
        "tag": "Pédagogie"
    },
    ],

    "MODULE 2: Anatomie & Neuroanatomie": [
     {
        "q": "Quelles sont les limites anatomiques du Thorax (cage thoracique) ?",
        "options": [
            "En haut la clavicule, en bas le bassin",
            "En avant le sternum, latéralement les côtes, en arrière la colonne vertébrale, en haut la 1ère côte, en bas le diaphragme",
            "Uniquement les côtes et le sternum",
            "C'est la cavité abdominale"
        ],
        "answer": "En avant le sternum, latéralement les côtes, en arrière la colonne vertébrale, en haut la 1ère côte, en bas le diaphragme",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le thorax est une 'cage' protectrice pour le cœur et les poumons. Le diaphragme en est le plancher, séparant le thorax de l'abdomen.",
        "tag": "Anatomie - Thorax"
    },
    {
        "q": "Combien de vertèbres cervicales compte la colonne vertébrale ?",
        "options": ["5", "7", "12", "Cela dépend des gens"],
        "answer": "7",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il y a 7 cervicales (C1 à C7). C'est une constante chez les mammifères (même la girafe !).",
        "tag": "Anatomie - Rachis"
    },
    {
        "q": "Quelle pathologie se caractérise par une douleur au niveau de la tubérosité tibiale antérieure chez l'adolescent sportif ?",
        "options": ["La maladie d'Osgood-Schlatter", "L'entorse de cheville", "La fracture du fémur", "La tendinite du coude"],
        "answer": "La maladie d'Osgood-Schlatter",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une apophysite de croissance (arrachement osseux) due à la sursollicitation du tendon patellaire (rotulien) sur le tibia.",
        "tag": "Pathologie - Pédiatrie"
    },
    {
        "q": "Quel est le muscle principal de la respiration qui ferme le thorax en bas ?",
        "options": ["Le grand droit", "Le Psoas", "Le Diaphragme", "Les Intercostaux"],
        "answer": "Le Diaphragme",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il agit comme un piston. Lorsqu'il se contracte (s'abaisse), il crée une dépression qui fait entrer l'air dans les poumons.",
        "tag": "Anatomie - Myologie"
    },
    {
        "q": "Combien de vertèbres thoraciques (dorsales) possédons-nous ?",
        "options": ["7", "5", "12", "24"],
        "answer": "12",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elles sont numérotées de T1 à T12 (ou D1 à D12). Chacune est articulée avec une paire de côtes.",
        "tag": "Anatomie - Rachis"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Décrivez la courbure physiologique du rachis cervical dans le plan sagittal.",
        "type": "ouverte",
        "answer": "C'est une Lordose cervicale, c'est-à-dire une courbure concave vers l'arrière (creux).",
        "level": "Intermédiaire",
        "explanation": "La colonne alterne : Lordose cervicale, Cyphose thoracique (bosse), Lordose lombaire, Cyphose sacrée. Cela permet d'amortir les chocs.",
        "tag": "Anatomie - Rachis"
    },
    {
        "q": "Qu'est-ce que la Maladie de Legg-Calvé-Perthes ?",
        "type": "ouverte",
        "answer": "C'est une ostéochondrite primitive de la hanche chez l'enfant (nécrose avasculaire de la tête fémorale due à un apport sanguin limité).",
        "level": "Intermédiaire",
        "explanation": "Elle évolue en 4 phases : Nécrose, Fragmentation, Ré-ossification, Remodelage. Elle peut laisser des séquelles comme une raideur ou une arthrose précoce.",
        "tag": "Pathologie - Pédiatrie"
    },
    {
        "q": "Comment sont orientées les côtes au niveau thoracique ?",
        "options": [
            "Elles sont horizontales",
            "Elles partent latéralement, surtout en avant et vers le bas (inclinées)",
            "Elles partent vers le haut",
            "Elles sont verticales"
        ],
        "answer": "Elles partent latéralement, surtout en avant et vers le bas (inclinées)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Cette obliquité est importante pour la mécanique respiratoire (mouvement en anse de seau).",
        "tag": "Anatomie - Thorax"
    },
    {
        "q": "Quelle est la cause principale de la nécrose avasculaire de la tête fémorale chez l'adulte (hors traumatisme) ?",
        "options": ["Le sport intensif", "L'éthylisme chronique (alcoolisme) ou les corticoïdes", "La marche à pied", "Le manque de calcium"],
        "answer": "L'éthylisme chronique (alcoolisme) ou les corticoïdes",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un processus idiopathique souvent lié à ces facteurs de risque, entraînant la mort du tissu osseux par manque de sang.",
        "tag": "Pathologie - Hanche"
    },
    {
        "q": "Quelle est la différence entre les 'vraies côtes', les 'fausses côtes' et les 'côtes flottantes' ?",
        "type": "ouverte",
        "answer": "Vraies (1-7) : attachées directement au sternum. Fausses (8-10) : attachées au cartilage de la côte du dessus. Flottantes (11-12) : libres en avant, sans attache sternale.",
        "level": "Intermédiaire",
        "explanation": "Cette architecture assure à la fois la protection (haut) et la mobilité respiratoire (bas).",
        "tag": "Anatomie - Thorax"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Dans la classification de Weber pour les fractures de la cheville (malléole externe/fibula), que signifie le type B ?",
        "options": [
            "Fracture sous-ligamentaire (pointe de la malléole)",
            "Fracture trans-ligamentaire (au niveau de la syndesmose tibio-fibulaire)",
            "Fracture sus-ligamentaire (au-dessus de la syndesmose)",
            "Fracture ouverte"
        ],
        "answer": "Fracture trans-ligamentaire (au niveau de la syndesmose tibio-fibulaire)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Weber A = Sous-ligamentaire (cheville stable). Weber B = Trans-ligamentaire. Weber C = Sus-ligamentaire (atteinte de la syndesmose, souvent instable chirurgicale).",
        "tag": "Traumatologie"
    },
    {
        "q": "Quelles sont les artères nourricières principales de la tête fémorale dont l'atteinte provoque une nécrose ?",
        "options": [
            "L'artère aorte",
            "Les artères circonflexes (latérale et médiale) et la branche de l'artère obturatrice",
            "L'artère radiale",
            "L'artère carotide"
        ],
        "answer": "Les artères circonflexes (latérale et médiale) et la branche de l'artère obturatrice",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Ces artères forment un anneau autour du col du fémur. En cas de fracture du col, elles sont souvent sectionnées, condamnant la tête à la nécrose (d'où la pose de prothèse).",
        "tag": "Anatomie - Vasculaire"
    },
    {
        "q": "Expliquez le mécanisme physiopathologique de l'Arthrite Rhumatoïde (Polyarthrite).",
        "type": "ouverte",
        "answer": "C'est une maladie auto-immune (terrain génétique HLA-DR4/DR1) caractérisée par une inflammation de la synoviale (pannus) qui détruit le cartilage et l'os. Elle touche 15-28% des hanches.",
        "level": "Avancé",
        "explanation": "Contrairement à l'arthrose (usure mécanique), c'est le système immunitaire qui attaque l'articulation. Elle touche souvent les femmes entre 40 et 60 ans.",
        "tag": "Rhumatologie"
    },
    {
        "q": "Qu'est-ce qu'une fracture du 'Pilon Tibial' et pourquoi est-elle grave ?",
        "options": [
            "Une fracture de l'orteil",
            "Une fracture de l'extrémité distale du tibia (plafond de la cheville), souvent intra-articulaire par compression axiale",
            "Une fracture du genou",
            "Une fracture de fatigue"
        ],
        "answer": "Une fracture de l'extrémité distale du tibia (plafond de la cheville), souvent intra-articulaire par compression axiale",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le pilon tibial supporte tout le poids du corps. Une fracture à ce niveau détruit la surface de glissement, entraînant presque systématiquement une arthrose post-traumatique invalidante.",
        "tag": "Traumatologie"
    },
    {
        "q": "Quelle est la définition exacte de l'Arthrose selon votre cours ?",
        "type": "ouverte",
        "answer": "C'est une dégénérescence du cartilage articulaire (usure) sans infection ni inflammation primaire spécifique (bien qu'une inflammation secondaire puisse survenir).",
        "level": "Avancé",
        "explanation": "Elle se manifeste par des douleurs mécaniques (à l'effort), une raideur et une déformation osseuse (ostéophytes).",
        "tag": "Rhumatologie"
    },
    {
        "q": "Concernant la maladie d'Osgood-Schlatter, quel est le traitement de référence ?",
        "options": [
            "Chirurgie immédiate",
            "Antibiotiques",
            "Mise au repos sportif (arrêt des tractions sur le tendon)",
            "Plâtre complet jambe-cuisse pendant 6 mois"
        ],
        "answer": "Mise au repos sportif (arrêt des tractions sur le tendon)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Comme c'est une pathologie de sursollicitation mécanique liée à la croissance, le repos suffit généralement à la guérison (consolidation de la tubérosité).",
        "tag": "Pathologie - Pédiatrie"
    },
    {
        "q": "Quels sont les antigènes génétiques fréquemment associés à la Polyarthrite Rhumatoïde ?",
        "options": ["HLA-B27", "HLA-DR4 (60%) et HLA-DR1 (30%)", "Groupe sanguin O", "Trisomie 21"],
        "answer": "HLA-DR4 (60%) et HLA-DR1 (30%)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La présence de ces marqueurs génétiques signe le terrain auto-immun favorisant la maladie.",
        "tag": "Génétique / Rhumato"
    },
    {
        "q": "Quel rôle joue la colonne vertébrale (rachis) dans la biomécanique du tronc ?",
        "type": "ouverte",
        "answer": "Elle est un système passif qui tient les articulations, constituée de vertèbres et de ligaments qui la soutiennent. Elle protège la moelle épinière et soutient la cage thoracique.",
        "level": "Avancé",
        "explanation": "C'est le mât central du corps, conciliant rigidité (protection) et souplesse (mouvement) grâce à ses courbures.",
        "tag": "Anatomie - Rachis"
    },
    {
        "q": "Dans les fractures du pilon tibial, quelles sont les 3 catégories de la classification mentionnée ?",
        "options": [
            "Verte, Jaune, Rouge",
            "Intra-articulaire, Articulaire partielle, et Articulaire complète",
            "Weber A, B, C",
            "Ouverte, Fermée, Comminutive"
        ],
        "answer": "Intra-articulaire, Articulaire partielle, et Articulaire complète",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cette classification évalue la gravité de l'atteinte de la surface articulaire, conditionnant le pronostic fonctionnel.",
        "tag": "Traumatologie"
    },
    {
        "q": "Pourquoi la 1ère côte est-elle un repère anatomique important ?",
        "type": "ouverte",
        "answer": "Elle délimite l'ouverture supérieure du thorax (le haut de la cage thoracique).",
        "level": "Avancé",
        "explanation": "Tout ce qui passe du cou au thorax (trachée, œsophage, gros vaisseaux) traverse cet orifice délimité par la 1ère côte.",
        "tag": "Anatomie - Thorax"
    },
    {
        "q": "Quel est le principal muscle fléchisseur de la hanche (qui permet de lever la cuisse) ?",
        "options": ["Le Grand Fessier", "Le Psoas-Iloaque", "Le Quadriceps", "Les Ischio-jambiers"],
        "answer": "Le Psoas-Iloaque",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un muscle profond puissant qui relie la colonne lombaire et le bassin au fémur. C'est le marcheur principal.",
        "tag": "Myologie - Membre Inf"
    },
    {
        "q": "Dans la classification des articulations, qu'est-ce qu'une 'Diarthrose' ?",
        "options": [
            "Une articulation immobile (sutures du crâne)",
            "Une articulation semi-mobile (disques vertébraux)",
            "Une articulation très mobile avec une cavité synoviale (ex: genou, épaule)",
            "Une fracture articulaire"
        ],
        "answer": "Une articulation très mobile avec une cavité synoviale (ex: genou, épaule)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le type d'articulation le plus répandu dans les membres. Elle possède du cartilage, une capsule, de la synoviale et des ligaments.",
        "tag": "Arthrologie"
    },
    {
        "q": "Combien de ménisques possède le genou ?",
        "options": ["1", "2 (Interne et Externe)", "4", "Aucun, c'est une rotule"],
        "answer": "2 (Interne et Externe)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Les ménisques sont des fibrocartilages en forme de croissant qui améliorent la congruence (l'emboîtement) entre le fémur (rond) et le tibia (plat).",
        "tag": "Anatomie - Genou"
    },
    {
        "q": "Quelle est la différence entre un Ligament et un Tendon ?",
        "options": [
            "C'est la même chose",
            "Le ligament relie deux os entre eux, le tendon relie un muscle à un os",
            "Le tendon relie deux os, le ligament relie un muscle à un os",
            "Le ligament est rouge, le tendon est bleu"
        ],
        "answer": "Le ligament relie deux os entre eux, le tendon relie un muscle à un os",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Moyen mnémotechnique : Ligament = Lie les os. Tendon = Tend le muscle vers l'os.",
        "tag": "Concepts de base"
    },
    {
        "q": "Concernant le pied, quel os constitue le talon ?",
        "options": ["Le Talus (Astragale)", "Le Calcanéus (Calcanéum)", "Le Cuboïde", "Le Naviculaire"],
        "answer": "Le Calcanéus (Calcanéum)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'os le plus volumineux du tarse, sur lequel s'insère le tendon d'Achille.",
        "tag": "Ostéologie - Pied"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que la 'Syndesmose' tibio-fibulaire ?",
        "type": "ouverte",
        "answer": "C'est l'articulation fibreuse distale entre le tibia et la fibula (péroné), maintenue par des ligaments puissants, assurant la stabilité de la 'mortaise' de la cheville.",
        "level": "Intermédiaire",
        "explanation": "Son atteinte (entorse haute ou fracture Weber C) est grave car elle écarte les deux os, rendant la cheville instable.",
        "tag": "Arthrologie - Cheville"
    },
    {
        "q": "Quel mouvement permet le muscle Triceps Sural (mollet) ?",
        "options": [
            "La flexion dorsale du pied (relever la pointe)",
            "La flexion plantaire du pied (se mettre sur la pointe des pieds)",
            "L'extension du genou",
            "La rotation interne de hanche"
        ],
        "answer": "La flexion plantaire du pied (se mettre sur la pointe des pieds)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est le muscle propulseur de la marche. Il s'insère via le tendon d'Achille.",
        "tag": "Myologie - Membre Inf"
    },
    {
        "q": "En anatomie, que désigne le 'Plan Sagittal' ?",
        "options": [
            "Le plan qui sépare le corps en haut et bas",
            "Le plan qui sépare le corps en avant et arrière (Frontal)",
            "Le plan qui sépare le corps en gauche et droite",
            "Le plan de la table"
        ],
        "answer": "Le plan qui sépare le corps en gauche et droite",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est dans ce plan que s'effectuent les mouvements de Flexion et d'Extension.",
        "tag": "Anatomie - Orientation"
    },
    {
        "q": "Pourquoi la fracture de la diaphyse fémorale est-elle potentiellement choquante (hypovolémique) ?",
        "type": "ouverte",
        "answer": "Car le fémur est un os très vascularisé entouré de grosses masses musculaires. Sa fracture peut entraîner une hémorragie interne de 1 à 1,5 litre de sang.",
        "level": "Intermédiaire",
        "explanation": "C'est une urgence vitale potentielle, surtout chez le sujet âgé ou le polytraumatisé.",
        "tag": "Traumatologie"
    },
    {
        "q": "Quelle est l'action des muscles Ischio-jambiers ?",
        "options": [
            "Extension de hanche et Flexion de genou",
            "Flexion de hanche et Extension de genou",
            "Adduction de la cuisse",
            "Rotation externe pure"
        ],
        "answer": "Extension de hanche et Flexion de genou",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Ils sont antagonistes du Quadriceps au niveau du genou. Ils sont situés à l'arrière de la cuisse.",
        "tag": "Myologie - Membre Inf"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Dans la classification de Weber (fractures malléolaires), qu'est-ce qui définit le Type C ?",
        "options": [
            "Une fracture sous la syndesmose",
            "Une fracture au niveau de la syndesmose",
            "Une fracture de la fibula AU-DESSUS de la syndesmose tibio-fibulaire, avec déchirure de celle-ci (instabilité)",
            "Une fracture du tibia seul"
        ],
        "answer": "Une fracture de la fibula AU-DESSUS de la syndesmose tibio-fibulaire, avec déchirure de celle-ci (instabilité)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le trait de fracture est haut situé (sus-ligamentaire). La membrane interosseuse est souvent déchirée jusqu'à la fracture. Chirurgie quasi systématique (plaque + vis).",
        "tag": "Traumatologie"
    },
    {
        "q": "Qu'est-ce que le 'Polygone de sustentation' ?",
        "type": "ouverte",
        "answer": "C'est la surface au sol délimitée par les points d'appui (les pieds). Pour qu'il y ait équilibre, la projection du centre de gravité doit tomber à l'intérieur de ce polygone.",
        "level": "Avancé",
        "explanation": "Concept clé en psychomotricité et en biomécanique. Plus le polygone est grand (pieds écartés), plus l'équilibre est stable.",
        "tag": "Biomécanique"
    },
    {
        "q": "Expliquez le rôle 'd'amortisseur hydraulique' du disque intervertébral.",
        "type": "ouverte",
        "answer": "Le disque est composé d'un noyau gélatineux (Nucleus Pulposus) entouré d'un anneau fibreux (Annulus). Le noyau répartit les pressions dans toutes les directions, transformant les contraintes verticales en forces horizontales absorbées par l'anneau.",
        "level": "Avancé",
        "explanation": "Avec l'âge, le noyau se déshydrate, perdant sa capacité d'amortissement, ce qui favorise l'arthrose et les hernies.",
        "tag": "Physiologie Articulaire"
    },
    {
        "q": "Quelle est la complication majeure tardive d'une fracture intra-articulaire du pilon tibial mal réduite ?",
        "options": [
            "L'infection",
            "L'arthrose post-traumatique tibiotalienne (cheville)",
            "La non-consolidation (pseudarthrose)",
            "L'algodystrophie"
        ],
        "answer": "L'arthrose post-traumatique tibiotalienne (cheville)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La moindre marche d'escalier (inégalité) sur la surface articulaire entraîne une usure rapide du cartilage ('effet râpe à fromage'), conduisant à une cheville douloureuse et raide.",
        "tag": "Traumatologie"
    },
    {
        "q": "Quelle est l'innervation motrice principale du Quadriceps ?",
        "options": ["Le nerf Sciatique", "Le nerf Fémoral (Crural)", "Le nerf Obturateur", "Le nerf Tibial"],
        "answer": "Le nerf Fémoral (Crural)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Une atteinte du nerf fémoral (L2-L3-L4) entraîne une impossibilité de verrouiller le genou en extension (chute à la marche) et une abolition du réflexe rotulien.",
        "tag": "Neuro-Anatomie Périphérique"
    },
    {
        "q": "Décrivez la 'Triade malheureuse' du genou (souvent au ski/football).",
        "type": "ouverte",
        "answer": "C'est l'association d'une rupture du Ligament Croisé Antérieur (LCA), du Ligament Collatéral Medial (LCM) et d'une lésion du Ménisque Interne.",
        "level": "Avancé",
        "explanation": "Elle survient sur un traumatisme en Valgus-Flexion-Rotation Externe. C'est une lésion grave de la stabilité du genou.",
        "tag": "Traumatologie"
    },
    {
        "q": "Quelle est la particularité vasculaire du 'Scaphoïde' (poignet) en cas de fracture ?",
        "options": [
            "Il saigne beaucoup",
            "Il est vascularisé à rebours (l'artère entre par le pôle distal), donc une fracture au milieu coupe le sang du pôle proximal : risque élevé de nécrose (pseudarthrose)",
            "Il ne se casse jamais",
            "Il n'a pas de vaisseaux"
        ],
        "answer": "Il est vascularisé à rebours (l'artère entre par le pôle distal), donc une fracture au milieu coupe le sang du pôle proximal : risque élevé de nécrose (pseudarthrose)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le piège classique. Une fracture du scaphoïde peut passer inaperçue à la radio initiale et nécroser ensuite.",
        "tag": "Traumatologie"
    },
    {
        "q": "Pourquoi les 'fausses côtes' (8, 9, 10) sont-elles appelées ainsi ?",
        "type": "ouverte",
        "answer": "Parce qu'elles ne s'articulent pas directement avec le sternum. Leur cartilage rejoint celui de la 7ème côte (le rebord costal).",
        "level": "Avancé",
        "explanation": "Cela crée une structure solidaire en 'auvent' qui protège le foie (à droite) et la rate (à gauche).",
        "tag": "Anatomie - Thorax"
    },
    {
        "q": "Qu'est-ce qu'une fracture 'en bois vert' ?",
        "options": [
            "Une fracture ouverte avec des débris végétaux",
            "Une fracture incomplète spécifique de l'enfant, où l'os se plie et se casse d'un côté (convexe) mais reste continu de l'autre (concave), comme une branche verte",
            "Une fracture très ancienne",
            "Une fracture de fatigue"
        ],
        "answer": "Une fracture incomplète spécifique de l'enfant, où l'os se plie et se casse d'un côté (convexe) mais reste continu de l'autre (concave), comme une branche verte",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'os de l'enfant est plus élastique (plus de collagène, périoste épais). Le traitement est orthopédique (plâtre), parfois il faut 'casser' l'autre coté pour redresser.",
        "tag": "Pédiatrie"
    },
    {
        "q": "Quel est le rôle biomécanique de la Patella (Rotule) ?",
        "type": "ouverte",
        "answer": "Elle agit comme une poulie qui déporte le tendon quadricipital vers l'avant. Cela augmente le bras de levier du quadriceps et donc sa force d'extension de 30 à 40%.",
        "level": "Avancé",
        "explanation": "Sans rotule (patellectomie), le quadriceps perdrait énormément de force. C'est un os sésamoïde inclus dans le tendon.",
        "tag": "Biomécanique"
    },
    {
        "q": "De quoi est composé anatomiquement le Système Nerveux Central (SNC) ?",
        "options": [
            "Du cerveau et du cœur",
            "De l'Encéphale (Cerveau, Cervelet, Tronc cérébral) et de la Moelle Épinière",
            "Des nerfs crâniens et des nerfs rachidiens",
            "Uniquement du cerveau"
        ],
        "answer": "De l'Encéphale (Cerveau, Cervelet, Tronc cérébral) et de la Moelle Épinière",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le SNC est la partie protégée par de l'os (crâne et colonne). Tout ce qui en sort constitue le Système Nerveux Périphérique (SNP).",
        "tag": "Neuroanat - Généralités"
    },
    {
        "q": "Quel lobe cérébral est le siège principal des fonctions exécutives (planification, jugement) et de la motricité volontaire ?",
        "options": ["Le lobe Occipital", "Le lobe Temporal", "Le lobe Frontal", "Le lobe Pariétal"],
        "answer": "Le lobe Frontal",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le 'chef d'orchestre' du cerveau, situé juste derrière le front. Il contient le cortex moteur primaire et les aires préfrontales.",
        "tag": "Neuroanat - Cerveau"
    },
    {
        "q": "Quelle est la fonction majeure du Cervelet ?",
        "options": [
            "La digestion",
            "La régulation de l'équilibre, du tonus et la coordination fine des mouvements",
            "La vision",
            "La production d'hormones"
        ],
        "answer": "La régulation de l'équilibre, du tonus et la coordination fine des mouvements",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le cervelet ne commande pas le mouvement (c'est le rôle du cortex), mais il le corrige et le fluidifie. Une lésion entraîne une démarche ébrieuse (ataxie).",
        "tag": "Neuroanat - Cervelet"
    },
    {
        "q": "Combien y a-t-il d'hémisphères cérébraux et comment communiquent-ils principalement ?",
        "options": ["2, reliés par le Corps Calleux", "4, reliés par le Tronc Cérébral", "1 seul", "2, totalement indépendants"],
        "answer": "2, reliés par le Corps Calleux",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le corps calleux est un épais faisceau de fibres (substance blanche) qui permet l'échange d'informations entre le cerveau gauche et le cerveau droit.",
        "tag": "Neuroanat - Cerveau"
    },
    {
        "q": "Où se situe la Moelle Épinière ?",
        "options": ["Dans le canal vertébral, à l'intérieur de la colonne", "Devant la colonne vertébrale", "Dans le crâne", "Le long des jambes"],
        "answer": "Dans le canal vertébral, à l'intérieur de la colonne",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elle s'étend du trou occipital jusqu'à la vertèbre L2 (ensuite, c'est la 'queue de cheval').",
        "tag": "Neuroanat - Moelle"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la différence entre Substance Grise et Substance Blanche ?",
        "type": "ouverte",
        "answer": "La Substance Grise contient les corps cellulaires des neurones (traitement de l'info). La Substance Blanche contient les axones myélinisés (transport de l'info).",
        "level": "Intermédiaire",
        "explanation": "Dans le cerveau, la substance grise est en périphérie (cortex). Dans la moelle épinière, elle est au centre (forme de papillon).",
        "tag": "Neuroanat - Histologie"
    },
    {
        "q": "Qu'est-ce que l'Homonculus de Penfield (Moteur ou Sensitif) ?",
        "type": "ouverte",
        "answer": "C'est une cartographie du corps sur le cortex cérébral où la taille de chaque partie du corps est proportionnelle à sa sensibilité ou à la précision de sa motricité, et non à sa taille réelle.",
        "level": "Intermédiaire",
        "explanation": "Ainsi, sur l'homonculus, les mains et la bouche sont énormes (très innervées), tandis que le dos est tout petit.",
        "tag": "Neuroanat - Cortex"
    },
    {
        "q": "Quel est le rôle du Thalamus ?",
        "options": [
            "Réguler la température",
            "Servir de relais et de filtre pour presque toutes les informations sensorielles avant qu'elles n'arrivent au cortex",
            "Commander les muscles",
            "Produire le liquide céphalo-rachidien"
        ],
        "answer": "Servir de relais et de filtre pour presque toutes les informations sensorielles avant qu'elles n'arrivent au cortex",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est la 'porte d'entrée' de la conscience. Il trie les infos (visuelles, tactiles, etc.) pour ne pas saturer le cortex.",
        "tag": "Neuroanat - Diencéphale"
    },
    {
        "q": "Citez les 3 parties du Tronc Cérébral (de haut en bas).",
        "type": "ouverte",
        "answer": "Mésencéphale (Pédoncules), Pont (Protubérance), Bulbe Rachidien.",
        "level": "Intermédiaire",
        "explanation": "C'est une zone vitale qui contient les centres de la respiration et du rythme cardiaque, ainsi que les noyaux des nerfs crâniens.",
        "tag": "Neuroanat - Tronc"
    },
    {
        "q": "À quoi sert le Liquide Cérébro-Spinal (LCS) ou Céphalo-Rachidien (LCR) ?",
        "options": [
            "À nourrir les os",
            "À protéger mécaniquement le SNC (amortisseur) et à éliminer les déchets métaboliques",
            "À transmettre l'influx nerveux",
            "À refroidir le cerveau"
        ],
        "answer": "À protéger mécaniquement le SNC (amortisseur) et à éliminer les déchets métaboliques",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le cerveau 'flotte' dans ce liquide, ce qui réduit son poids apparent et le protège des chocs contre la boîte crânienne.",
        "tag": "Neuroanat - Protection"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le principe de la 'Décussation' des voies pyramidales et sa conséquence clinique.",
        "type": "ouverte",
        "answer": "Les fibres motrices croisent la ligne médiane au niveau du bulbe rachidien. Conséquence : l'hémisphère droit commande la moitié gauche du corps, et inversement (Hémiplégie controlatérale).",
        "level": "Avancé",
        "explanation": "Environ 80 à 90% des fibres croisent. C'est pourquoi une lésion du cerveau gauche entraîne une paralysie à droite.",
        "tag": "Neuroanat - Voies"
    },
    {
        "q": "Qu'est-ce que le Polygone de Willis ?",
        "options": [
            "Une zone du cerveau qui gère les maths",
            "Un cercle d'anastomose artérielle à la base du cerveau reliant le système carotidien et vertébro-basilaire",
            "Un ventricule cérébral",
            "Une malformation"
        ],
        "answer": "Un cercle d'anastomose artérielle à la base du cerveau reliant le système carotidien et vertébro-basilaire",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un système de sécurité hydraulique. Si une artère se bouche, le sang peut faire le tour par les communicantes pour irriguer la zone en danger.",
        "tag": "Neuroanat - Vasculaire"
    },
    {
        "q": "Quelle est la différence fonctionnelle entre l'Aire de Broca et l'Aire de Wernicke ?",
        "type": "ouverte",
        "answer": "Broca (lobe frontal) gère la PRODUCTION du langage (parler). Wernicke (lobe temporal) gère la COMPRÉHENSION du langage.",
        "level": "Avancé",
        "explanation": "Une aphasie de Broca : le patient comprend mais ne peut pas parler. Une aphasie de Wernicke : le patient parle (jargon) mais ne comprend pas et n'a pas de sens.",
        "tag": "Neuroanat - Cortex"
    },
    {
        "q": "Quel est le rôle des Ganglions de la Base (Noyaux Gris Centraux) dans la motricité ?",
        "options": [
            "La force musculaire brute",
            "L'initiation, la facilitation et l'inhibition des mouvements volontaires (boucle de régulation)",
            "Les réflexes ostéotendineux",
            "La perception sensorielle"
        ],
        "answer": "L'initiation, la facilitation et l'inhibition des mouvements volontaires (boucle de régulation)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Leur dysfonctionnement est typique de la maladie de Parkinson (difficulté à initier le mouvement, tremblements de repos, rigidité).",
        "tag": "Neuroanat - Fonctionnel"
    },
    {
        "q": "Nommez, dans l'ordre (de l'extérieur vers l'intérieur), les trois méninges qui protègent le SNC.",
        "type": "ouverte",
        "answer": "Dure-mère (Dura mater), Arachnoïde, Pie-mère (Pia mater).",
        "level": "Avancé",
        "explanation": "Moyen mnémotechnique : DAP. La Dure-mère est solide (cuir), l'Arachnoïde ressemble à une toile d'araignée (circulation du LCS), la Pie-mère est collée au cerveau.",
        "tag": "Neuroanat - Protection"
    },
    {
        "q": "Qu'est-ce que la barrière hémato-encéphalique (BHE) ?",
        "options": [
            "Une cloison osseuse",
            "Une barrière physiologique sélective qui empêche le passage de nombreuses substances toxiques ou pathogènes du sang vers le cerveau",
            "Le corps calleux",
            "La membrane des neurones"
        ],
        "answer": "Une barrière physiologique sélective qui empêche le passage de nombreuses substances toxiques ou pathogènes du sang vers le cerveau",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle protège l'homéostasie cérébrale. Seules certaines molécules (glucose, oxygène, alcool, psychotropes) peuvent passer.",
        "tag": "Neuroanat - Vasculaire"
    },
    {
        "q": "Quel nerf crânien (le X) a la plus grande étendue végétative, innervant le cœur, les poumons et le système digestif ?",
        "options": ["Le nerf Olfactif", "Le nerf Trijumeau", "Le nerf Vague (Pneumogastrique)", "Le nerf Facial"],
        "answer": "Le nerf Vague (Pneumogastrique)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le nerf principal du système parasympathique. Un malaise 'vagal' vient d'une hyperactivité de ce nerf (ralentissement cardiaque).",
        "tag": "Neuroanat - Nerfs Crâniens"
    },
    {
        "q": "Dans la moelle épinière, où circulent les informations sensitives (voies afférentes) ?",
        "options": [
            "Dans les cornes antérieures (ventrales)",
            "Dans les cornes postérieures (dorsales) et les cordons postérieurs",
            "Dans le canal central",
            "Elles ne passent pas par la moelle"
        ],
        "answer": "Dans les cornes postérieures (dorsales) et les cordons postérieurs",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Loi de Bell-Magendie : 'Dorsal = Sensitif, Ventral = Moteur'. L'info rentre par le dos de la moelle et la commande sort par le ventre.",
        "tag": "Neuroanat - Moelle"
    },
    {
        "q": "Qu'est-ce que le Système Limbique ?",
        "type": "ouverte",
        "answer": "C'est un ensemble de structures cérébrales (Hippocampe, Amygdale, etc.) impliquées dans la mémoire, les émotions et les comportements instinctifs.",
        "level": "Avancé",
        "explanation": "C'est le 'cerveau émotionnel'. L'hippocampe est crucial pour la mémorisation, l'amygdale pour la gestion de la peur.",
        "tag": "Neuroanat - Fonctionnel"
    },
    {
        "q": "Quelle est la différence entre une atteinte du Motoneurone Central et du Motoneurone Périphérique ?",
        "type": "ouverte",
        "answer": "Central (Cerveau/Moelle) : Paralysie spastique (raideur), hyper-réflexie, signe de Babinski. Périphérique (Nerf) : Paralysie flasque (molle), atrophie musculaire, aréflexie.",
        "level": "Avancé",
        "explanation": "C'est la distinction fondamentale en neurologie clinique pour localiser la lésion.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quel est le plus gros nerf du corps humain, innervant la loge postérieure de la cuisse et une grande partie de la jambe ?",
        "options": ["Le nerf Fémoral", "Le nerf Sciatique (Ischiatique)", "Le nerf Radial", "Le nerf Optique"],
        "answer": "Le nerf Sciatique (Ischiatique)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il sort du bassin par la grande échancrure ischiatique. Une compression de sa racine (L5 ou S1) entraîne une sciatique (douleur irradiant dans la jambe).",
        "tag": "Neuroanat - Périphérique"
    },
    {
        "q": "Quels muscles constituent la 'Coiffe des Rotateurs' de l'épaule ?",
        "options": [
            "Biceps, Triceps, Deltoïde",
            "Supra-épineux, Infra-épineux, Petit Rond, Subscapulaire",
            "Pectoraux et Dorsaux",
            "Trapèze et Sterno-cléido-mastoïdien"
        ],
        "answer": "Supra-épineux, Infra-épineux, Petit Rond, Subscapulaire",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Ces muscles stabilisent la tête de l'humérus dans la glène de l'omoplate. Le supra-épineux est le plus souvent lésé (tendinite).",
        "tag": "Myologie - Membre Sup"
    },
    {
        "q": "Quel nerf est comprimé dans le Syndrome du Canal Carpien ?",
        "options": ["Le nerf Ulnaire", "Le nerf Radial", "Le nerf Médian", "Le nerf Axillaire"],
        "answer": "Le nerf Médian",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Ce nerf gère la sensibilité du pouce, de l'index et du majeur, ainsi que la force de la pince pouce-index.",
        "tag": "Pathologie - Membre Sup"
    },
    {
        "q": "Quelle est la fonction principale du muscle Deltoïde ?",
        "options": ["L'abduction de l'épaule (lever le bras sur le côté)", "La flexion du coude", "L'extension du poignet", "La rotation de la tête"],
        "answer": "L'abduction de l'épaule (lever le bras sur le côté)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le muscle galbe de l'épaule. Il prend le relais du supra-épineux pour lever le bras.",
        "tag": "Myologie - Membre Sup"
    },
    {
        "q": "Qu'est-ce qu'un 'Dermatome' ?",
        "options": [
            "Une maladie de peau",
            "Une zone cutanée innervée par une seule racine nerveuse spinale (ex: C6 pour le pouce)",
            "Un instrument de chirurgie",
            "Un muscle de la peau"
        ],
        "answer": "Une zone cutanée innervée par une seule racine nerveuse spinale (ex: C6 pour le pouce)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Connaître les dermatomes permet de localiser une hernie discale en fonction de l'endroit où le patient a mal ou perd la sensibilité.",
        "tag": "Neuroanat - Clinique"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quel est le risque majeur lors d'une fracture du col de la fibula (péroné) ?",
        "options": [
            "Lésion de l'artère fémorale",
            "Lésion du nerf Fibulaire Commun (SPE) entraînant un pied tombant (steppage)",
            "Rupture du tendon d'Achille",
            "Aucun risque particulier"
        ],
        "answer": "Lésion du nerf Fibulaire Commun (SPE) entraînant un pied tombant (steppage)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le nerf contourne le col de la fibula très superficiellement. S'il est touché, les muscles releveurs du pied sont paralysés.",
        "tag": "Neuroanat - Traumato"
    },
    {
        "q": "Qu'est-ce que le Plexus Brachial ?",
        "type": "ouverte",
        "answer": "C'est un réseau de nerfs formé par les racines spinales de C5 à T1, situé dans le cou et l'aisselle, qui assure l'innervation motrice et sensitive de tout le membre supérieur.",
        "level": "Intermédiaire",
        "explanation": "Tous les grands nerfs du bras (Radial, Médian, Ulnaire...) naissent de ce plexus.",
        "tag": "Neuroanat - Périphérique"
    },
    {
        "q": "Quel muscle est responsable du signe de Trendelenburg (bascule du bassin à la marche) s'il est déficitaire ?",
        "options": ["Le Grand Fessier", "Le Moyen Fessier", "Le Quadriceps", "Les Adducteurs"],
        "answer": "Le Moyen Fessier",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le Moyen Fessier est le stabilisateur latéral du bassin lors de l'appui unipodal. S'il est faible, le bassin tombe du côté opposé à l'appui.",
        "tag": "Biomécanique - Marche"
    },
    {
        "q": "Décrivez l'innervation sensitive de la main par le nerf Ulnaire (Cubital).",
        "type": "ouverte",
        "answer": "Il innerve le petit doigt (auriculaire) et la moitié interne de l'annulaire (4ème doigt), face palmaire et dorsale.",
        "level": "Intermédiaire",
        "explanation": "C'est le nerf qu'on cogne au niveau du coude ('petit juif'), provoquant des fourmis dans le petit doigt.",
        "tag": "Neuroanat - Périphérique"
    },
    {
        "q": "Quels sont les deux os de l'avant-bras et quel mouvement permettent-ils ensemble ?",
        "options": [
            "Tibia et Fibula -> Flexion",
            "Radius et Ulna -> Pronosupination (tourner la main paume haut/bas)",
            "Humérus et Fémur -> Rotation",
            "Scaphoïde et Lunatum -> Glissement"
        ],
        "answer": "Radius et Ulna -> Pronosupination (tourner la main paume haut/bas)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le Radius tourne autour de l'Ulna. La supination, c'est porter la soupe (paume vers le haut). La pronation, c'est prendre (paume vers le bas).",
        "tag": "Anatomie - Membre Sup"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Quelle est la conséquence motrice caractéristique d'une atteinte du Nerf Radial ?",
        "options": [
            "La main en griffe (griffe ulnaire)",
            "La main tombante (paralysie des extenseurs du poignet et des doigts)",
            "La main de singe (perte de l'opposition du pouce)",
            "L'impossibilité de plier le coude"
        ],
        "answer": "La main tombante (paralysie des extenseurs du poignet et des doigts)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le nerf Radial est le nerf de l'EXTENSION (coude, poignet, doigts). S'il est coupé, la main pend.",
        "tag": "Neuroanat - Pathologie"
    },
    {
        "q": "Expliquez le concept de 'Rythme Scapulo-Huméral'.",
        "type": "ouverte",
        "answer": "C'est la coordination entre le mouvement de l'humérus et celui de l'omoplate (scapula). Au-delà de 30° d'abduction, pour 2 degrés de mouvement de l'humérus, la scapula bascule d'1 degré.",
        "level": "Avancé",
        "explanation": "Pour lever le bras à la verticale (180°), l'articulation de l'épaule seule ne suffit pas, l'omoplate doit pivoter sur le thorax.",
        "tag": "Biomécanique"
    },
    {
        "q": "Qu'est-ce que le 'Canal de Guyon' et quelle pathologie y est associée ?",
        "type": "ouverte",
        "answer": "C'est un canal ostéo-fibreux au niveau du poignet (côté petit doigt) où passe le nerf Ulnaire et l'artère ulnaire. Sa compression entraîne un syndrome du canal de Guyon (paresthésies 4ème/5ème doigt, faiblesse intrinsèque).",
        "level": "Avancé",
        "explanation": "C'est l'équivalent du canal carpien mais pour le nerf Ulnaire. Fréquent chez les cyclistes (appui prolongé sur le guidon).",
        "tag": "Neuroanat - Pathologie"
    },
    {
        "q": "Quel muscle est le principal fléchisseur de l'avant-bras, innervé par le nerf Musculo-cutané ?",
        "options": ["Le Triceps Brachial", "Le Biceps Brachial (et le Brachial antérieur)", "Le Rond Pronateur", "L'Anconé"],
        "answer": "Le Biceps Brachial (et le Brachial antérieur)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le nerf musculo-cutané traverse le muscle coraco-brachial. Une lésion entraîne une faiblesse majeure en flexion du coude.",
        "tag": "Myologie - Membre Sup"
    },
    {
        "q": "Quelle est la particularité anatomique du muscle Sterno-Cléido-Mastoïdien (SCM) ?",
        "type": "ouverte",
        "answer": "Il a deux chefs (sterno et cléido), il permet la rotation controlatérale de la tête et l'inclinaison homolatérale. Il est aussi inspirateur accessoire.",
        "level": "Avancé",
        "explanation": "Une contracture unilatérale du SCM entraîne un torticolis congénital ou acquis.",
        "tag": "Myologie - Cou"
    },
    {
        "q": "Dans la marche, quel est le rôle des muscles 'Releveurs du pied' (Tibial Antérieur) lors de la phase oscillante ?",
        "options": [
            "Propulser le corps",
            "Empêcher la pointe du pied de racler le sol (raccourcir le membre)",
            "Amortir le talon",
            "Stabiliser le genou"
        ],
        "answer": "Empêcher la pointe du pied de racler le sol (raccourcir le membre)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Si ce muscle est paralysé (atteinte L5 ou nerf fibulaire), le patient doit lever le genou très haut pour ne pas trébucher : c'est le steppage.",
        "tag": "Biomécanique - Marche"
    },
    {
        "q": "Qu'est-ce que la 'Pince Pollicipitale' et quel nerf est indispensable pour l'opposition du pouce ?",
        "options": [
            "Pince entre le pouce et l'auriculaire -> Nerf Ulnaire",
            "Pince entre le pouce et l'index (ou autres doigts) -> Nerf Médian",
            "Pince avec les deux mains",
            "L'extension du pouce -> Nerf Radial"
        ],
        "answer": "Pince entre le pouce et l'index (ou autres doigts) -> Nerf Médian",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'opposition du pouce (mettre le pouce face aux autres doigts) est le mouvement propre à l'homme, géré par le Médian. Sans lui, la main devient une simple 'palette' (main de singe).",
        "tag": "Anatomie Fonctionnelle"
    },
    {
        "q": "En neurologie périphérique, qu'est-ce qu'un 'Myotome' ?",
        "type": "ouverte",
        "answer": "C'est le groupe de muscles innervés par une même racine nerveuse spinale (ex: L5 pour l'extension des orteils, S1 pour la flexion plantaire).",
        "level": "Avancé",
        "explanation": "Tester la force de groupes musculaires précis permet de remonter à la racine lésée au niveau de la colonne.",
        "tag": "Neuroanat - Clinique"
    },
    {
        "q": "Quel est le trajet du nerf vague (X) dans le cou ?",
        "options": [
            "Il passe dans la colonne vertébrale",
            "Il descend dans la gaine vasculaire avec l'artère carotide et la veine jugulaire interne",
            "Il passe sous la peau",
            "Il s'arrête à la mâchoire"
        ],
        "answer": "Il descend dans la gaine vasculaire avec l'artère carotide et la veine jugulaire interne",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un rapport anatomique vital. Une chirurgie de la carotide peut léser le vague (troubles de la voix, déglutition, cœur).",
        "tag": "Anatomie - Cou"
    },
    {
        "q": "Qu'est-ce que l'Épine de l'Omoplate (Scapula) et que délimite-t-elle ?",
        "type": "ouverte",
        "answer": "C'est une crête osseuse palpable à la face postérieure de la scapula. Elle sépare la fosse supra-épineuse (muscle supra-épineux) de la fosse infra-épineuse (muscle infra-épineux) et se termine par l'Acromion.",
        "level": "Avancé",
        "explanation": "L'acromion s'articule avec la clavicule. C'est un repère essentiel pour la palpation de l'épaule.",
        "tag": "Ostéologie - Membre Sup"
    }, {
        "q": "En embryologie, quelle structure est à l'origine de tout le Système Nerveux Central ?",
        "options": ["L'Endoderme", "Le Tube Neural (ectoderme)", "La Corde", "Le Mésoderme"],
        "answer": "Le Tube Neural (ectoderme)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le système nerveux se forme à partir de la plaque neurale (feuillet externe) qui se replie pour former un tube. S'il ne se ferme pas bien, cela crée des malformations (Spina Bifida).",
        "tag": "Embryologie"
    },
    {
        "q": "Quel est le rôle de la Myéline autour des axones ?",
        "options": [
            "Nourrir le neurone",
            "Accélérer la vitesse de conduction de l'influx nerveux (conduction saltatoire)",
            "Freiner l'influx nerveux",
            "Donner la couleur grise au cerveau"
        ],
        "answer": "Accélérer la vitesse de conduction de l'influx nerveux (conduction saltatoire)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La myéline agit comme un isolant électrique. Dans la Sclérose en Plaques (SEP), cette gaine est détruite, ce qui ralentit ou bloque les informations.",
        "tag": "Neuro-Histologie"
    },
    {
        "q": "Quelle vitamine est prescrite aux femmes enceintes pour prévenir les malformations du tube neural (Spina Bifida) ?",
        "options": ["Vitamine C", "Vitamine B9 (Acide Folique)", "Vitamine D", "Fer"],
        "answer": "Vitamine B9 (Acide Folique)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La fermeture du tube neural a lieu très tôt (4ème semaine), souvent avant que la femme ne sache qu'elle est enceinte. La supplémentation est donc préconisée dès le désir de grossesse.",
        "tag": "Embryologie / Santé Pub"
    },
    {
        "q": "Où se termine la moelle épinière chez l'adulte ?",
        "options": ["En bas du sacrum", "En L1-L2 (relais avec la Queue de Cheval)", "En T12", "Dans le cerveau"],
        "answer": "En L1-L2 (relais avec la Queue de Cheval)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La colonne vertébrale grandit plus vite que la moelle. C'est pourquoi on fait les ponctions lombaires en L3-L4 ou L4-L5, là où il n'y a plus de moelle (risque nul de la piquer).",
        "tag": "Neuroanat - Moelle"
    },
    {
        "q": "Quelle pathologie correspond à une usure 'mécanique' du cartilage, fréquente chez la personne âgée ?",
        "options": ["L'Arthrite", "L'Arthrose", "L'Ostéoporose", "La Scoliose"],
        "answer": "L'Arthrose",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une maladie dégénérative ('rouille'). À distinguer de l'arthrite qui est inflammatoire ('feu').",
        "tag": "Rhumatologie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que la 'Queue de Cheval' (Cauda Equina) ?",
        "type": "ouverte",
        "answer": "C'est le faisceau de racines nerveuses lombo-sacrées qui descendent dans le canal vertébral en dessous de la terminaison de la moelle épinière (L2) avant de sortir par leurs trous de conjugaison.",
        "level": "Intermédiaire",
        "explanation": "Un 'Syndrome de la Queue de Cheval' (compression massive de ces racines) est une urgence chirurgicale absolue (risque d'incontinence définitive).",
        "tag": "Neuroanat - Moelle"
    },
    {
        "q": "Quel est le signe clinique majeur d'une atteinte du système vestibulaire (oreille interne) ?",
        "options": ["La surdité seule", "Le vertige rotatoire (la pièce tourne)", "La cécité", "L'anosmie"],
        "answer": "Le vertige rotatoire (la pièce tourne)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le système vestibulaire gère l'équilibre et la position de la tête. Une atteinte provoque vertiges, nausées et nystagmus (yeux qui sautent).",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Décrivez le réflexe myotatique (réflexe ostéo-tendineux) et son utilité.",
        "type": "ouverte",
        "answer": "C'est la contraction réflexe d'un muscle suite à son étirement brusque (coup de marteau). C'est un arc réflexe monosynaptique (médullaire) qui sert à maintenir le tonus postural et protéger le muscle.",
        "level": "Intermédiaire",
        "explanation": "S'il est aboli -> atteinte périphérique. S'il est vif/exagéré -> atteinte centrale (levée de l'inhibition).",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Qu'est-ce que le 'Spina Bifida' ?",
        "options": [
            "Une courbure de la colonne",
            "Une malformation congénitale liée à un défaut de fermeture de l'arc postérieur des vertèbres (et souvent du tube neural)",
            "Une fracture de fatigue",
            "Une tumeur bénigne"
        ],
        "answer": "Une malformation congénitale liée à un défaut de fermeture de l'arc postérieur des vertèbres (et souvent du tube neural)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Cela peut aller de la forme occulta (invisible) à la forme aperta (moelle à l'air libre, paralysie des jambes).",
        "tag": "Embryologie / Pathologie"
    },
    {
        "q": "Quelle est la différence entre une 'Paraplégie' et une 'Tétraplégie' ?",
        "options": [
            "Para = 1 jambe, Tétra = 2 jambes",
            "Paraplégie = paralysie des membres inférieurs (lésion dorsale/lombaire). Tétraplégie = paralysie des 4 membres (lésion cervicale)",
            "C'est pareil",
            "Tétraplégie = paralysie du visage"
        ],
        "answer": "Paraplégie = paralysie des membres inférieurs (lésion dorsale/lombaire). Tétraplégie = paralysie des 4 membres (lésion cervicale)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le niveau de la lésion sur la moelle épinière détermine l'étendue de la paralysie. Plus c'est haut, plus c'est grave.",
        "tag": "Neuroanat - Clinique"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le 'Syndrome de Brown-Séquard' (Hémisection de la moelle).",
        "type": "ouverte",
        "answer": "C'est une lésion de la moitié de la moelle. Du côté de la lésion : Paralysie motrice et perte de sensibilité tactile fine/proprioceptive. Du côté opposé : Perte de la sensibilité thermo-algique (douleur/chaud/froid).",
        "level": "Avancé",
        "explanation": "Cela s'explique par le fait que les voies motrices et tactiles croisent dans le bulbe (haut), alors que les voies de la douleur croisent tout de suite dans la moelle.",
        "tag": "Neuroanat - Syndrome"
    },
    {
        "q": "Quel neurotransmetteur est déficitaire dans la Maladie de Parkinson et dans quelle zone précise ?",
        "options": [
            "La Sérotonine dans le cortex",
            "La Dopamine dans la Substance Noire (Locus Niger)",
            "L'Acétylcholine dans les muscles",
            "Le GABA dans le cervelet"
        ],
        "answer": "La Dopamine dans la Substance Noire (Locus Niger)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La destruction des neurones dopaminergiques de la substance noire perturbe la boucle des ganglions de la base, entraînant la triade : Tremblement de repos, Rigidité, Akinésie.",
        "tag": "Neuro-Pathologie"
    },
    {
        "q": "Qu'est-ce que le signe de 'Lasègue' et que recherche-t-il ?",
        "type": "ouverte",
        "answer": "C'est une manœuvre clinique où l'on élève la jambe tendue du patient allongé. S'il déclenche une douleur irradiant dans la fesse et la jambe (avant 60°), c'est un signe d'irritation du nerf sciatique (conflit disco-radiculaire).",
        "level": "Avancé",
        "explanation": "Incontournable en examen clinique pour diagnostiquer une sciatique sur hernie discale.",
        "tag": "Neuroanat - Clinique"
    },
    {
        "q": "En embryologie, que deviennent les cellules de la 'Crête Neurale' ?",
        "options": [
            "Elles disparaissent",
            "Elles migrent pour former le Système Nerveux Périphérique (ganglions, nerfs), les mélanocytes et une partie de la face",
            "Elles forment le cerveau",
            "Elles forment les os"
        ],
        "answer": "Elles migrent pour former le Système Nerveux Périphérique (ganglions, nerfs), les mélanocytes et une partie de la face",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "On appelle parfois la crête neurale le '4ème feuillet' tant son rôle est important. Une anomalie de migration crée des pathologies complexes (neurocristopathies).",
        "tag": "Embryologie"
    },
    {
        "q": "Quelle est la différence entre une 'Hernie Discale' et une 'Protrusion Discale' ?",
        "type": "ouverte",
        "answer": "Protrusion : le disque s'étale globalement mais l'anneau fibreux est intact. Hernie : l'anneau fibreux est rompu, le noyau gélatineux sort (s'exclut) et vient comprimer la racine nerveuse.",
        "level": "Avancé",
        "explanation": "La hernie est plus agressive et douloureuse (conflit direct) que la protrusion (vieillissement discal).",
        "tag": "Pathologie Rachidienne"
    },
    {
        "q": "Qu'est-ce que l'artère d'Adamkiewicz ?",
        "options": [
            "Une artère du bras",
            "L'artère principale vascularisant la moelle épinière thoraco-lombaire",
            "Une artère du cerveau",
            "L'artère du fémur"
        ],
        "answer": "L'artère principale vascularisant la moelle épinière thoraco-lombaire",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle est unique et vitale. Si elle est touchée lors d'une chirurgie de l'aorte, le patient peut se réveiller paraplégique (ischémie médullaire).",
        "tag": "Neuroanat - Vasculaire"
    },
    {
        "q": "Analysez la différence entre une atteinte radiculaire L5 et S1 (Sciatique).",
        "type": "ouverte",
        "answer": "L5 : Douleur face externe cuisse/jambe, passe devant la malléole, finit sur le gros orteil. Déficit : Relever le pied (marche sur talons impossible). S1 : Douleur fesse/arrière cuisse/mollet, talon, plante pied. Déficit : Pointe de pied (marche sur pointes impossible).",
        "level": "Avancé",
        "explanation": "Moyen mnémotechnique : L5 vers le gros orteil, S1 vers le petit orteil/plante. S1 abolit aussi le réflexe achilléen.",
        "tag": "Neuroanat - Clinique"
    },
    {
        "q": "Qu'est-ce que la Proprioception consciente et quelle voie emprunte-t-elle ?",
        "options": [
            "La douleur -> Voie extra-lemniscale",
            "La sensibilité profonde (position des articulations) et tactile fine -> Voie Lemniscale (Cordons postérieurs)",
            "La motricité -> Voie Pyramidale",
            "La vision -> Nerf Optique"
        ],
        "answer": "La sensibilité profonde (position des articulations) et tactile fine -> Voie Lemniscale (Cordons postérieurs)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le 'sens du corps'. L'info remonte tout droit dans la moelle et croise seulement dans le tronc cérébral. Essentiel pour le psychomotricien.",
        "tag": "Neuroanat - Voies"
    },
    {
        "q": "Quelles sont les 3 vésicules primitives du cerveau de l'embryon ?",
        "type": "ouverte",
        "answer": "Prosencéphale (Cerveau antérieur), Mésencéphale (Cerveau moyen), Rhombencéphale (Cerveau postérieur).",
        "level": "Avancé",
        "explanation": "Elles vont se diviser ensuite en 5 vésicules pour donner le cerveau adulte (ex: le Prosencéphale donne Télencéphale + Diencéphale).",
        "tag": "Embryologie"
    },
    {
        "q": "Pourquoi une lésion haute du rachis cervical (C1-C4) est-elle critique pour la survie ?",
        "options": [
            "Car on ne peut plus bouger les bras",
            "Car elle atteint le nerf Phrénique (C3-C4-C5) qui commande le diaphragme -> Arrêt respiratoire",
            "Car elle coupe la digestion",
            "Car elle fait mal à la tête"
        ],
        "answer": "Car elle atteint le nerf Phrénique (C3-C4-C5) qui commande le diaphragme -> Arrêt respiratoire",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Moyen mnémotechnique anglais : 'C3, C4, C5 keep the diaphragm alive'. Une lésion au-dessus de C3 nécessite une ventilation artificielle à vie (type Christopher Reeve).",
        "tag": "Neuroanat - Clinique"
    },

    
    ],

    "MODULE 3: Physiologie": [
        # CELLULE & HOMÉOSTASIE
        {
        "q": "Qu'est-ce que l'homéostasie ?",
        "options": [
            "La coagulation du sang",
            "La capacité de l'organisme à maintenir ses constantes physiologiques (température, pH, glycémie) dans des limites stables malgré les perturbations extérieures",
            "La division cellulaire",
            "La digestion des aliments"
        ],
        "answer": "La capacité de l'organisme à maintenir ses constantes physiologiques (température, pH, glycémie) dans des limites stables malgré les perturbations extérieures",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le concept central de la physiologie (Claude Bernard/Cannon). Si l'homéostasie est rompue, c'est la maladie ou la mort.",
        "tag": "Concepts de base"
    },
    {
        "q": "Quelle est l'unité fonctionnelle de base du muscle squelettique ?",
        "options": ["Le neurone", "Le sarcomère", "L'ostéone", "Le néphron"],
        "answer": "Le sarcomère",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le sarcomère est la plus petite portion de fibre musculaire capable de se contracter, située entre deux stries Z.",
        "tag": "Physio Musculaire"
    },
    {
        "q": "Quel est le rôle des dendrites sur un neurone ?",
        "options": [
            "Transmettre l'information vers un autre neurone (sortie)",
            "Recevoir les informations provenant d'autres neurones et les acheminer vers le corps cellulaire (entrée)",
            "Protéger le noyau",
            "Produire de l'énergie"
        ],
        "answer": "Recevoir les informations provenant d'autres neurones et les acheminer vers le corps cellulaire (entrée)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Les dendrites sont les 'antennes' réceptrices. L'axone est le câble émetteur.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quelle est la valeur moyenne du Potentiel de Repos d'un neurone ?",
        "options": ["0 mV", "+30 mV", "-70 mV", "-120 mV"],
        "answer": "-70 mV",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'intérieur du neurone est négatif par rapport à l'extérieur. Cette polarité est maintenue par la pompe Na+/K+.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quel ion est indispensable pour déclencher la contraction musculaire en se liant à la troponine ?",
        "options": ["Le Sodium (Na+)", "Le Potassium (K+)", "Le Calcium (Ca2+)", "Le Magnésium (Mg2+)"],
        "answer": "Le Calcium (Ca2+)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Sans Calcium, les sites de fixation sur l'actine sont masqués. Le Calcium lève ce masque et permet l'accrochage myosine-actine.",
        "tag": "Physio Musculaire"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Expliquez la différence entre transport passif et transport actif à travers la membrane cellulaire.",
        "type": "ouverte",
        "answer": "Transport Passif : se fait sans énergie, dans le sens du gradient de concentration (du + concentré vers le - concentré). Transport Actif : nécessite de l'énergie (ATP) pour aller contre le gradient (ex: pompe Na+/K+).",
        "level": "Intermédiaire",
        "explanation": "C'est fondamental pour comprendre comment les cellules maintiennent leurs concentrations ioniques différentes de celles du sang.",
        "tag": "Physio Cellulaire"
    },
    {
        "q": "Qu'est-ce qu'une 'Unité Motrice' ?",
        "options": [
            "Un muscle entier",
            "Un motoneurone alpha et l'ensemble des fibres musculaires qu'il innerve",
            "Une mitochondrie",
            "Un réflexe"
        ],
        "answer": "Un motoneurone alpha et l'ensemble des fibres musculaires qu'il innerve",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Quand le motoneurone tire, toutes les fibres de son unité se contractent en même temps. Pour un mouvement fin (œil), une unité contient peu de fibres. Pour la force (cuisse), elle en contient des milliers.",
        "tag": "Physio Musculaire"
    },
    {
        "q": "Quel est le rôle de la pompe Na+/K+ ATPase ?",
        "type": "ouverte",
        "answer": "Elle expulse 3 ions Na+ et fait entrer 2 ions K+ en consommant de l'ATP. Elle permet de maintenir le potentiel de repos négatif (-70mV) et les gradients de concentration.",
        "level": "Intermédiaire",
        "explanation": "Sans elle, les ions s'équilibreraient et le neurone ne pourrait plus transmettre d'influx électrique (mort cérébrale).",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Qu'est-ce que la 'Période Réfractaire' d'un neurone ?",
        "options": [
            "Le moment où il dort",
            "Une brève période après un potentiel d'action où le neurone est inexcitable et ne peut pas générer de nouveau signal",
            "La période de croissance du neurone",
            "Le temps de transmission synaptique"
        ],
        "answer": "Une brève période après un potentiel d'action où le neurone est inexcitable et ne peut pas générer de nouveau signal",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Elle oblige l'influx nerveux à aller dans un seul sens (il ne peut pas faire demi-tour) et limite la fréquence maximale des décharges.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quelle est la différence fonctionnelle entre les fibres musculaires de Type I et de Type II ?",
        "type": "ouverte",
        "answer": "Type I (Rouges, Lentes) : Endurantes, métabolisme aérobie, posture. Type II (Blanches, Rapides) : Explosives, métabolisme anaérobie, fatigables.",
        "level": "Intermédiaire",
        "explanation": "Un sprinter a beaucoup de type II, un marathonien beaucoup de type I. Les muscles posturaux du dos sont riches en type I.",
        "tag": "Physio Musculaire"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Décrivez les étapes ioniques du Potentiel d'Action (PA).",
        "type": "ouverte",
        "answer": "1. Dépolarisation (ouverture canaux Na+ voltage-dépendants, entrée massive de Na+). 2. Repolarisation (fermeture Na+, ouverture K+, sortie de K+). 3. Hyperpolarisation (sortie excessive de K+). 4. Retour au repos (pompe Na/K).",
        "level": "Avancé",
        "explanation": "C'est un phénomène 'Tout ou Rien'. Une fois le seuil atteint (-55mV), la séquence est inarrêtable.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Qu'est-ce que la conduction 'saltatoire' et quel est son avantage ?",
        "options": [
            "L'influx saute d'un neurone à l'autre",
            "L'influx saute d'un nœud de Ranvier à l'autre le long d'un axone myélinisé, ce qui augmente considérablement la vitesse de conduction",
            "C'est une conduction lente pour la douleur",
            "C'est la conduction dans les muscles"
        ],
        "answer": "L'influx saute d'un nœud de Ranvier à l'autre le long d'un axone myélinisé, ce qui augmente considérablement la vitesse de conduction",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Sur un axone myélinisé, la vitesse peut atteindre 100 m/s, contre 1 m/s sur un axone non myélinisé.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Expliquez le mécanisme de la 'Sommation Spatiale' au niveau d'un neurone.",
        "type": "ouverte",
        "answer": "C'est l'addition simultanée des potentiels postsynaptiques (excitateurs et inhibiteurs) provenant de plusieurs synapses différentes sur le même neurone. Si la somme atteint le seuil, un PA est déclenché.",
        "level": "Avancé",
        "explanation": "Le neurone fait en permanence la somme algébrique des 'Oui' (excitation) et des 'Non' (inhibition) qu'il reçoit pour décider s'il tire ou non.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Qu'est-ce que le Tétanos physiologique (et non la maladie) ?",
        "options": [
            "Une crampe douloureuse",
            "La fusion des secousses musculaires due à une stimulation à haute fréquence, donnant une contraction lisse et maintenue",
            "La relaxation totale du muscle",
            "La rupture du tendon"
        ],
        "answer": "La fusion des secousses musculaires due à une stimulation à haute fréquence, donnant une contraction lisse et maintenue",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Tous nos mouvements volontaires sont des tétanos physiologiques. Si la fréquence de commande baisse, on a des tremblements.",
        "tag": "Physio Musculaire"
    },
    {
        "q": "Quel est le rôle de l'ATP dans la relaxation musculaire (et non la contraction) ?",
        "type": "ouverte",
        "answer": "L'ATP est nécessaire pour détacher la tête de myosine de l'actine et pour repomper le Calcium dans le réticulum sarcoplasmique.",
        "level": "Avancé",
        "explanation": "C'est pourquoi lors de la mort (plus d'ATP), les muscles restent figés : c'est la rigidité cadavérique (Rigor Mortis). Le muscle ne peut plus se relâcher.",
        "tag": "Physio Musculaire"
    },
    {
        "q": "Comment fonctionne une synapse chimique ?",
        "options": [
            "Le courant passe directement",
            "Arrivée du PA -> Entrée de Calcium -> Exocytose des neurotransmetteurs -> Fixation sur récepteurs postsynaptiques -> Ouverture canaux ioniques",
            "Le neurone touche le muscle",
            "Par magie"
        ],
        "answer": "Arrivée du PA -> Entrée de Calcium -> Exocytose des neurotransmetteurs -> Fixation sur récepteurs postsynaptiques -> Ouverture canaux ioniques",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'étape cruciale est l'entrée de Calcium dans le bouton pré-synaptique qui déclenche la libération des vésicules.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Qu'est-ce qu'un PPSE (Potentiel Post-Synaptique Excitateur) ?",
        "options": [
            "Une hyperpolarisation qui freine le neurone",
            "Une dépolarisation locale de la membrane postsynaptique qui rapproche le potentiel du seuil de déclenchement",
            "Un potentiel d'action complet",
            "Une protéine"
        ],
        "answer": "Une dépolarisation locale de la membrane postsynaptique qui rapproche le potentiel du seuil de déclenchement",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Souvent dû à une entrée de Sodium (Na+). À l'inverse, un PPSI (Inhibiteur) est une hyperpolarisation (entrée de Chlore Cl- ou sortie de K+) qui éloigne du seuil.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "En physiologie de l'effort, qu'est-ce que la 'Dette d'Oxygène' ?",
        "type": "ouverte",
        "answer": "C'est la consommation d'oxygène qui reste élevée après l'arrêt de l'effort. Elle sert à re-synthétiser les stocks d'énergie (ATP, Phosphocréatine) et à éliminer l'acide lactique.",
        "level": "Avancé",
        "explanation": "C'est pour cela qu'on continue de souffler fort après avoir couru.",
        "tag": "Physio Effort"
    },
    {
        "q": "Quelle est la loi de recrutement de Henneman (Size Principle) ?",
        "type": "ouverte",
        "answer": "Les unités motrices sont recrutées de la plus petite (fibres lentes, faibles) à la plus grosse (fibres rapides, fortes) en fonction de l'intensité de l'effort demandé.",
        "level": "Avancé",
        "explanation": "Cela permet des mouvements fluides. Pour soulever un stylo, je n'active que les petites unités. Pour une haltère, j'ajoute les grosses.",
        "tag": "Physio Musculaire"
    },
    {
        "q": "Quel est le rôle des Fuseaux Neuromusculaires ?",
        "options": [
            "Mesurer la tension du tendon",
            "Mesurer la longueur du muscle et sa vitesse d'étirement (récepteurs proprioceptifs)",
            "Produire la force",
            "Lubrifier le muscle"
        ],
        "answer": "Mesurer la longueur du muscle et sa vitesse d'étirement (récepteurs proprioceptifs)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Ils sont à l'origine du réflexe myotatique. Les Organes Tendineux de Golgi, eux, mesurent la tension (force) dans le tendon.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quelle est la fonction globale du Système Nerveux Sympathique (Orthosympathique) ?",
        "options": [
            "Le repos et la digestion",
            "La préparation à l'action, au stress et à l'urgence ('Fight or Flight')",
            "L'endormissement",
            "La production d'urine"
        ],
        "answer": "La préparation à l'action, au stress et à l'urgence ('Fight or Flight')",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il mobilise l'énergie : accélération du cœur, dilatation des pupilles, augmentation de la force musculaire.",
        "tag": "Physio SN Autonome"
    },
    {
        "q": "Dans l'œil, quels photorécepteurs sont responsables de la vision des couleurs et de la précision (acuité) ?",
        "options": ["Les Bâtonnets", "Les Cônes", "Le Cristallin", "La Cornée"],
        "answer": "Les Cônes",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Les cônes (Rouge, Vert, Bleu) ont besoin de beaucoup de lumière. Les bâtonnets, eux, voient en noir et blanc mais sont très sensibles dans la pénombre.",
        "tag": "Physio Sensorielle"
    },
    {
        "q": "Où se situe l'organe principal de l'équilibre (système vestibulaire) ?",
        "options": ["Dans le cervelet", "Dans l'oreille interne", "Dans les yeux", "Dans la plante des pieds"],
        "answer": "Dans l'oreille interne",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le vestibule est accolé à la cochlée (audition). Il détecte les mouvements de la tête.",
        "tag": "Physio Vestibulaire"
    },
    {
        "q": "Quel neurotransmetteur est principalement utilisé par le Système Parasympathique ?",
        "options": ["L'Adrénaline", "L'Acétylcholine", "La Dopamine", "Le Glutamate"],
        "answer": "L'Acétylcholine",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est lui qui ralentit le cœur (frein vagal) et stimule la digestion.",
        "tag": "Physio SN Autonome"
    },
    {
        "q": "Qu'est-ce que l'accommodation visuelle ?",
        "options": [
            "S'habituer à l'obscurité",
            "La capacité du cristallin à modifier sa courbure pour faire la mise au point sur des objets proches",
            "Le mouvement des yeux",
            "La fermeture de la paupière"
        ],
        "answer": "La capacité du cristallin à modifier sa courbure pour faire la mise au point sur des objets proches",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Avec l'âge, le cristallin perd sa souplesse et ne peut plus bomber suffisamment : c'est la presbytie.",
        "tag": "Physio Vision"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quel est l'effet du Système Sympathique sur les pupilles ?",
        "options": ["Myosis (rétrécissement)", "Mydriase (dilatation)", "Aucun effet", "Fermeture des yeux"],
        "answer": "Mydriase (dilatation)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "En cas de danger (stress), la pupille s'ouvre pour capter le maximum d'informations visuelles périphériques.",
        "tag": "Physio SN Autonome"
    },
    {
        "q": "Qu'est-ce que la 'Tache Aveugle' (Papille optique) sur la rétine ?",
        "type": "ouverte",
        "answer": "C'est la zone où le nerf optique quitte l'œil. Il n'y a aucun photorécepteur (ni cônes ni bâtonnets) à cet endroit, donc le cerveau ne reçoit aucune image de cette zone.",
        "level": "Intermédiaire",
        "explanation": "Le cerveau 'bouche le trou' en reconstituant l'image par interpolation avec l'autre œil.",
        "tag": "Physio Vision"
    },
    {
        "q": "À quoi servent les Canaux Semi-Circulaires de l'oreille interne ?",
        "options": [
            "À entendre les sons aigus",
            "À détecter les accélérations angulaires (rotations de la tête : Oui, Non, Peut-être)",
            "À détecter la gravité",
            "À évacuer le cérumen"
        ],
        "answer": "À détecter les accélérations angulaires (rotations de la tête : Oui, Non, Peut-être)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Il y en a 3 par oreille (un dans chaque plan de l'espace X, Y, Z). Ils contiennent un liquide (endolymphe) qui bouge quand on tourne la tête.",
        "tag": "Physio Vestibulaire"
    },
    {
        "q": "Pourquoi la fréquence cardiaque augmente-t-elle à l'inspiration (Arythmie sinusale respiratoire) ?",
        "type": "ouverte",
        "answer": "À l'inspiration, la pression intrathoracique baisse, le retour veineux augmente, et le tonus vagal (parasympathique) diminue temporairement, ce qui laisse le cœur accélérer légèrement.",
        "level": "Intermédiaire",
        "explanation": "C'est un signe de bonne santé (variabilité cardiaque) et de bon fonctionnement du système nerveux autonome.",
        "tag": "Physio Cardio"
    },
    {
        "q": "Physiologiquement, qu'est-ce que la Myopie ?",
        "options": [
            "L'œil est trop court, l'image se forme derrière la rétine",
            "L'œil est trop long (ou trop puissant), l'image se forme EN AVANT de la rétine",
            "Le cristallin est opaque",
            "Le nerf optique est coupé"
        ],
        "answer": "L'œil est trop long (ou trop puissant), l'image se forme EN AVANT de la rétine",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le myope voit flou de loin. On corrige avec une lentille divergente (concave) pour reculer l'image sur la rétine.",
        "tag": "Physio Vision"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le 'Réflexe Vestibulo-Oculaire' (VOR) et son importance capitale en motricité.",
        "type": "ouverte",
        "answer": "C'est un réflexe qui génère un mouvement des yeux de vitesse égale mais de sens opposé au mouvement de la tête. Il permet de stabiliser le regard sur une cible (vision nette) pendant que l'on bouge.",
        "level": "Avancé",
        "explanation": "Sans VOR, le monde 'sauterait' visuellement à chaque pas ou mouvement de tête (oscillopsie). C'est la base de la coordination visuo-motrice.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quelle est la particularité des Otolithes (Utricule et Saccule) par rapport aux canaux semi-circulaires ?",
        "type": "ouverte",
        "answer": "Les Otolithes détectent les accélérations LINÉAIRES (avancer en voiture, monter en ascenseur) et la position de la tête par rapport à la GRAVITÉ (tête penchée), grâce à des petits cristaux pesants.",
        "level": "Avancé",
        "explanation": "Ce sont eux qui nous disent où est le 'bas' (verticale) même les yeux fermés.",
        "tag": "Physio Vestibulaire"
    },
    {
        "q": "Au niveau du Chiasma Optique, quelles fibres nerveuses croisent la ligne médiane ?",
        "options": [
            "Toutes les fibres",
            "Uniquement les fibres provenant de la rétine NASALE (qui voient le champ visuel temporal/externe)",
            "Uniquement les fibres de la rétine temporale",
            "Aucune fibre"
        ],
        "answer": "Uniquement les fibres provenant de la rétine NASALE (qui voient le champ visuel temporal/externe)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cette décussation partielle permet la vision stéréoscopique (3D). Une lésion du chiasma (ex: tumeur hypophyse) entraîne une hémianopsie bitemporale (vision en œillères).",
        "tag": "Neuroanat - Vision"
    },
    {
        "q": "Quel est le mécanisme surprenant de la photo-transduction (réaction à la lumière) dans les photorécepteurs ?",
        "options": [
            "La lumière dépolarise le récepteur (comme les autres neurones)",
            "La lumière HYPERPOLARISE le photorécepteur et arrête la libération de neurotransmetteur (glutamate)",
            "La lumière chauffe la cellule",
            "La lumière fait exploser le pigment"
        ],
        "answer": "La lumière HYPERPOLARISE le photorécepteur et arrête la libération de neurotransmetteur (glutamate)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "À l'obscurité, le photorécepteur est dépolarisé en permanence. La lumière 'éteint' ce courant d'obscurité. C'est l'inverse de la logique habituelle (stimulus = dépolarisation).",
        "tag": "Physio Cellulaire"
    },
    {
        "q": "Le nerf Vague (X) est le vecteur principal du parasympathique. Jusqu'où s'étend son action digestive ?",
        "options": [
            "Juste à l'estomac",
            "Jusqu'à l'angle gauche du côlon (côlon transverse distal), couvrant tout le grêle et le début du côlon",
            "Jusqu'à l'anus",
            "Il n'innerve pas le digestif"
        ],
        "answer": "Jusqu'à l'angle gauche du côlon (côlon transverse distal), couvrant tout le grêle et le début du côlon",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La fin du tube digestif (côlon descendant, rectum) et la vessie sont innervés par le parasympathique sacré (nerfs érecteurs) et non le vague.",
        "tag": "Physio SN Autonome"
    },
    {
        "q": "Qu'est-ce que la 'Fovéa' et pourquoi l'acuité visuelle y est-elle maximale ?",
        "type": "ouverte",
        "answer": "C'est une petite dépression au centre de la macula contenant exclusivement des CÔNES très serrés. Les couches de neurones sus-jacentes sont écartées pour laisser passer la lumière directement.",
        "level": "Avancé",
        "explanation": "Pour regarder un détail, on doit aligner l'œil pour que l'image tombe pile sur la fovéa. Le reste de la rétine est flou.",
        "tag": "Physio Vision"
    },
    {
        "q": "Comment le système sympathique régule-t-il la pression artérielle lors du passage de la position couchée à debout (Baroréflexe) ?",
        "options": [
            "Il ne fait rien",
            "Il détecte la baisse de pression (barorécepteurs carotidiens) -> Stimule le sympathique -> Vasoconstriction + Tachycardie pour remonter la pression",
            "Il stimule le parasympathique pour calmer le cœur",
            "Il dilate les vaisseaux"
        ],
        "answer": "Il détecte la baisse de pression (barorécepteurs carotidiens) -> Stimule le sympathique -> Vasoconstriction + Tachycardie pour remonter la pression",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Si ce réflexe est trop lent (fatigue, médicaments, vieillesse), on fait un malaise vagal ou une hypotension orthostatique (voile noir en se levant).",
        "tag": "Physio Cardio"
    },
    {
        "q": "Quelle est la différence fondamentale entre Proprioception et Système Vestibulaire ?",
        "type": "ouverte",
        "answer": "La Proprioception informe sur la position des segments du corps les uns par rapport aux autres (via muscles/tendons). Le Vestibulaire informe sur la position et le mouvement de la TÊTE dans l'espace (gravité/accélération).",
        "level": "Avancé",
        "explanation": "L'équilibre résulte de l'intégration de ces deux sens + la Vision.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Les glandes surrénales (médullosurrénale) sont considérées comme un ganglion sympathique modifié. Que sécrètent-elles dans le sang ?",
        "options": ["Cortisol", "Adrénaline (80%) et Noradrénaline (20%)", "Insuline", "Testostérone"],
        "answer": "Adrénaline (80%) et Noradrénaline (20%)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cela prolonge l'effet du système nerveux sympathique par voie hormonale (effet plus durable que l'influx nerveux direct).",
        "tag": "Endocrinologie"
    },
    {
        "q": "Qu'est-ce que le 'Nystagmus' physiologique ?",
        "type": "ouverte",
        "answer": "C'est un mouvement réflexe des yeux composé d'une phase lente (suivi d'une cible ou VOR) et d'une phase rapide de rappel (saccade) pour recentrer l'œil.",
        "level": "Avancé",
        "explanation": "On l'observe quand on regarde le paysage défiler dans un train (Nystagmus optocinétique). S'il apparaît au repos, c'est pathologique (vertige).",
        "tag": "Neuro-Ophtalmologie"
    },
    {
        "q": "Quelle est la différence entre la Petite et la Grande Circulation ?",
        "options": [
            "La petite est pour les enfants, la grande pour les adultes",
            "Petite (Pulmonaire) = Cœur Droit -> Poumons -> Cœur Gauche. Grande (Systémique) = Cœur Gauche -> Tout le corps -> Cœur Droit",
            "La petite va au cerveau, la grande aux jambes",
            "C'est la vitesse du sang qui change"
        ],
        "answer": "Petite (Pulmonaire) = Cœur Droit -> Poumons -> Cœur Gauche. Grande (Systémique) = Cœur Gauche -> Tout le corps -> Cœur Droit",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La petite circulation sert à recharger le sang en oxygène. La grande sert à distribuer cet oxygène aux organes.",
        "tag": "Physio Cardio"
    },
    {
        "q": "Quel est le muscle inspiratoire principal ?",
        "options": ["Les abdominaux", "Le Diaphragme", "Les pectoraux", "Le trapèze"],
        "answer": "Le Diaphragme",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Lorsqu'il se contracte, il s'abaisse, augmentant le volume de la cage thoracique, ce qui aspire l'air dans les poumons (comme une seringue).",
        "tag": "Physio Respi"
    },
    {
        "q": "Qu'est-ce que la Systole ?",
        "options": ["La phase de remplissage du cœur (repos)", "La phase de contraction et d'éjection du sang", "L'arrêt cardiaque", "La mesure de la tension"],
        "answer": "La phase de contraction et d'éjection du sang",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le cœur pompe en deux temps : Diastole (je me remplis) -> Systole (j'éjecte).",
        "tag": "Physio Cardio"
    },
    {
        "q": "Où ont lieu les échanges gazeux (O2/CO2) dans les poumons ?",
        "options": ["Dans la trachée", "Dans les bronches", "Dans les alvéoles pulmonaires", "Dans la plèvre"],
        "answer": "Dans les alvéoles pulmonaires",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Les alvéoles sont de minuscules sacs entourés de capillaires sanguins. La barrière est si fine que les gaz passent par simple diffusion.",
        "tag": "Physio Respi"
    },
    {
        "q": "Quelle est la valeur normale de la fréquence cardiaque de repos chez l'adulte ?",
        "options": ["30-40 bpm", "60-80 bpm", "100-120 bpm", "150 bpm"],
        "answer": "60-80 bpm",
        "type": "qcm",
        "level": "Basique",
        "explanation": "En dessous de 60, c'est une bradycardie. Au-dessus de 100, c'est une tachycardie.",
        "tag": "Physio Cardio"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Définissez le 'Débit Cardiaque' (Q) et sa formule.",
        "type": "ouverte",
        "answer": "C'est le volume de sang éjecté par le cœur par minute. Formule : Q = Fréquence Cardiaque (FC) x Volume d'Éjection Systolique (VES).",
        "level": "Intermédiaire",
        "explanation": "Au repos, il est d'environ 5 L/min. À l'effort, il peut monter à 20-25 L/min en augmentant la fréquence et le volume éjecté.",
        "tag": "Physio Cardio"
    },
    {
        "q": "Sur un ECG (Électrocardiogramme), que représente le complexe QRS ?",
        "options": [
            "La contraction des oreillettes",
            "La dépolarisation (contraction) des ventricules",
            "Le repos du cœur",
            "La repolarisation"
        ],
        "answer": "La dépolarisation (contraction) des ventricules",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "L'onde P = Oreillettes. Le QRS = Ventricules (c'est le gros pic car les ventricules sont puissants). L'onde T = Repolarisation (repos) des ventricules.",
        "tag": "Physio Cardio"
    },
    {
        "q": "Qu'est-ce que le Surfactant pulmonaire ?",
        "type": "ouverte",
        "answer": "C'est une substance lipidique sécrétée par les alvéoles qui diminue la tension superficielle, empêchant les alvéoles de s'effondrer (collaber) à l'expiration.",
        "level": "Intermédiaire",
        "explanation": "Chez le prématuré, l'absence de surfactant provoque une détresse respiratoire grave (maladie des membranes hyalines).",
        "tag": "Physio Respi"
    },
    {
        "q": "Quel est le stimulus principal qui déclenche l'envie de respirer (régulation chimique) ?",
        "options": [
            "Le manque d'Oxygène (Hypoxie)",
            "L'excès de CO2 (Hypercapnie) et l'acidité du sang",
            "La volonté consciente",
            "La fréquence cardiaque"
        ],
        "answer": "L'excès de CO2 (Hypercapnie) et l'acidité du sang",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Paradoxalement, ce n'est pas le manque d'O2 qui nous fait respirer, mais l'accumulation de déchets (CO2). On respire pour éliminer l'acide.",
        "tag": "Physio Respi"
    },
    {
        "q": "Quelle est la différence entre artères et veines ?",
        "type": "ouverte",
        "answer": "Les Artères partent du cœur (haute pression, paroi épaisse/élastique). Les Veines reviennent au cœur (basse pression, paroi fine, présence de valvules anti-reflux).",
        "level": "Intermédiaire",
        "explanation": "Attention : ce n'est pas la couleur du sang ! L'artère pulmonaire contient du sang 'bleu' (pauvre en O2), mais c'est une artère car elle part du cœur.",
        "tag": "Anatomie Vasculaire"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez la 'Loi de Frank-Starling' (Loi du cœur).",
        "type": "ouverte",
        "answer": "Plus le cœur se remplit pendant la diastole (étirement des fibres myocardiques), plus il se contracte fort ensuite pour éjecter le sang.",
        "level": "Avancé",
        "explanation": "C'est un mécanisme d'autorégulation mécanique : le cœur adapte sa force d'éjection au volume de sang qui lui arrive (Retour Veineux).",
        "tag": "Physio Cardio"
    },
    {
        "q": "Qu'est-ce que la 'Capacité Vitale' (CV) en spirométrie ?",
        "options": [
            "Le volume d'air qui reste dans les poumons après avoir tout soufflé",
            "Le volume maximal d'air que l'on peut mobiliser (Inspiration max + Expiration max)",
            "Le volume d'une respiration normale",
            "La taille des poumons"
        ],
        "answer": "Le volume maximal d'air que l'on peut mobiliser (Inspiration max + Expiration max)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "CV = Volume Courant + Volume de Réserve Inspiratoire + Volume de Réserve Expiratoire. Il ne manque que le Volume Résiduel pour faire la Capacité Pulmonaire Totale.",
        "tag": "Physio Respi"
    },
    {
        "q": "Décrivez le trajet de l'influx électrique cardiaque (Système de conduction).",
        "type": "ouverte",
        "answer": "Nœud Sinusal (pacemaker naturel, oreillette droite) -> Nœud Auriculo-Ventriculaire (AV) -> Faisceau de His -> Branches droite/gauche -> Réseau de Purkinje (ventricules).",
        "level": "Avancé",
        "explanation": "Le nœud AV impose un léger délai pour laisser le temps aux oreillettes de se vider avant que les ventricules ne se contractent.",
        "tag": "Physio Cardio"
    },
    {
        "q": "Qu'est-ce que la 'Précharge' et la 'Postcharge' ?",
        "type": "ouverte",
        "answer": "Précharge = Volume de sang qui étire le ventricule avant la contraction (fin de diastole). Postcharge = Résistance que le cœur doit vaincre pour éjecter le sang (principalement la pression artérielle).",
        "level": "Avancé",
        "explanation": "Une hypertension augmente la postcharge, ce qui fatigue le cœur (il doit pousser contre une porte lourde).",
        "tag": "Physio Cardio"
    },
    {
        "q": "Comment le transport de l'Oxygène dans le sang est-il affecté par l'effet Bohr ?",
        "options": [
            "L'O2 se fixe mieux si le sang est acide",
            "L'acidité (liée au CO2 et à l'effort) diminue l'affinité de l'hémoglobine pour l'O2, ce qui facilite sa libération vers les muscles qui en ont besoin",
            "L'effet Bohr concerne le transport du sucre",
            "Il empêche l'O2 de quitter le sang"
        ],
        "answer": "L'acidité (liée au CO2 et à l'effort) diminue l'affinité de l'hémoglobine pour l'O2, ce qui facilite sa libération vers les muscles qui en ont besoin",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un mécanisme génial : là où le muscle travaille, il produit de l'acide/CO2, ce qui force l'hémoglobine à 'lâcher' son oxygène localement.",
        "tag": "Physio Respi"
    },
    {
        "q": "Qu'est-ce que le 'Volume Résiduel' ?",
        "options": [
            "Le volume d'air inspiré normalement",
            "Le volume d'air qui reste dans les poumons même après une expiration forcée maximale (on ne peut pas vider totalement ses poumons)",
            "L'air dans l'estomac",
            "Le volume mort"
        ],
        "answer": "Le volume d'air qui reste dans les poumons même après une expiration forcée maximale (on ne peut pas vider totalement ses poumons)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Il permet aux alvéoles de ne pas se coller entre elles et assure une continuité des échanges gazeux même pendant l'expiration.",
        "tag": "Physio Respi"
    },
    {
        "q": "Quelle est la conséquence d'une fibrillation auriculaire sur le débit cardiaque ?",
        "type": "ouverte",
        "answer": "Les oreillettes ne se contractent plus efficacement (elles trémulent), on perd le 'remplissage actif' (environ 20% du volume). Le débit cardiaque baisse, et il y a un risque de formation de caillots (thrombose) dans l'oreillette.",
        "level": "Avancé",
        "explanation": "C'est l'arythmie la plus fréquente chez la personne âgée.",
        "tag": "Pathologie Cardio"
    },
    {
        "q": "Pourquoi la paroi du Ventricule Gauche est-elle beaucoup plus épaisse que celle du Ventricule Droit ?",
        "type": "ouverte",
        "answer": "Car le Ventricule Gauche doit propulser le sang dans tout le corps (Grande Circulation) à haute pression (120 mmHg). Le Droit ne pousse que vers les poumons tout proches à basse pression.",
        "level": "Avancé",
        "explanation": "Le muscle s'adapte à la charge (hypertrophie physiologique).",
        "tag": "Anatomie Cardio"
    },
    {
        "q": "Qu'est-ce que l'Espace Mort Anatomique ?",
        "options": [
            "Une zone du poumon nécrosée",
            "Le volume des voies aériennes de conduction (nez, trachée, bronches) où il n'y a PAS d'échanges gazeux",
            "L'espace entre les deux poumons",
            "Le volume résiduel"
        ],
        "answer": "Le volume des voies aériennes de conduction (nez, trachée, bronches) où il n'y a PAS d'échanges gazeux",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Sur 500ml inspirés, seuls 350ml arrivent aux alvéoles. Les 150ml restants remplissent juste les 'tuyaux' (espace mort).",
        "tag": "Physio Respi"
    },
    {
        "q": "Comment le pH sanguin est-il régulé par la respiration ?",
        "type": "ouverte",
        "answer": "Le CO2 est un acide volatil. En hyperventilant, on élimine beaucoup de CO2 -> le pH remonte (Alcalose). En hypoventilant, on garde le CO2 -> le pH baisse (Acidose).",
        "level": "Avancé",
        "explanation": "C'est le système tampon le plus rapide de l'organisme, avant l'intervention des reins.",
        "tag": "Physio Respi"
    },
    {
        "q": "Quel est le rôle principal de l'Insuline ?",
        "options": [
            "Augmenter le taux de sucre dans le sang",
            "Faire baisser le taux de sucre dans le sang (Hypoglycémiante) en le faisant entrer dans les cellules",
            "Digérer les graisses",
            "Augmenter la tension"
        ],
        "answer": "Faire baisser le taux de sucre dans le sang (Hypoglycémiante) en le faisant entrer dans les cellules",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la seule hormone hypoglycémiante de l'organisme. Le Glucagon fait l'inverse (Hyperglycémiant).",
        "tag": "Endocrinologie"
    },
    {
        "q": "Où se déroule la majeure partie de l'absorption des nutriments ?",
        "options": ["Dans l'estomac", "Dans l'Intestin Grêle", "Dans le Gros Intestin (Côlon)", "Dans l'œsophage"],
        "answer": "Dans l'Intestin Grêle",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Grâce aux villosités intestinales, la surface d'absorption est immense (taille d'un terrain de tennis). L'estomac ne fait que préparer la bouillie (chyme).",
        "tag": "Physio Digestive"
    },
    {
        "q": "Quel organe produit la bile ?",
        "options": ["La Vésicule Biliaire", "Le Foie", "Le Pancréas", "L'Estomac"],
        "answer": "Le Foie",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le foie FABRIQUE la bile. La vésicule biliaire ne fait que la STOCKER et la concentrer.",
        "tag": "Physio Digestive"
    },
    {
        "q": "Quelle est l'unité fonctionnelle du rein chargée de filtrer le sang ?",
        "options": ["Le Neurone", "Le Néphron", "L'Alvéole", "L'Hépatocyte"],
        "answer": "Le Néphron",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Chaque rein contient environ 1 million de néphrons. Ils filtrent le sang pour former l'urine.",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quelle glande située dans le cou régule le métabolisme de base (vitesse de fonctionnement du corps) ?",
        "options": ["L'Hypophyse", "La Thyroïde", "Les Surrénales", "Le Thymus"],
        "answer": "La Thyroïde",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elle produit les hormones T3 et T4. En hyperthyroïdie, tout s'accélère (maigreur, tachycardie). En hypo, tout ralentit (prise de poids, fatigue).",
        "tag": "Endocrinologie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que le Péristaltisme ?",
        "type": "ouverte",
        "answer": "C'est l'ensemble des contractions musculaires ondulatoires (comme une vague) du tube digestif qui font avancer le bol alimentaire de la bouche vers l'anus.",
        "level": "Intermédiaire",
        "explanation": "C'est un mouvement involontaire (muscles lisses). S'il s'arrête, c'est l'occlusion intestinale.",
        "tag": "Physio Digestive"
    },
    {
        "q": "En plus de filtrer les déchets, quelle fonction vitale assure le rein via l'érythropoïétine (EPO) ?",
        "options": [
            "La digestion des sucres",
            "La stimulation de la moelle osseuse pour fabriquer des globules rouges",
            "La régulation du sommeil",
            "La production de bile"
        ],
        "answer": "La stimulation de la moelle osseuse pour fabriquer des globules rouges",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "En cas d'insuffisance rénale, le patient devient anémique car il manque d'EPO.",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quel est le rôle du Pancréas Exocrine (par opposition à Endocrine) ?",
        "type": "ouverte",
        "answer": "Il sécrète le suc pancréatique (riche en enzymes : amylase, lipase, trypsine) et du bicarbonate dans le duodénum pour digérer les aliments et neutraliser l'acidité gastrique.",
        "level": "Intermédiaire",
        "explanation": "Le pancréas a une double casquette : digestion (exocrine) et régulation du sucre (endocrine).",
        "tag": "Physio Digestive"
    },
    {
        "q": "Qu'est-ce que le 'Seuil Rénal du Glucose' ?",
        "options": [
            "La quantité de sucre qu'on mange",
            "La concentration sanguine de glucose (environ 1.80 g/L) au-delà de laquelle le rein ne peut plus tout réabsorber, et le sucre apparaît dans les urines (glycosurie)",
            "La taille du rein",
            "Le taux d'insuline"
        ],
        "answer": "La concentration sanguine de glucose (environ 1.80 g/L) au-delà de laquelle le rein ne peut plus tout réabsorber, et le sucre apparaît dans les urines (glycosurie)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un signe historique du diabète ('urine au goût de miel'). Normalement, il n'y a JAMAIS de sucre dans les urines.",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quelle hormone est sécrétée en réponse au stress chronique (et non aigu) ?",
        "options": ["L'Adrénaline", "Le Cortisol", "La Mélatonine", "L'Ocytocine"],
        "answer": "Le Cortisol",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "L'adrénaline gère l'urgence immédiate. Le cortisol gère l'adaptation sur la durée (mais il est néfaste à long terme : baisse immunité, prise de poids).",
        "tag": "Endocrinologie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le mécanisme de la sécrétion d'acide chlorhydrique (HCl) dans l'estomac et son utilité.",
        "type": "ouverte",
        "answer": "Les cellules pariétales sécrètent des ions H+ (pompe à protons). Cela acidifie l'estomac (pH 1-2) pour tuer les bactéries, dénaturer les protéines et activer la pepsine (enzyme).",
        "level": "Avancé",
        "explanation": "L'estomac doit se protéger de son propre acide avec un mucus épais, sinon c'est l'ulcère.",
        "tag": "Physio Digestive"
    },
    {
        "q": "Qu'est-ce que la 'Clairance rénale' (Glomerular Filtration Rate) ?",
        "type": "ouverte",
        "answer": "C'est le volume de plasma totalement épuré d'une substance par les reins par unité de temps. C'est le meilleur indicateur de la fonction rénale (Normale > 90 ml/min).",
        "level": "Avancé",
        "explanation": "On utilise souvent la Créatinine pour la calculer. Si la clairance baisse, l'insuffisance rénale s'installe.",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quel est le rôle de l'Hormone Anti-Diurétique (ADH ou Vasopressine) ?",
        "options": [
            "Faire uriner beaucoup",
            "Augmenter la réabsorption d'eau par le rein pour concentrer les urines et remonter la pression artérielle",
            "Éliminer le sel",
            "Stimuler la soif uniquement"
        ],
        "answer": "Augmenter la réabsorption d'eau par le rein pour concentrer les urines et remonter la pression artérielle",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'alcool inhibe l'ADH, c'est pourquoi on urine beaucoup (et on se déshydrate) quand on boit de l'alcool.",
        "tag": "Endocrinologie"
    },
    {
        "q": "Dans la digestion des graisses, à quoi sert l'émulsion par les sels biliaires ?",
        "type": "ouverte",
        "answer": "Les sels biliaires agissent comme un détergent : ils fractionnent les grosses gouttes de lipides en fines gouttelettes (micelles), augmentant la surface d'attaque pour les enzymes (lipases).",
        "level": "Avancé",
        "explanation": "Sans bile, les graisses ne sont pas digérées et finissent dans les selles (stéatorrhée).",
        "tag": "Physio Digestive"
    },
    {
        "q": "Qu'est-ce que le Système Rénine-Angiotensine-Aldostérone (SRAA) ?",
        "type": "ouverte",
        "answer": "C'est une cascade hormonale déclenchée par le rein en cas de baisse de pression. Rénine -> Angiotensine (vasoconstriction) -> Aldostérone (rétention eau/sel). Résultat : la Tension Artérielle remonte.",
        "level": "Avancé",
        "explanation": "C'est la cible principale des médicaments contre l'hypertension (IEC, Sartans).",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quelle est la différence entre Diabète de Type 1 et de Type 2 ?",
        "options": [
            "Le Type 1 est moins grave",
            "Type 1 = Destruction auto-immune des cellules insulino-sécrétrices (défaut de production). Type 2 = Résistance des cellules à l'insuline (défaut d'action) souvent lié au surpoids",
            "Type 1 touche les vieux, Type 2 les jeunes",
            "C'est pareil"
        ],
        "answer": "Type 1 = Destruction auto-immune des cellules insulino-sécrétrices (défaut de production). Type 2 = Résistance des cellules à l'insuline (défaut d'action) souvent lié au surpoids",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le Type 1 nécessite de l'insuline à vie. Le Type 2 se traite d'abord par le régime et les antidiabétiques oraux.",
        "tag": "Endocrinologie"
    },
    {
        "q": "Le foie reçoit du sang par deux entrées. Lesquelles ?",
        "options": [
            "Deux artères hépatiques",
            "L'Artère Hépatique (sang oxygéné) et la Veine Porte (sang riche en nutriments venant de l'intestin)",
            "La Veine Cave et l'Aorte",
            "L'Artère Rénale et l'Artère Fémorale"
        ],
        "answer": "L'Artère Hépatique (sang oxygéné) et la Veine Porte (sang riche en nutriments venant de l'intestin)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La Veine Porte apporte tout ce qu'on a mangé directement au foie pour filtrage/stockage avant que cela n'aille dans le reste du corps. C'est unique.",
        "tag": "Anatomie Vasculaire"
    },
    {
        "q": "Qu'est-ce que l'Axe Hypothalamo-Hypophysaire ?",
        "type": "ouverte",
        "answer": "C'est le 'chef d'orchestre' endocrinien. L'hypothalamus commande l'hypophyse, qui commande à son tour les glandes périphériques (Thyroïde, Surrénales, Ovaires/Testicules).",
        "level": "Avancé",
        "explanation": "Cela fonctionne par rétrocontrôle (feedback). Si le taux d'hormone périphérique est suffisant, l'axe s'arrête de stimuler.",
        "tag": "Endocrinologie"
    },
    {
        "q": "En physiologie rénale, qu'est-ce que la réabsorption tubulaire ?",
        "type": "ouverte",
        "answer": "C'est le processus par lequel le rein récupère les substances utiles (eau, glucose, sodium) présentes dans l'urine primitive pour les remettre dans le sang.",
        "level": "Avancé",
        "explanation": "On filtre 180 Litres de sang par jour, mais on n'urine que 1.5 Litre. 99% est réabsorbé ! Sans ça, on se viderait de notre eau en quelques minutes.",
        "tag": "Physio Rénale"
    },
    {
        "q": "Quel est le rôle du microbiote intestinal (flore) ?",
        "type": "ouverte",
        "answer": "Il aide à la digestion des fibres, produit des vitamines (K, B12), protège contre les pathogènes et interagit avec le système immunitaire et le cerveau (axe intestin-cerveau).",
        "level": "Avancé",
        "explanation": "On le considère aujourd'hui comme un organe à part entière (1 à 2 kg de bactéries).",
        "tag": "Physio Digestive"
    },
    {
        "q": "Quel est le centre de commande principal de la température corporelle (le thermostat du corps) ?",
        "options": ["Le Cervelet", "L'Hypothalamus", "Le Tronc Cérébral", "La Peau"],
        "answer": "L'Hypothalamus",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il compare en permanence la température du sang à la valeur de consigne (37°C) et déclenche les réactions de chauffage (frisson) ou de refroidissement (sueur).",
        "tag": "Thermorégulation"
    },
    {
        "q": "Quelle hormone, sécrétée par la glande pinéale à l'obscurité, favorise l'endormissement ?",
        "options": ["L'Adrénaline", "La Mélatonine", "Le Cortisol", "L'Insuline"],
        "answer": "La Mélatonine",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'hormone du rythme circadien. La lumière bleue (écrans) bloque sa sécrétion et retarde le sommeil.",
        "tag": "Physio Sommeil"
    },
    {
        "q": "Qu'est-ce que l'Intéroception ?",
        "options": [
            "La perception du monde extérieur",
            "La perception des signaux venant de l'intérieur du corps (battements de cœur, faim, douleur viscérale...)",
            "La capacité à intercepter un ballon",
            "L'équilibre"
        ],
        "answer": "La perception des signaux venant de l'intérieur du corps (battements de cœur, faim, douleur viscérale...)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le 'sens de l'état physiologique'. Une mauvaise intéroception est souvent liée à des troubles de la régulation émotionnelle (anxiété).",
        "tag": "Psychomotricité"
    },
    {
        "q": "Combien de temps dure environ un cycle de sommeil complet chez l'adulte ?",
        "options": ["10 minutes", "30 minutes", "90 minutes (1h30)", "4 heures"],
        "answer": "90 minutes (1h30)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Une nuit se compose de 4 à 6 cycles successifs.",
        "tag": "Physio Sommeil"
    },
    {
        "q": "Quel est le moyen le plus efficace pour le corps de perdre de la chaleur lors d'un effort intense ?",
        "options": ["La respiration", "L'évaporation de la sueur", "L'urine", "Le rayonnement"],
        "answer": "L'évaporation de la sueur",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'évaporation consomme beaucoup d'énergie thermique. Si l'air est trop humide (sauna/climat tropical), la sueur ruisselle sans s'évaporer et ne refroidit pas -> Risque de coup de chaleur.",
        "tag": "Thermorégulation"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que le Sommeil Paradoxal (REM Sleep) ?",
        "type": "ouverte",
        "answer": "C'est la phase du sommeil où l'activité cérébrale est intense (proche de l'éveil, rêves), mais où le tonus musculaire est totalement aboli (atonie), avec des mouvements oculaires rapides.",
        "level": "Intermédiaire",
        "explanation": "On l'appelle paradoxal car le cerveau est réveillé mais le corps est paralysé (pour ne pas acter ses rêves).",
        "tag": "Physio Sommeil"
    },
    {
        "q": "Pourquoi frissonne-t-on quand on a de la fièvre ?",
        "type": "ouverte",
        "answer": "L'hypothalamus a monté le thermostat (ex: à 39°C pour tuer le virus). Comme le corps est encore à 37°C, il se croit en hypothermie et déclenche le frisson pour produire de la chaleur et atteindre la nouvelle consigne.",
        "level": "Intermédiaire",
        "explanation": "Le frisson est une contraction musculaire involontaire et rapide qui génère de la chaleur.",
        "tag": "Thermorégulation"
    },
    {
        "q": "Quel est le lien physiologique entre Stress et Digestion ?",
        "options": [
            "Le stress améliore la digestion",
            "Le système Sympathique (Stress) inhibe le système digestif (vasoconstriction, arrêt péristaltisme) pour détourner le sang vers les muscles",
            "Aucun lien",
            "Le stress fait grossir l'estomac"
        ],
        "answer": "Le système Sympathique (Stress) inhibe le système digestif (vasoconstriction, arrêt péristaltisme) pour détourner le sang vers les muscles",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est pourquoi un stress chronique peut entraîner des troubles digestifs fonctionnels (douleurs, ballonnements).",
        "tag": "Physio Intégrative"
    },
    {
        "q": "Qu'est-ce qu'un Rythme Circadien ?",
        "options": [
            "Un rythme d'environ un mois (menstruel)",
            "Un rythme biologique d'environ 24 heures (veille/sommeil, température, cortisol)",
            "Un rythme cardiaque rapide",
            "Un rythme respiratoire"
        ],
        "answer": "Un rythme biologique d'environ 24 heures (veille/sommeil, température, cortisol)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Il est synchronisé par la lumière du jour via le noyau suprachiasmatique.",
        "tag": "Chronobiologie"
    },
    {
        "q": "En physiologie musculaire, qu'est-ce que le 'Tonus de fond' ?",
        "type": "ouverte",
        "answer": "C'est l'état de légère tension permanente des muscles au repos, d'origine réflexe, qui s'oppose à la gravité et prépare le mouvement.",
        "level": "Intermédiaire",
        "explanation": "C'est la toile de fond de l'activité motrice et émotionnelle (Henri Wallon).",
        "tag": "Psychomotricité"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Quelle est la différence physiologique entre 'Ficv' et 'Coup de Chaleur' (Hyperthermie maligne) ?",
        "type": "ouverte",
        "answer": "Fièvre : L'hypothalamus décide de monter la température (consigne élevée). Coup de chaleur : L'hypothalamus veut refroidir (consigne normale) mais les systèmes de régulation sont dépassés par la chaleur extérieure (le corps chauffe malgré lui).",
        "level": "Avancé",
        "explanation": "L'aspirine baisse la fièvre (agit sur l'hypothalamus) mais ne sert à rien sur un coup de chaleur (il faut refroidir physiquement le patient).",
        "tag": "Thermorégulation"
    },
    {
        "q": "Quel est le rôle du Sommeil Lent Profond (Stade N3) ?",
        "options": [
            "Rêver",
            "La récupération physique, la sécrétion d'hormone de croissance et le nettoyage des déchets cérébraux (système glymphatique)",
            "L'apprentissage moteur",
            "La vigilance"
        ],
        "answer": "La récupération physique, la sécrétion d'hormone de croissance et le nettoyage des déchets cérébraux (système glymphatique)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le sommeil réparateur. Il survient surtout en début de nuit. S'il manque, on se sent épuisé physiquement.",
        "tag": "Physio Sommeil"
    },
    {
        "q": "Expliquez le lien entre Emotion et Tonus Musculaire (Dialogue Tonique).",
        "type": "ouverte",
        "answer": "Les circuits de l'émotion (Limbique) sont directement connectés à la formation réticulée qui régule le tonus (voies réticulo-spinales). Une émotion (peur/colère) se traduit immédiatement par une hypertonie (tension) ou une hypotonie (sidération).",
        "level": "Avancé",
        "explanation": "Le corps ne ment pas. Le psychomotricien lit l'état émotionnel du patient à travers ses variations toniques.",
        "tag": "Psychomotricité"
    },
    {
        "q": "Qu'est-ce que la 'Plasticité Cérébrale' (Neuroplasticité) ?",
        "type": "ouverte",
        "answer": "C'est la capacité du cerveau à remodeler ses connexions (synapses) en fonction de l'expérience et de l'apprentissage tout au long de la vie.",
        "level": "Avancé",
        "explanation": "C'est le fondement de la rééducation. Rien n'est figé. Un entraînement répété renforce les connexions (Loi de Hebb : 'Neurons that fire together, wire together').",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Comment le corps s'adapte-t-il physiologiquement à l'altitude (Hypoxie) à court et long terme ?",
        "options": [
            "Il ne s'adapte pas",
            "Court terme : Hyperventilation + Tachycardie. Long terme : Production d'EPO -> Augmentation des globules rouges (Polyglobulie)",
            "Il baisse sa température",
            "Il arrête de respirer"
        ],
        "answer": "Court terme : Hyperventilation + Tachycardie. Long terme : Production d'EPO -> Augmentation des globules rouges (Polyglobulie)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est pourquoi les athlètes s'entraînent en altitude : pour booster leur transport d'oxygène naturellement.",
        "tag": "Physio Adaptation"
    },
    {
        "q": "Qu'est-ce que le 'Mécanisme du Gate Control' dans la modulation de la douleur ?",
        "type": "ouverte",
        "answer": "C'est l'inhibition de la douleur au niveau de la moelle épinière par la stimulation des fibres tactiles (frotter là où on a mal). Les fibres du toucher (rapides) 'ferment la porte' aux fibres de la douleur (lentes).",
        "level": "Avancé",
        "explanation": "C'est le principe de l'effet antalgique du massage ou du TENS (neurostimulation électrique).",
        "tag": "Neurophysiologie"
    },
    {
        "q": "Quelle est la conséquence d'une lésion de la Formation Réticulée Activatrice Ascendante (FRAA) dans le tronc cérébral ?",
        "options": [
            "Une insomnie",
            "Un coma (perte de l'éveil)",
            "Une paralysie",
            "Une cécité"
        ],
        "answer": "Un coma (perte de l'éveil)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La FRAA est la 'pile électrique' qui maintient le cortex éveillé. Sans elle, le cerveau s'éteint.",
        "tag": "Neurophysiologie"
    },
    {
        "q": "En psychophysiologie, qu'est-ce que l'Axe Corticotrope (HPA) ?",
        "options": [
            "L'axe de la marche",
            "L'axe Hypothalamus-Hypophyse-Surrénales qui gère la réponse au stress par la sécrétion de Cortisol",
            "L'axe de la vision",
            "L'axe digestif"
        ],
        "answer": "L'axe Hypothalamus-Hypophyse-Surrénales qui gère la réponse au stress par la sécrétion de Cortisol",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Une hyperactivation chronique de cet axe (stress permanent, dépression) est toxique pour les neurones (notamment l'hippocampe/mémoire).",
        "tag": "Physio Intégrative"
    },
    {
        "q": "Pourquoi le nourrisson a-t-il une thermorégulation immature ?",
        "type": "ouverte",
        "answer": "Il a une grande surface corporelle par rapport à son poids (perte de chaleur), peu de graisse isolante, et ne sait pas frissonner efficacement. Il produit de la chaleur grâce à la 'Graisse Brune'.",
        "level": "Avancé",
        "explanation": "C'est pourquoi il faut particulièrement le couvrir (bonnet) et surveiller sa température.",
        "tag": "Pédiatrie / Physio"
    },
    {
        "q": "Qu'est-ce que la Proprioception Inconsciente et où est-elle traitée ?",
        "options": [
            "Dans le cortex pariétal",
            "Dans le Cervelet (via les voies spino-cérébelleuses)",
            "Dans les yeux",
            "Dans la peau"
        ],
        "answer": "Dans le Cervelet (via les voies spino-cérébelleuses)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle permet l'ajustement automatique de la posture et du tonus sans qu'on ait besoin d'y penser, contrairement à la proprioception consciente (Schéma corporel).",
        "tag": "Neurophysiologie"
    },
    ],

    "MODULE 4: Psychologie": [
        # GÉNÉRALITÉS & DÉVELOPPEMENT
        {
        "q": "Selon votre cours, quelle est la définition exacte de l'Affect ?",
        "options": [
            "Une réaction physiologique brutale",
            "Un état émotionnel immédiat, ressenti dans le corps et la psyché, avec une tonalité (plaisir, colère, joie)",
            "Un sentiment durable comme l'amour",
            "Une maladie mentale"
        ],
        "answer": "Un état émotionnel immédiat, ressenti dans le corps et la psyché, avec une tonalité (plaisir, colère, joie)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'affect est l'énergie de la pulsion qui se manifeste. Il se distingue du sentiment qui est plus construit et durable.",
        "tag": "Psychoaffectif"
    },
    {
        "q": "Qu'est-ce que l'Attachement selon la définition de votre cours ?",
        "options": [
            "Le fait d'aimer ses jouets",
            "Un lien affectif durable et sécurisant entre l'enfant et ses figures de soin",
            "La dépendance pathologique à la mère",
            "Le fait de ne pas vouloir grandir"
        ],
        "answer": "Un lien affectif durable et sécurisant entre l'enfant et ses figures de soin",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un besoin primaire (Bowlby). L'enfant a besoin de cette base de sécurité pour ensuite explorer le monde.",
        "tag": "Attachement"
    },
    {
        "q": "Dans le développement, qu'est-ce que la 'Différenciation' ?",
        "options": [
            "Apprendre les couleurs",
            "Le processus par lequel l'enfant découvre qu'il n'est pas sa mère, qu'il se sépare et a ses propres désirs",
            "Le rejet des parents",
            "La capacité à marcher"
        ],
        "answer": "Le processus par lequel l'enfant découvre qu'il n'est pas sa mère, qu'il se sépare et a ses propres désirs",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Au début de la vie, le bébé est dans une 'symbiose' ou indifférenciation avec la mère. Se différencier est l'étape clé vers l'autonomie.",
        "tag": "Développement"
    },
    {
        "q": "Qu'est-ce que la Communication Non-Verbale (CNV) ?",
        "options": [
            "L'utilisation de la langue des signes",
            "Tout ce qui véhicule du sens sans passer par les mots (gestes, regard, posture, toucher, distance)",
            "L'écriture",
            "Le silence absolu"
        ],
        "answer": "Tout ce qui véhicule du sens sans passer par les mots (gestes, regard, posture, toucher, distance)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La CNV représente la majeure partie du message dans une interaction, bien plus que les mots eux-mêmes.",
        "tag": "CNV"
    },
    {
        "q": "Selon Guéguen (2001), quel est l'effet du 'Toucher' dans les interactions sociales ?",
        "options": [
            "Il est toujours perçu comme une agression",
            "C'est une 'source d'influence' puissante qui favorise la persuasion et l'acceptation des requêtes",
            "Il n'a aucun effet",
            "Il ne sert qu'à soigner"
        ],
        "answer": "C'est une 'source d'influence' puissante qui favorise la persuasion et l'acceptation des requêtes",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Toucher légèrement le bras de quelqu'un en lui demandant quelque chose augmente statistiquement les chances qu'il dise oui.",
        "tag": "Psychologie Sociale"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle différence votre cours fait-il entre 'Émotion' et 'Sentiment' ?",
        "type": "ouverte",
        "answer": "L'Émotion est une réaction physiologique et comportementale brève à un événement. Le Sentiment est une émotion devenue durable, intégrée à la conscience et stable dans le temps (ex: amour, jalousie).",
        "level": "Intermédiaire",
        "explanation": "L'émotion est un 'orage' (court, intense), le sentiment est un 'climat' (long, stable).",
        "tag": "Définitions"
    },
    {
        "q": "Qu'est-ce que la 'Relation d'Objet' en psychanalyse ?",
        "type": "ouverte",
        "answer": "C'est la manière dont le sujet se relie à l'autre. 'L'objet' désigne ici la personne (ou la partie de la personne) qui est investie affectivement par le sujet.",
        "level": "Intermédiaire",
        "explanation": "On parle de relation d'objet 'anaclitique' (dépendance) ou 'génitale' (adulte). C'est la structure de nos liens affectifs.",
        "tag": "Psychanalyse"
    },
    {
        "q": "En CNV, qu'est-ce que la 'Proxémie' (Edward T. Hall) ?",
        "options": [
            "L'étude des mimiques du visage",
            "L'étude de la gestion de l'espace et des distances entre les individus (Intime, Personnelle, Sociale, Publique)",
            "L'étude du toucher",
            "L'étude de la voix"
        ],
        "answer": "L'étude de la gestion de l'espace et des distances entre les individus (Intime, Personnelle, Sociale, Publique)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "En psychomotricité, savoir gérer sa distance avec le patient (ne pas être trop intrusif ni trop distant) est une compétence proxémique fondamentale.",
        "tag": "CNV"
    },
    {
        "q": "Qu'est-ce que la 'Symbolisation' dans le développement de l'enfant ?",
        "type": "ouverte",
        "answer": "C'est la capacité de l'enfant à se représenter mentalement un objet absent et à mettre des mots, des gestes ou des dessins sur ses expériences, permettant de différer la satisfaction.",
        "level": "Intermédiaire",
        "explanation": "Le langage est la forme suprême de symbolisation. Avant cela, l'enfant symbolise par le jeu (faire semblant).",
        "tag": "Développement"
    },
    {
        "q": "Selon Freud, quelle est la première zone érogène investie par l'enfant (Stade Oral) ?",
        "options": ["L'anus", "La bouche et la zone bucco-labiale", "Les organes génitaux", "La peau"],
        "answer": "La bouche et la zone bucco-labiale",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le plaisir est lié à la succion (tétée) et à l'incorporation. C'est le stade de la découverte du monde par la bouche.",
        "tag": "Psychanalyse"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le concept de 'Soi' (Self) selon votre cours.",
        "type": "ouverte",
        "answer": "C'est le sentiment d'être unifié, d'exister de manière cohérente et continue dans le temps (continuité d'existence).",
        "level": "Avancé",
        "explanation": "Pour Winnicott, le 'Vrai Self' se construit grâce à une mère suffisamment bonne. Si l'environnement est défaillant, l'enfant développe un 'Faux Self' pour s'adapter.",
        "tag": "Concepts Clés"
    },
    {
        "q": "Quels sont les facteurs qui nuancent l'efficacité et l'acceptabilité du toucher dans le soin ?",
        "options": [
            "Il n'y a aucun facteur limitant",
            "Les facteurs Sociaux (statut, hiérarchie), Culturels (codes, rapport à l'étranger) et Éducatifs (histoire personnelle)",
            "La température de la pièce",
            "La taille des mains"
        ],
        "answer": "Les facteurs Sociaux (statut, hiérarchie), Culturels (codes, rapport à l'étranger) et Éducatifs (histoire personnelle)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le toucher n'est pas universel. Dans certaines cultures, toucher la tête est tabou. Le psychomotricien doit lire ces codes.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce que l'Objet Transitionnel (Winnicott) et quelle est sa fonction ?",
        "type": "ouverte",
        "answer": "C'est la première possession 'non-moi' de l'enfant (doudou). Il sert de défense contre l'angoisse de séparation et permet de faire la transition entre la fusion maternelle et la réalité extérieure.",
        "level": "Avancé",
        "explanation": "Il se situe dans l'aire transitionnelle (aire de jeu). Il ne doit être ni changé ni lavé par l'adulte car il porte l'odeur et l'histoire de l'enfant.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Quelle est la différence entre l'Assimilation et l'Accommodation chez Jean Piaget ?",
        "type": "ouverte",
        "answer": "Assimilation : J'intègre le monde à mes schèmes existants (ex: je secoue tout ce que j'attrape). Accommodation : Je modifie mes schèmes pour m'adapter à la réalité (ex: je dois pincer délicatement pour attraper une miette).",
        "level": "Avancé",
        "explanation": "L'intelligence naît de l'équilibre entre ces deux processus (Équilibration Majorante).",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "Qu'est-ce que le 'Dialogue Tonique' selon Henri Wallon ?",
        "options": [
            "Parler fort",
            "La communication primitive entre la mère et le bébé qui passe par les variations du tonus musculaire (tensions/détentes) bien avant le langage verbal",
            "Faire de la gymnastique ensemble",
            "Le cri du bébé"
        ],
        "answer": "La communication primitive entre la mère et le bébé qui passe par les variations du tonus musculaire (tensions/détentes) bien avant le langage verbal",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le concept central en psychomotricité. L'émotion est indissociable du tonus. Le bébé 'parle' avec son corps.",
        "tag": "Psychomotricité"
    },
    {
        "q": "En Éthologie, qu'est-ce que l'Empreinte (Imprinting) décrite par Konrad Lorenz ?",
        "options": [
            "Une trace de pas",
            "Un apprentissage irréversible se produisant pendant une période sensible critique, où le jeune animal s'attache à la première figure en mouvement qu'il voit (souvent la mère)",
            "La mémoire génétique",
            "L'instinct de chasse"
        ],
        "answer": "Un apprentissage irréversible se produisant pendant une période sensible critique, où le jeune animal s'attache à la première figure en mouvement qu'il voit (souvent la mère)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Lorenz l'a démontré avec des oies qui le suivaient partout car il était le premier être vivant qu'elles avaient vu à l'éclosion.",
        "tag": "Éthologie"
    },
    {
        "q": "Qu'est-ce que le Stade du Miroir (Lacan/Wallon) et quel âge survient-il environ ?",
        "type": "ouverte",
        "answer": "Entre 6 et 18 mois. L'enfant reconnaît son image dans le miroir et jubile. Cela marque la construction de l'identité et l'unification du corps (fin du corps morcelé).",
        "level": "Avancé",
        "explanation": "Avant ce stade, l'enfant ne sait pas que le reflet est lui-même. C'est une étape fondatrice de la conscience de soi.",
        "tag": "Psycho du Développement"
    },
    {
        "q": "Quelles sont les trois instances de la 2ème Topique de Freud ?",
        "options": [
            "Conscient, Préconscient, Inconscient",
            "Ça (Pulsions), Moi (Médiateur), Surmoi (Interdits/Loi)",
            "Oral, Anal, Phallique",
            "Cerveau, Cœur, Ventre"
        ],
        "answer": "Ça (Pulsions), Moi (Médiateur), Surmoi (Interdits/Loi)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le Moi doit jongler entre les exigences pulsionnelles du Ça et les interdits moraux du Surmoi. La 1ère topique était Conscient/Préconscient/Inconscient.",
        "tag": "Psychanalyse"
    },
    {
        "q": "En psychologie sociale, qu'est-ce que l'Effet de Halo ?",
        "type": "ouverte",
        "answer": "C'est un biais cognitif où la perception d'une caractéristique positive (ex: beauté physique) influence positivement l'évaluation des autres caractéristiques (ex: intelligence, gentillesse) sans preuve.",
        "level": "Avancé",
        "explanation": "Le soignant doit s'en méfier pour ne pas juger un patient sur son apparence ou sa première impression.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Quel est le lien entre 'Posture' et 'État émotionnel' mis en avant par la CNV ?",
        "options": [
            "Il n'y en a pas",
            "La posture est le reflet direct de l'état émotionnel (ex: épaules voûtées = tristesse/repli), et modifier sa posture peut rétroactivement influencer l'émotion (Feedback facial/postural)",
            "La posture dépend uniquement de la colonne vertébrale",
            "Les émotions sont invisibles"
        ],
        "answer": "La posture est le reflet direct de l'état émotionnel (ex: épaules voûtées = tristesse/repli), et modifier sa posture peut rétroactivement influencer l'émotion (Feedback facial/postural)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un outil thérapeutique : redresser un patient déprimé peut l'aider à se sentir mieux psychiquement.",
        "tag": "CNV"
    },
    {
        "q": "Quel est l'ordre chronologique des stades du développement libidinal selon Freud ?",
        "options": [
            "Anal -> Oral -> Phallique -> Latence -> Génital",
            "Oral -> Anal -> Phallique -> Latence -> Génital",
            "Oral -> Phallique -> Anal -> Génital -> Latence",
            "Phallique -> Oral -> Anal -> Génital"
        ],
        "answer": "Oral -> Anal -> Phallique -> Latence -> Génital",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la progression classique : Bouche (0-1 an), Sphincters (1-3 ans), Sexe/Castration (3-6 ans), Calme (6-12 ans), Puberté (12+).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Selon Jean Piaget, quel est le premier stade de l'intelligence (de 0 à 2 ans) ?",
        "options": [
            "Le stade des opérations formelles",
            "Le stade sensori-moteur",
            "Le stade pré-opératoire",
            "Le stade du miroir"
        ],
        "answer": "Le stade sensori-moteur",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'enfant comprend le monde uniquement par ses sens et ses mouvements (manipulation). Il n'a pas encore de pensée symbolique ou de langage construit.",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "Qu'est-ce que la 'Permanence de l'Objet' (acquisition majeure vers 8-12 mois) ?",
        "options": [
            "Savoir qu'un objet continue d'exister même quand on ne le voit plus",
            "Savoir attraper un objet",
            "Savoir nommer un objet",
            "Savoir qu'un objet est solide"
        ],
        "answer": "Savoir qu'un objet continue d'exister même quand on ne le voit plus",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Avant cette acquisition, pour le bébé, 'loin des yeux = loin du cœur' (l'objet n'existe plus). Après, il va chercher le doudou caché sous la couverture.",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "Quelle est la caractéristique principale du Stade Anal (Freud) ?",
        "options": [
            "Le plaisir de manger",
            "L'apprentissage de la propreté et la maîtrise des sphincters (rétention/expulsion)",
            "La découverte de la différence des sexes",
            "L'entrée à l'école"
        ],
        "answer": "L'apprentissage de la propreté et la maîtrise des sphincters (rétention/expulsion)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'âge du 'Non', de l'opposition et du contrôle. L'enfant découvre son pouvoir sur l'adulte (je donne mon caca ou je le garde).",
        "tag": "Psychanalyse"
    },
    {
        "q": "En psychologie cognitive, qu'est-ce que la Mémoire à Court Terme (MCT) ?",
        "options": [
            "La mémoire des souvenirs d'enfance",
            "La mémoire de travail qui permet de retenir une information quelques secondes (ex: un numéro de téléphone) pour l'utiliser immédiatement",
            "La mémoire des savoir-faire (vélo)",
            "La mémoire du futur"
        ],
        "answer": "La mémoire de travail qui permet de retenir une information quelques secondes (ex: un numéro de téléphone) pour l'utiliser immédiatement",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Sa capacité est limitée (environ 7 éléments, le fameux 'nombre magique de Miller').",
        "tag": "Cognition"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que le Complexe d'Œdipe et à quel stade survient-il ?",
        "type": "ouverte",
        "answer": "Il survient au Stade Phallique (3-6 ans). L'enfant éprouve des désirs amoureux pour le parent du sexe opposé et une rivalité hostile envers le parent du même sexe.",
        "level": "Intermédiaire",
        "explanation": "Sa résolution (renoncer à posséder maman/papa) permet l'identification au parent du même sexe et l'intégration des interdits (Surmoi).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Quelle est la différence entre Mémoire Épisodique et Mémoire Sémantique ?",
        "type": "ouverte",
        "answer": "Mémoire Épisodique : souvenirs personnels autobiographiques, situés dans le temps et l'espace (ex: mon mariage). Mémoire Sémantique : connaissances générales sur le monde, sans contexte (ex: Paris est la capitale de la France).",
        "level": "Intermédiaire",
        "explanation": "Dans la maladie d'Alzheimer, la mémoire épisodique est touchée en premier, alors que la sémantique résiste plus longtemps.",
        "tag": "Cognition"
    },
    {
        "q": "Qu'est-ce que l'Égocentrisme enfantin selon Piaget (Stade Pré-opératoire) ?",
        "options": [
            "L'enfant est égoïste et méchant",
            "L'incapacité de l'enfant à se décentrer et à adopter le point de vue de l'autre (il croit que tout le monde voit/pense comme lui)",
            "L'enfant veut toujours être le chef",
            "L'enfant ne s'aime pas"
        ],
        "answer": "L'incapacité de l'enfant à se décentrer et à adopter le point de vue de l'autre (il croit que tout le monde voit/pense comme lui)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Exemple : Si on lui demande ce que voit la poupée en face de lui, il décrit ce que LUI voit. Ce n'est pas un défaut moral, mais une limite cognitive.",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "En quoi consiste la 'Période de Latence' (6-12 ans) ?",
        "options": [
            "L'enfant dort beaucoup",
            "C'est une pause dans le développement pulsionnel sexuel, permettant à l'énergie de se sublimer vers les apprentissages scolaires et sociaux",
            "C'est la crise d'adolescence",
            "C'est le début de la marche"
        ],
        "answer": "C'est une pause dans le développement pulsionnel sexuel, permettant à l'énergie de se sublimer vers les apprentissages scolaires et sociaux",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le 'refoulement' est massif. L'enfant devient pudique et sage (l'âge de raison).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que l'Attention Sélective ?",
        "type": "ouverte",
        "answer": "C'est la capacité à focaliser son attention sur une information pertinente tout en inhibant les distracteurs (bruit, mouvement autour).",
        "level": "Intermédiaire",
        "explanation": "C'est l'effet 'Cocktail Party' : être capable d'écouter une seule conversation dans une pièce bruyante. Déficitaire dans le TDAH.",
        "tag": "Cognition"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez l'angoisse de Castration chez le garçon et son équivalent (ou différence) chez la fille selon Freud.",
        "type": "ouverte",
        "answer": "Garçon : Peur de perdre son pénis (puni par le père rival). Fille : Constate qu'elle n'en a pas (envie du pénis) et se sent 'déjà châtrée' ou lésée, se tournant vers le père pour obtenir un enfant (substitut).",
        "level": "Avancé",
        "explanation": "C'est le moteur de la sortie du complexe d'Œdipe. L'angoisse de castration pousse le garçon à renoncer à la mère pour sauver son intégrité.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que la Mémoire Procédurale ?",
        "options": [
            "La mémoire des procédures administratives",
            "La mémoire implicite des habiletés motrices et des savoir-faire automatisés (ex: faire du vélo, conduire, écrire)",
            "La mémoire des visages",
            "La mémoire immédiate"
        ],
        "answer": "La mémoire implicite des habiletés motrices et des savoir-faire automatisés (ex: faire du vélo, conduire, écrire)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle est très robuste et inconsciente ('le corps se souvient'). Elle est essentielle en rééducation psychomotrice.",
        "tag": "Cognition"
    },
    {
        "q": "Dans la théorie de Piaget, qu'est-ce que la 'Conservation' (acquise au stade des opérations concrètes vers 7 ans) ?",
        "type": "ouverte",
        "answer": "Comprendre qu'une quantité (liquide, poids, volume) reste la même malgré les transformations de son apparence (ex: transvaser de l'eau dans un verre plus fin ne change pas la quantité).",
        "level": "Avancé",
        "explanation": "Avant 7 ans, l'enfant dira qu'il y a 'plus' d'eau dans le verre fin car le niveau est plus haut (il se fie à l'aspect perceptif et non à la logique).",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "Qu'est-ce que le 'Stade du Personnalisme' (3 ans) décrit par Henri Wallon ?",
        "options": [
            "L'enfant devient gentil",
            "L'enfant affirme son 'Moi' par l'opposition systématique (crise du non), le narcissisme et la séduction, pour se distinguer d'autrui",
            "L'enfant apprend à lire",
            "L'enfant imite les animaux"
        ],
        "answer": "L'enfant affirme son 'Moi' par l'opposition systématique (crise du non), le narcissisme et la séduction, pour se distinguer d'autrui",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Wallon insiste sur la construction de la personnalité. Dire 'Non', c'est dire 'Je'.",
        "tag": "Psycho du Développement"
    },
    {
        "q": "Quelle est la différence entre Fonctions Exécutives 'Froides' et 'Chaudes' ?",
        "type": "ouverte",
        "answer": "Froides : Processus purement cognitifs (planification, inhibition, mémoire de travail) sans contexte émotionnel. Chaudes : Processus de décision impliquant des émotions, des récompenses ou des risques (motivation, gratification).",
        "level": "Avancé",
        "explanation": "Un enfant peut être bon en fonctions froides (tests QI) mais échouer en fonctions chaudes (impulsivité dans la vie réelle).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Selon Freud, quel mécanisme de défense caractérise principalement le Stade Anal ?",
        "options": [
            "Le Refoulement",
            "L'Isolation et la Formation Réactionnelle (le souci de propreté excessif pour masquer le désir de saleté)",
            "La Projection",
            "Le Déni"
        ],
        "answer": "L'Isolation et la Formation Réactionnelle (le souci de propreté excessif pour masquer le désir de saleté)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La formation réactionnelle transforme une pulsion inacceptable en son contraire (ex: une maniaquerie de l'ordre pour lutter contre un désir de désordre).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que l'Animisme dans la pensée enfantine (Piaget) ?",
        "options": [
            "Aimer les animaux",
            "La tendance à attribuer une vie, une conscience et des intentions aux objets inanimés (ex: 'le soleil est méchant', 'la table m'a tapé')",
            "La peur des fantômes",
            "Une religion"
        ],
        "answer": "La tendance à attribuer une vie, une conscience et des intentions aux objets inanimés (ex: 'le soleil est méchant', 'la table m'a tapé')",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une forme de pensée magique typique du stade pré-opératoire (avant 7 ans).",
        "tag": "Psychologie Cognitive"
    },
    {
        "q": "Qu'est-ce que l'Attention Divisée ?",
        "type": "ouverte",
        "answer": "C'est la capacité à traiter simultanément deux tâches ou plus (Double Tâche). Cela nécessite un partage des ressources attentionnelles.",
        "level": "Avancé",
        "explanation": "Exemple : Conduire et parler au passager. Si l'une des tâches n'est pas automatisée, la performance chute dans les deux.",
        "tag": "Cognition"
    },
    {
        "q": "En psychologie du développement, qu'est-ce que l'Étayage (Scaffolding) selon Bruner ?",
        "options": [
            "Mettre des béquilles",
            "L'ensemble des interactions d'assistance de l'adulte qui permettent à l'enfant de réaliser une tâche qu'il ne pourrait pas faire seul (soutien temporaire)",
            "L'interdiction de faire",
            "La punition"
        ],
        "answer": "L'ensemble des interactions d'assistance de l'adulte qui permettent à l'enfant de réaliser une tâche qu'il ne pourrait pas faire seul (soutien temporaire)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'application concrète de la Zone Prochaine de Développement de Vygotski. L'adulte prête sa conscience et ses compétences.",
        "tag": "Pédagogie / Psycho"
    },
    {
        "q": "Quel est le rôle de l'Hippocampe dans la mémoire ?",
        "type": "ouverte",
        "answer": "Il est indispensable à l'encodage et à la consolidation des nouveaux souvenirs épisodiques (passage de la mémoire court terme à long terme).",
        "level": "Avancé",
        "explanation": "Une lésion bilatérale de l'hippocampe (cas H.M.) entraîne une amnésie antérograde totale (incapacité de former de nouveaux souvenirs), comme dans le film Memento.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce que la 'Régression' comme mécanisme de défense ?",
        "options": [
            "Oublier ses leçons",
            "Le retour à des modes de comportement ou de satisfaction d'un stade antérieur (ex: refaire pipi au lit à la naissance d'un petit frère) pour se rassurer",
            "Devenir agressif",
            "Arrêter de grandir"
        ],
        "answer": "Le retour à des modes de comportement ou de satisfaction d'un stade antérieur (ex: refaire pipi au lit à la naissance d'un petit frère) pour se rassurer",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un mécanisme très fréquent et normal chez l'enfant en situation de stress ou de changement.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Quels sont les trois symptômes cardinaux du TDAH (Trouble du Déficit de l'Attention avec/sans Hyperactivité) ?",
        "options": [
            "Tristesse, Colère, Peur",
            "Inattention, Impulsivité, Hyperactivité motrice",
            "Retard de langage, Bégaiement, Tics",
            "Refus de manger, Insomnie, Pleurs"
        ],
        "answer": "Inattention, Impulsivité, Hyperactivité motrice",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le TDAH est un trouble neurodéveloppemental. L'enfant ne fait pas exprès d'être distrait ou agité.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que le 'Refoulement' ?",
        "options": [
            "Refuser d'entrer quelque part",
            "Le rejet dans l'inconscient de représentations ou pulsions inacceptables pour le Moi",
            "La peur de la foule",
            "Une forme de politesse"
        ],
        "answer": "Le rejet dans l'inconscient de représentations ou pulsions inacceptables pour le Moi",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la 'pierre angulaire' de la névrose selon Freud. Ce qui est refoulé cherche toujours à revenir (lapsus, rêves, symptômes).",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Qui a décrit le syndrome d'Hospitalisme (dépression anaclitique) chez le bébé privé de sa mère ?",
        "options": ["Sigmund Freud", "René Spitz", "Jean Piaget", "Henri Wallon"],
        "answer": "René Spitz",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il a montré que les bébés en orphelinat, bien nourris mais sans affection, se laissaient mourir de tristesse (marasme).",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que la 'Projection' ?",
        "options": [
            "Aller au cinéma",
            "Attribuer à autrui ses propres désirs, sentiments ou défauts que l'on refuse de reconnaître en soi (ex: 'Il me déteste' alors que c'est moi qui le déteste)",
            "Planifier l'avenir",
            "Se jeter par terre"
        ],
        "answer": "Attribuer à autrui ses propres désirs, sentiments ou défauts que l'on refuse de reconnaître en soi (ex: 'Il me déteste' alors que c'est moi qui le déteste)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un mécanisme fréquent dans la paranoïa, mais aussi dans la vie quotidienne.",
        "tag": "Mécanismes de Défense"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la dyade symptomatique principale du Trouble du Spectre de l'Autisme (TSA) selon le DSM-5 ?",
        "type": "ouverte",
        "answer": "1. Déficits de la communication et des interactions sociales. 2. Caractère restreint et répétitif des comportements, intérêts ou activités (stéréotypies).",
        "level": "Intermédiaire",
        "explanation": "On ne parle plus de la 'triade' (qui incluait le langage à part), mais de dyade. Les troubles sensoriels (hyper/hypo-sensibilité) sont aussi un critère clé.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que le 'Déni' (à ne pas confondre avec la dénégation) ?",
        "options": [
            "Dire non",
            "Le refus de reconnaître la réalité d'une perception traumatisante (ex: ne pas croire à la mort d'un proche)",
            "Mentir aux autres",
            "Oublier un rendez-vous"
        ],
        "answer": "Le refus de reconnaître la réalité d'une perception traumatisante (ex: ne pas croire à la mort d'un proche)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le déni porte sur la RÉALITÉ extérieure ('ça n'existe pas'). Le refoulement porte sur une pulsion INTÉRIEURE.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Qu'est-ce que l'Angoisse de Séparation (normale vers 8 mois) ?",
        "type": "ouverte",
        "answer": "C'est la détresse du bébé lorsque sa figure d'attachement s'éloigne ou lorsqu'il voit un visage inconnu (peur de l'étranger).",
        "level": "Intermédiaire",
        "explanation": "Cela prouve que le bébé a acquis la permanence de la personne (il sait que sa mère est unique) et qu'il a un attachement préférentiel.",
        "tag": "Développement"
    },
    {
        "q": "En quoi consiste la 'Sublimation' ?",
        "options": [
            "C'est l'évaporation d'un liquide",
            "La dérivation de l'énergie pulsionnelle (sexuelle ou agressive) vers des buts socialement valorisés (art, sport, travail, intellect)",
            "Le fait de rêver éveillé",
            "La répression des émotions"
        ],
        "answer": "La dérivation de l'énergie pulsionnelle (sexuelle ou agressive) vers des buts socialement valorisés (art, sport, travail, intellect)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est le seul mécanisme de défense considéré comme 'réussi' et non pathologique par Freud, car il crée de la culture.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Qu'est-ce que l'Écholalie chez l'enfant autiste ?",
        "type": "ouverte",
        "answer": "C'est la répétition automatique et immédiate (ou différée) des mots ou phrases entendus, souvent sans intention de communication (comme un perroquet).",
        "level": "Intermédiaire",
        "explanation": "C'est un signe clinique fréquent dans les TSA. Elle peut parfois avoir une fonction d'auto-stimulation ou d'apaisement.",
        "tag": "Psychopathologie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Décrivez les trois phases de l'Hospitalisme selon René Spitz.",
        "type": "ouverte",
        "answer": "1. Phase de protestation (pleurs, cris). 2. Phase de désespoir (retrait, refus de contact, perte de poids). 3. Phase de détachement (indifférence, retard de développement irréversible si la carence dure > 5 mois).",
        "level": "Avancé",
        "explanation": "Cela démontre que l'amour est aussi vital que la nourriture pour le développement du bébé.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que l'Identification à l'Agresseur (Anna Freud) ?",
        "options": [
            "Devenir policier",
            "Un mécanisme où le sujet reprend à son compte les attributs ou comportements de celui qui l'agresse pour maîtriser sa peur (passer de passif à actif)",
            "Dénoncer son agresseur",
            "Se cacher"
        ],
        "answer": "Un mécanisme où le sujet reprend à son compte les attributs ou comportements de celui qui l'agresse pour maîtriser sa peur (passer de passif à actif)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'enfant grondé gronde sa poupée. C'est un moyen de gérer le traumatisme en devenant soi-même celui qui fait peur.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Dans le TDAH, quelle est la différence entre Impulsivité Cognitive et Impulsivité Motrice ?",
        "type": "ouverte",
        "answer": "Impulsivité Cognitive : répondre avant la fin de la question, incapacité à différer la pensée. Impulsivité Motrice : incapacité à inhiber un geste, couper la parole, se lever, toucher à tout.",
        "level": "Avancé",
        "explanation": "C'est un déficit des fonctions exécutives (inhibition).",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que le 'Clivage du Moi' (défense archaïque) ?",
        "options": [
            "Avoir une double personnalité",
            "La coexistence au sein du Moi de deux attitudes psychiques opposées et indépendantes face à la réalité (l'une accepte la réalité, l'autre la dénie)",
            "Avoir mal à la tête",
            "Hésiter entre deux choix"
        ],
        "answer": "La coexistence au sein du Moi de deux attitudes psychiques opposées et indépendantes face à la réalité (l'une accepte la réalité, l'autre la dénie)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Typique des états limites (borderline) ou de la psychose. Le sujet sépare le monde en 'tout bon' ou 'tout mauvais' sans nuance.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Qu'est-ce que la 'Dysharmonie Évolutive' (ou Dysharmonie Psychotique) ?",
        "type": "ouverte",
        "answer": "C'est un développement hétérogène de l'enfant où certains secteurs sont matures (ex: intelligence) et d'autres très immatures ou pathologiques (ex: relationnel, affectif), avec une angoisse massive.",
        "level": "Avancé",
        "explanation": "C'est un diagnostic complexe (classif française CFTMEA), souvent à la frontière entre psychose et névrose grave.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Quelle est la différence entre une Angoisse et une Peur ?",
        "options": [
            "La peur est plus forte",
            "La peur a un objet identifié (peur du chien), l'angoisse est une peur sans objet, indéfinissable, liée à une menace intérieure",
            "L'angoisse touche les adultes, la peur les enfants",
            "C'est la même chose"
        ],
        "answer": "La peur a un objet identifié (peur du chien), l'angoisse est une peur sans objet, indéfinissable, liée à une menace intérieure",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'angoisse est le signal d'alarme du Moi face à un danger pulsionnel.",
        "tag": "Psychologie Clinique"
    },
    {
        "q": "Qu'est-ce que la 'Rationalisation' ?",
        "options": [
            "Être bon en maths",
            "Justifier après coup, par des raisons logiques et acceptables, une attitude ou un sentiment dont le véritable motif (pulsionnel) est refoulé",
            "Planifier sa journée",
            "Parler calmement"
        ],
        "answer": "Justifier après coup, par des raisons logiques et acceptables, une attitude ou un sentiment dont le véritable motif (pulsionnel) est refoulé",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Exemple : 'J'ai raté cet examen parce que le prof est nul' (pour éviter de dire 'je n'ai pas travaillé'). C'est se raconter une histoire pour ne pas culpabiliser.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Dans l'autisme, qu'est-ce que le 'Défaut de Théorie de l'Esprit' ?",
        "type": "ouverte",
        "answer": "C'est l'incapacité (ou la difficulté) à attribuer des états mentaux (pensées, croyances, intentions) aux autres et à comprendre qu'ils peuvent être différents des siens.",
        "level": "Avancé",
        "explanation": "C'est ce qui rend les interactions sociales si difficiles (cécité mentale). Ils ne comprennent pas l'implicite, l'ironie ou le mensonge.",
        "tag": "Psychologie Cognitive / TSA"
    },
    {
        "q": "Qu'est-ce que l'Annulation Rétroactive ?",
        "options": [
            "Effacer un dessin",
            "Faire en sorte que des pensées, paroles ou gestes passés ne soient pas advenus en utilisant une pensée ou un comportement contraire (ex: tocs de vérification)",
            "Oublier le passé",
            "Demander pardon"
        ],
        "answer": "Faire en sorte que des pensées, paroles ou gestes passés ne soient pas advenus en utilisant une pensée ou un comportement contraire (ex: tocs de vérification)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Typique de la névrose obsessionnelle. C'est une pensée magique.",
        "tag": "Mécanismes de Défense"
    },
    {
        "q": "Qu'est-ce que la 'Dépression Anaclitique' décrite par Spitz ?",
        "type": "ouverte",
        "answer": "C'est un état dépressif grave du nourrisson séparé de sa mère (après avoir eu une relation normale) pendant plus de 3 mois. Symptômes : pleurs, retrait, regard vide, insomnie, perte de poids.",
        "level": "Avancé",
        "explanation": "Si la mère revient avant 3-5 mois, c'est réversible. Sinon, cela évolue vers l'hospitalisme.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Quelle est la définition du 'Stress' selon Hans Selye (Syndrome Général d'Adaptation) ?",
        "options": [
            "Une maladie mentale",
            "Une réponse non spécifique de l'organisme face à toute demande d'adaptation qui lui est faite",
            "La peur de mourir",
            "Le fait d'être pressé"
        ],
        "answer": "Une réponse non spécifique de l'organisme face à toute demande d'adaptation qui lui est faite",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le stress n'est pas négatif en soi (eustress), c'est une réaction physiologique de survie. C'est son excès ou sa chronicité qui devient pathologique.",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Qu'a démontré l'expérience de Milgram (1963) ?",
        "options": [
            "Que les gens sont méchants par nature",
            "La soumission à l'autorité : une majorité d'individus normaux peuvent infliger des souffrances mortelles à autrui si une figure d'autorité légitime leur en donne l'ordre",
            "L'effet de groupe",
            "La mémoire visuelle"
        ],
        "answer": "La soumission à l'autorité : une majorité d'individus normaux peuvent infliger des souffrances mortelles à autrui si une figure d'autorité légitime leur en donne l'ordre",
        "type": "qcm",
        "level": "Basique",
        "explanation": "65% des sujets sont allés jusqu'à la décharge maximale (450V) simplement parce qu'un scientifique en blouse blanche leur disait 'l'expérience exige que vous continuiez'.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce qu'un 'Stéréotype' ?",
        "options": [
            "Une insulte raciste",
            "Une croyance partagée et simplificatrice concernant les caractéristiques d'un groupe social (ex: 'les Italiens parlent avec les mains')",
            "Un comportement discriminatoire",
            "Une vérité scientifique"
        ],
        "answer": "Une croyance partagée et simplificatrice concernant les caractéristiques d'un groupe social (ex: 'les Italiens parlent avec les mains')",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le stéréotype est une 'image dans la tête' (cognitif). Le préjugé est l'attitude (affectif) et la discrimination est le comportement (action).",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce que l'Empathie ?",
        "options": [
            "Souffrir avec l'autre",
            "La capacité à se mettre à la place de l'autre et à percevoir ce qu'il ressent, tout en gardant une distance et en sachant qu'on n'est pas l'autre",
            "Être gentil",
            "La pitié"
        ],
        "answer": "La capacité à se mettre à la place de l'autre et à percevoir ce qu'il ressent, tout en gardant une distance et en sachant qu'on n'est pas l'autre",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Sans cette distance ('comme si'), ce n'est plus de l'empathie mais de la contagion émotionnelle ou de la sympathie, ce qui mène à l'épuisement professionnel.",
        "tag": "Relation de Soin"
    },
    {
        "q": "Qu'est-ce que le 'Burn-out' ?",
        "options": [
            "Une dépression classique",
            "Un syndrome d'épuisement professionnel physique, émotionnel et mental lié à une exposition prolongée à des situations de travail exigeantes émotionnellement",
            "Un coup de fatigue passager",
            "Une maladie cardiaque"
        ],
        "answer": "Un syndrome d'épuisement professionnel physique, émotionnel et mental lié à une exposition prolongée à des situations de travail exigeantes émotionnellement",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il touche particulièrement les métiers d'aide (soignants, travailleurs sociaux, enseignants).",
        "tag": "Psychologie de la Santé"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Dans le modèle transactionnel du stress (Lazarus & Folkman), qu'est-ce que le 'Coping' ?",
        "type": "ouverte",
        "answer": "Ce sont les efforts cognitifs et comportementaux (stratégies) mis en place par l'individu pour faire face (gérer, réduire, tolérer) aux exigences d'une situation stressante.",
        "level": "Intermédiaire",
        "explanation": "On distingue le Coping centré sur le problème (agir) et le Coping centré sur l'émotion (se calmer).",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Qu'a démontré l'expérience de Asch sur les lignes ?",
        "options": [
            "L'intelligence visuelle",
            "Le Conformisme de groupe : un individu peut nier sa propre perception correcte pour se rallier à l'avis erroné de la majorité, par peur du rejet",
            "La rivalité",
            "L'altruisme"
        ],
        "answer": "Le Conformisme de groupe : un individu peut nier sa propre perception correcte pour se rallier à l'avis erroné de la majorité, par peur du rejet",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Même face à une évidence (quelle ligne est la plus longue ?), 37% des réponses se conforment à l'avis faux du groupe.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce que l'Effet Placebo ?",
        "type": "ouverte",
        "answer": "C'est l'amélioration de l'état de santé (symptômes) attribuable non pas à l'efficacité pharmacologique du traitement, mais à la signification thérapeutique, aux attentes du patient et à la relation soignant-soigné.",
        "level": "Intermédiaire",
        "explanation": "C'est un effet psychobiologique réel (libération d'endorphines). Son inverse est l'effet Nocebo.",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Qu'est-ce que le 'Locus de Contrôle' (Rotter) ?",
        "options": [
            "Une zone du cerveau",
            "La tendance à attribuer la cause des événements soit à soi-même (Interne), soit à des facteurs extérieurs comme la chance ou le destin (Externe)",
            "La maîtrise de soi",
            "Le contrôle des sphincters"
        ],
        "answer": "La tendance à attribuer la cause des événements soit à soi-même (Interne), soit à des facteurs extérieurs comme la chance ou le destin (Externe)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Un locus interne favorise généralement une meilleure santé (on se sent acteur), sauf en cas d'échec incontrôlable (culpabilité).",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "En dynamique de groupe, qu'est-ce que la 'Facilitation Sociale' ?",
        "options": [
            "On travaille moins bien en groupe",
            "La présence d'autrui améliore les performances individuelles sur des tâches simples ou bien apprises",
            "On se fait des amis",
            "C'est la fête"
        ],
        "answer": "La présence d'autrui améliore les performances individuelles sur des tâches simples ou bien apprises",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "À l'inverse, sur une tâche complexe ou nouvelle, la présence d'autrui peut créer une 'Inhibition Sociale' (peur du jugement).",
        "tag": "Psychologie Sociale"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Citez les 3 phases du Syndrome Général d'Adaptation (SGA) décrit par Selye.",
        "type": "ouverte",
        "answer": "1. Phase d'Alarme (choc + contre-choc, adrénaline). 2. Phase de Résistance (adaptation, cortisol). 3. Phase d'Épuisement (effondrement des ressources, apparition des maladies).",
        "level": "Avancé",
        "explanation": "Le stress devient toxique quand on reste bloqué en phase de résistance trop longtemps, menant à l'épuisement (Burn-out).",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Qu'est-ce que la 'Dissonance Cognitive' (Festinger) ?",
        "options": [
            "Un trouble de l'audition",
            "Un état de tension inconfortable dû à la coexistence de deux cognitions (idées, croyances, actes) contradictoires (ex: fumer en sachant que ça tue)",
            "Une perte de mémoire",
            "Un conflit avec les autres"
        ],
        "answer": "Un état de tension inconfortable dû à la coexistence de deux cognitions (idées, croyances, actes) contradictoires (ex: fumer en sachant que ça tue)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Pour réduire cette tension, l'individu va souvent modifier ses croyances ('il faut bien mourir de quelque chose') plutôt que son comportement.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce que l'Effet Pygmalion (Rosenthal & Jacobson) ?",
        "type": "ouverte",
        "answer": "C'est une prophétie auto-réalisatrice : les attentes positives (ou négatives) d'une personne (ex: enseignant/soignant) envers une autre influencent inconsciemment le comportement de cette dernière, qui finit par se conformer à ces attentes.",
        "level": "Avancé",
        "explanation": "Si vous croyez qu'un patient va progresser, vous le traitez différemment (plus de sourires, de patience) et il progresse vraiment mieux.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Quelles sont les trois dimensions du Burn-out mesurées par le MBI (Maslach Burnout Inventory) ?",
        "options": [
            "Fatigue, Faim, Soif",
            "Épuisement émotionnel, Dépersonnalisation (cynisme) et Baisse de l'accomplissement personnel",
            "Dépression, Anxiété, Phobie",
            "Colère, Déni, Marchandage"
        ],
        "answer": "Épuisement émotionnel, Dépersonnalisation (cynisme) et Baisse de l'accomplissement personnel",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La dépersonnalisation est une défense : on traite les patients comme des objets ou des numéros pour ne plus ressentir d'émotion.",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Qu'est-ce que l'Erreur Fondamentale d'Attribution ?",
        "options": [
            "Se tromper de chemin",
            "La tendance à surestimer les causes internes (personnalité) et à sous-estimer les causes externes (situation) pour expliquer le comportement d'autrui",
            "Se tromper de diagnostic",
            "Oublier un nom"
        ],
        "answer": "La tendance à surestimer les causes internes (personnalité) et à sous-estimer les causes externes (situation) pour expliquer le comportement d'autrui",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Exemple : Si quelqu'un tombe, on pense 'il est maladroit' (interne) plutôt que 'le sol est glissant' (externe). Pour soi-même, on fait souvent l'inverse (Biais d'autocomplaisance).",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Qu'est-ce que l'Effet du Témoin (Bystander Effect) illustré par l'affaire Kitty Genovese ?",
        "type": "ouverte",
        "answer": "Plus il y a de témoins lors d'une situation d'urgence, moins chacun a de chance d'intervenir. C'est dû à la 'dilution de responsabilité' ('quelqu'un d'autre va le faire').",
        "level": "Avancé",
        "explanation": "Pour obtenir de l'aide dans une foule, il faut désigner quelqu'un précisément ('Toi avec le pull rouge, appelle les pompiers !').",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Dans le stress, quelle est la différence entre l'Évaluation Primaire et l'Évaluation Secondaire (Lazarus) ?",
        "options": [
            "Primaire = C'est grave ? Secondaire = Qu'est-ce que je peux faire ?",
            "Primaire = Cerveau gauche, Secondaire = Cerveau droit",
            "Primaire = Enfant, Secondaire = Adulte",
            "Il n'y a pas de différence"
        ],
        "answer": "Primaire = C'est grave ? Secondaire = Qu'est-ce que je peux faire ?",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le stress survient si l'évaluation primaire est 'Menace' et que l'évaluation secondaire est 'Je n'ai pas les ressources pour faire face'.",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "Définissez la Résilience (Boris Cyrulnik).",
        "type": "ouverte",
        "answer": "C'est la capacité d'un individu à reprendre un nouveau développement après un traumatisme psychique, à 'surmonter' l'épreuve sans être détruit.",
        "level": "Avancé",
        "explanation": "Ce n'est pas de l'invulnérabilité. C'est un processus dynamique soutenu par des facteurs de protection (tuteurs de résilience).",
        "tag": "Psychologie Clinique"
    },
    {
        "q": "Qu'est-ce que la 'Charge Allostatique' ?",
        "type": "ouverte",
        "answer": "C'est le coût physiologique cumulé pour l'organisme obligé de s'adapter en permanence à des facteurs de stress chroniques (usure du corps : HTA, troubles métaboliques).",
        "level": "Avancé",
        "explanation": "L'allostasie est le maintien de la stabilité par le changement. Quand le système est trop sollicité, la charge devient trop lourde (maladie).",
        "tag": "Psychologie de la Santé"
    },
    {
        "q": "En psychologie sociale, qu'est-ce que la 'Polarisation de groupe' ?",
        "options": [
            "Le groupe se sépare en deux",
            "La tendance du groupe à prendre des décisions plus extrêmes (plus risquées ou plus prudentes) que la moyenne des avis individuels de départ",
            "Le groupe gèle sur place",
            "Tout le monde est d'accord tout de suite"
        ],
        "answer": "La tendance du groupe à prendre des décisions plus extrêmes (plus risquées ou plus prudentes) que la moyenne des avis individuels de départ",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "La discussion renforce les opinions dominantes. C'est un mécanisme clé de la radicalisation ou des effets de foule.",
        "tag": "Psychologie Sociale"
    },
    {
        "q": "Quelle est la distinction entre Puberté et Adolescence ?",
        "options": [
            "C'est la même chose",
            "La Puberté est le phénomène biologique (maturation sexuelle), l'Adolescence est le processus psychique et social d'adaptation à ces changements",
            "La puberté dure plus longtemps",
            "L'adolescence commence à 18 ans"
        ],
        "answer": "La Puberté est le phénomène biologique (maturation sexuelle), l'Adolescence est le processus psychique et social d'adaptation à ces changements",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le corps change plus vite que la tête. L'adolescent doit s'approprier ce nouveau corps sexué et capable de procréer.",
        "tag": "Adolescence"
    },
    {
        "q": "Qu'est-ce qu'une 'Apraxie' ?",
        "options": [
            "Une perte de la vue",
            "Un trouble de la réalisation du geste volontaire (savoir-faire) sans paralysie ni déficit intellectuel",
            "Une incapacité à parler",
            "Un trouble de la marche"
        ],
        "answer": "Un trouble de la réalisation du geste volontaire (savoir-faire) sans paralysie ni déficit intellectuel",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le patient a la force musculaire et comprend l'ordre, mais 'ne sait plus comment faire' (ex: saluer, utiliser un peigne).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce qu'une 'Agnosie' ?",
        "options": [
            "L'oubli d'un nom",
            "L'incapacité à reconnaître (identifier) un objet par les sens, alors que les organes sensoriels fonctionnent bien",
            "La perte de l'odorat",
            "L'incapacité à écrire"
        ],
        "answer": "L'incapacité à reconnaître (identifier) un objet par les sens, alors que les organes sensoriels fonctionnent bien",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le patient voit la clé (vision intacte) mais ne sait pas ce que c'est. S'il la touche, il la reconnaît (agnosie visuelle mais pas tactile).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Quel est l'enjeu central de la crise d'adolescence ?",
        "options": [
            "Avoir de l'argent de poche",
            "La construction de l'identité propre (Qui suis-je ?) et l'autonomisation vis-à-vis des parents",
            "Réussir ses examens",
            "Apprendre à conduire"
        ],
        "answer": "La construction de l'identité propre (Qui suis-je ?) et l'autonomisation vis-à-vis des parents",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'adolescent doit 'tuer' symboliquement l'enfant qu'il était et les parents idéaux de l'enfance pour devenir adulte.",
        "tag": "Adolescence"
    },
    {
        "q": "Qu'est-ce que la Gérontologie ?",
        "options": [
            "La médecine des vieux",
            "L'étude scientifique du vieillissement sous tous ses aspects (biologique, psychologique, social)",
            "La science des dents",
            "L'étude de la marche"
        ],
        "answer": "L'étude scientifique du vieillissement sous tous ses aspects (biologique, psychologique, social)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La Gériatrie est la branche médicale (soin des maladies). La Gérontologie est la science globale du vieillir.",
        "tag": "Gérontologie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que l'Apraxie Idéomotrice ?",
        "options": [
            "Ne pas savoir utiliser un objet réel",
            "L'incapacité à réaliser des gestes simples isolés sur commande ou imitation (ex: faire au revoir, bras d'honneur, signe de croix)",
            "Ne pas savoir s'habiller",
            "Ne pas savoir dessiner"
        ],
        "answer": "L'incapacité à réaliser des gestes simples isolés sur commande ou imitation (ex: faire au revoir, bras d'honneur, signe de croix)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Il y a une déconnexion entre l'idée du geste et sa réalisation motrice. Par contre, le patient peut parfois faire le geste spontanément (dissociation automatico-volontaire).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Pourquoi le groupe de pairs (amis) est-il si important à l'adolescence ?",
        "type": "ouverte",
        "answer": "Il sert de nouveau support identificatoire et de réassurance narcissique ('Je suis comme eux, donc je suis normal') pour se détacher de la famille.",
        "level": "Intermédiaire",
        "explanation": "Le groupe offre un code, un style et une sécurité pour explorer le monde hors du cocon familial.",
        "tag": "Adolescence"
    },
    {
        "q": "Qu'est-ce que la Prosopagnosie ?",
        "options": [
            "La peur des gens",
            "L'incapacité à reconnaître les visages familiers (même sa propre famille ou soi-même dans un miroir)",
            "La perte de la vision des couleurs",
            "L'incapacité à lire"
        ],
        "answer": "L'incapacité à reconnaître les visages familiers (même sa propre famille ou soi-même dans un miroir)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le patient identifie les gens à la voix, aux vêtements ou à la démarche. C'est une agnosie visuelle spécifique.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce que la 'Crise du Milieu de Vie' (Midlife Crisis) ?",
        "type": "ouverte",
        "answer": "C'est une période de transition (40-50 ans) marquée par la prise de conscience du temps qui passe et de la finitude, entraînant un bilan de vie et parfois des remaniements majeurs (professionnels, conjugaux).",
        "level": "Intermédiaire",
        "explanation": "C'est la 'seconde adolescence' de l'adulte (Jung). On passe de 'temps depuis la naissance' à 'temps restant à vivre'.",
        "tag": "Psychologie Adulte"
    },
    {
        "q": "En quoi consiste l'Apraxie de l'Habillage ?",
        "options": [
            "Ne pas avoir de goût vestimentaire",
            "L'incapacité à orienter et disposer correctement les vêtements sur le corps (mettre le pantalon sur la tête, inverser devant/derrière)",
            "Ne pas pouvoir boutonner (motricité fine)",
            "Refuser de s'habiller"
        ],
        "answer": "L'incapacité à orienter et disposer correctement les vêtements sur le corps (mettre le pantalon sur la tête, inverser devant/derrière)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Souvent liée à une lésion pariétale droite (trouble du schéma corporel et de l'espace).",
        "tag": "Neuropsychologie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que le 'Travail de Vieillir' (Messy) ?",
        "type": "ouverte",
        "answer": "C'est l'effort psychique que doit fournir la personne âgée pour accepter les pertes (santé, rôle social, proches) et remanier son identité sans sombrer dans la dépression.",
        "level": "Avancé",
        "explanation": "Bien vieillir n'est pas passif. C'est un travail de deuil et de réinvestissement d'autres objets (transmission, sagesse).",
        "tag": "Gérontologie"
    },
    {
        "q": "Qu'est-ce que l'Apraxie Idéatoire ?",
        "options": [
            "Ne pas avoir d'idées",
            "L'incapacité à manipuler des objets réels dans une séquence complexe (ex: allumer une bougie avec une allumette, préparer un café)",
            "Ne pas savoir imiter un geste",
            "Ne pas savoir écrire"
        ],
        "answer": "L'incapacité à manipuler des objets réels dans une séquence complexe (ex: allumer une bougie avec une allumette, préparer un café)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une 'panne du scénario' de l'action. Le patient frotte la bougie sur la boîte d'allumettes. C'est grave pour l'autonomie (repas, toilette).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'appelle-t-on le 'Processus Pubertaire' au sens psychique ?",
        "type": "ouverte",
        "answer": "C'est la réactivation des conflits œdipiens à l'adolescence. La sexualité génitale devient possible biologiquement, ce qui rend l'interdit de l'inceste concret et angoissant, obligeant l'ado à se détourner de ses parents.",
        "level": "Avancé",
        "explanation": "C'est le 'second temps' de la sexualité humaine (après la sexualité infantile).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que l'Apraxie Constructive ?",
        "options": [
            "Ne pas savoir construire des phrases",
            "La difficulté à assembler des éléments dans l'espace pour former un tout (ex: dessiner un cube, faire un puzzle, copier une figure)",
            "Ne pas savoir bricoler",
            "L'incapacité à faire des gestes symboliques"
        ],
        "answer": "La difficulté à assembler des éléments dans l'espace pour former un tout (ex: dessiner un cube, faire un puzzle, copier une figure)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Très fréquente dans la maladie d'Alzheimer et les lésions pariétales. On la teste avec le test de l'Horloge ou la Figure de Rey.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce que l'Anosognosie ?",
        "type": "ouverte",
        "answer": "C'est l'incapacité pathologique d'un patient à reconnaître sa propre maladie ou ses déficits (ex: un hémiplégique qui affirme qu'il peut marcher).",
        "level": "Avancé",
        "explanation": "Ce n'est pas du déni psychologique (défense), mais un trouble neurologique de la conscience de soi.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Pourquoi la maturation du Lobe Frontal est-elle cruciale à l'adolescence ?",
        "options": [
            "Elle permet de grandir",
            "Elle permet le développement des fonctions exécutives (inhibition, jugement, contrôle des impulsions) qui sont les dernières à maturer (jusqu'à 25 ans)",
            "Elle permet la vision",
            "Elle permet la digestion"
        ],
        "answer": "Elle permet le développement des fonctions exécutives (inhibition, jugement, contrôle des impulsions) qui sont les dernières à maturer (jusqu'à 25 ans)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Cela explique la prise de risque et l'impulsivité des ados : le moteur (émotions/pulsions) est puissant, mais les freins (frontal) ne sont pas encore finis.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce que le 'Syndrome de Glissement' chez la personne âgée ?",
        "type": "ouverte",
        "answer": "C'est une décompensation rapide et globale de l'état général (refus de manger, de boire, de parler) suite à un événement déclencheur (chute, deuil, grippe), menant souvent au décès par 'laisser-aller'.",
        "level": "Avancé",
        "explanation": "C'est une urgence gériatrique, une forme de suicide inconscient ou de renoncement vital.",
        "tag": "Gérontologie"
    },
    {
        "q": "Quelle est la différence entre une 'Plainte mnésique' bénigne et un début de démence (Alzheimer) ?",
        "options": [
            "La bénigne concerne le passé, la démence le présent",
            "Dans la plainte bénigne, le sujet a conscience d'oublier et s'en inquiète. Dans la démence débutante, le sujet minimise ou oublie qu'il a oublié (anosognosie partielle) et c'est l'entourage qui s'inquiète.",
            "Il n'y a pas de différence",
            "La bénigne se soigne"
        ],
        "answer": "Dans la plainte bénigne, le sujet a conscience d'oublier et s'en inquiète. Dans la démence débutante, le sujet minimise ou oublie qu'il a oublié (anosognosie partielle) et c'est l'entourage qui s'inquiète.",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le 'bon' vieillissement s'accompagne d'un ralentissement de récupération, mais pas d'oubli des événements récents.",
        "tag": "Gérontologie"
    },
    {
        "q": "Qu'est-ce que les 'Fonctions Instrumentales' ?",
        "type": "ouverte",
        "answer": "Ce sont les outils cognitifs localisables dans le cerveau qui permettent l'interaction avec le monde : Langage, Geste (Praxies), Perception (Gnosies), Calcul, Mémoire.",
        "level": "Avancé",
        "explanation": "On les distingue des Fonctions Exécutives (le chef d'orchestre) et de l'Intelligence globale.",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Qu'est-ce que l'Héminégligence (Négligence Spatiale Unilatérale) ?",
        "options": [
            "Une paralysie de la moitié du corps",
            "L'incapacité à prêter attention, à réagir ou à s'orienter vers des stimuli présentés dans l'hémi-espace opposé à la lésion cérébrale (souvent gauche ignoré après lésion droite)",
            "Une cécité d'un œil",
            "Une surdité"
        ],
        "answer": "L'incapacité à prêter attention, à réagir ou à s'orienter vers des stimuli présentés dans l'hémi-espace opposé à la lésion cérébrale (souvent gauche ignoré après lésion droite)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le patient ne rase que la moitié droite de son visage, ne mange que la moitié droite de son assiette. Ce n'est pas un problème visuel, mais attentionnel.",
        "tag": "Neuropsychologie"
    },
    
    ],

    "MODULE 5: Psychiatrie": [
        # HISTOIRE & CADRE LÉGAL
        {
        "q": "Quelle est la définition fondamentale de la Psychiatrie ?",
        "options": [
            "L'étude de l'âme",
            "La branche de la médecine spécialisée dans le diagnostic, la prévention et le traitement des troubles mentaux",
            "La science du comportement",
            "Une méthode de relaxation"
        ],
        "answer": "La branche de la médecine spécialisée dans le diagnostic, la prévention et le traitement des troubles mentaux",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Contrairement à la psychologie (sciences humaines), la psychiatrie est une discipline médicale. Le psychiatre est un médecin.",
        "tag": "Définition"
    },
    {
        "q": "En sémiologie, qu'est-ce que la 'Catatonie' ?",
        "options": [
            "Une grande fatigue",
            "Un syndrome psychomoteur caractérisé par une inertie, un négativisme, une immobilité et parfois des accès d'agitation",
            "Une paralysie des jambes",
            "Une perte de mémoire"
        ],
        "answer": "Un syndrome psychomoteur caractérisé par une inertie, un négativisme, une immobilité et parfois des accès d'agitation",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un trouble majeur de la psychomotricité, souvent associé à la schizophrénie, où le corps se fige ou répète des gestes sans but.",
        "tag": "Sémiologie Catatonie"
    },
    {
        "q": "Qu'est-ce qu'un trouble psychosomatique ?",
        "options": [
            "Une maladie imaginaire",
            "Une lésion réelle d'un organe dont l'apparition ou l'évolution est favorisée par des facteurs psychologiques",
            "Une simulation pour ne pas aller au travail",
            "Une infection virale"
        ],
        "answer": "Une lésion réelle d'un organe dont l'apparition ou l'évolution est favorisée par des facteurs psychologiques",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le corps 'parle' quand la tête ne peut pas dire. Ex: ulcère, eczéma, asthme. Il y a une vraie atteinte organique (contrairement à la conversion hystérique).",
        "tag": "Psychosomatique"
    },
    {
        "q": "Qu'est-ce que l'Alexithymie ?",
        "options": [
            "La peur des mots",
            "L'incapacité à identifier et à exprimer ses propres émotions avec des mots",
            "La dyslexie",
            "L'absence de rêves"
        ],
        "answer": "L'incapacité à identifier et à exprimer ses propres émotions avec des mots",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un trait fréquent chez les patients psychosomatiques. L'émotion ne pouvant être verbalisée, elle se décharge directement dans le corps (somatisation).",
        "tag": "Sémiologie"
    },
    {
        "q": "Quel signe clinique décrit une résistance active ou passive à toute sollicitation (refus de serrer la main, de bouger) ?",
        "options": ["Le Négativisme", "L'Optimisme", "La Catalepsie", "L'Apathie"],
        "answer": "Le Négativisme",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le patient fait le contraire de ce qu'on lui demande ou s'oppose physiquement (raidissement) à la mobilisation.",
        "tag": "Sémiologie Catatonie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Dans le syndrome catatonique, qu'est-ce que la 'Catalepsie' (ou flexibilité cireuse) ?",
        "type": "ouverte",
        "answer": "C'est le maintien d'attitudes ou de positions imposées par l'examinateur, même inconfortables, pendant une longue durée (comme une poupée de cire).",
        "level": "Intermédiaire",
        "explanation": "Si on lève le bras du patient, il le garde en l'air indéfiniment. C'est un trouble du tonus et de l'initiative motrice.",
        "tag": "Sémiologie Catatonie"
    },
    {
        "q": "Qu'est-ce que le 'Signe de l'oreiller' psychique ?",
        "options": [
            "Dormir tout le temps",
            "Le patient, allongé, garde la tête soulevée au-dessus du matelas pendant longtemps comme s'il avait un oreiller invisible",
            "Une hallucination visuelle",
            "Une douleur cervicale"
        ],
        "answer": "Le patient, allongé, garde la tête soulevée au-dessus du matelas pendant longtemps comme s'il avait un oreiller invisible",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un signe pathognomonique (typique) de la catatonie.",
        "tag": "Sémiologie Catatonie"
    },
    {
        "q": "Quelle est la différence entre Mythomanie et Pathomimie ?",
        "type": "ouverte",
        "answer": "Mythomanie : Falsification de l'histoire personnelle (mensonge verbal) à laquelle le sujet finit par croire. Pathomimie : Falsification de symptômes physiques (le sujet se crée volontairement des lésions ou maladies) pour obtenir le statut de malade.",
        "level": "Intermédiaire",
        "explanation": "Le Syndrome de Münchhausen est une forme grave de pathomimie avec errance médicale.",
        "tag": "Sémiologie"
    },
    {
        "q": "Qu'est-ce que l'Échopraxie ?",
        "options": [
            "Répéter les mots de l'autre",
            "Imiter en miroir les gestes et mouvements de l'interlocuteur de façon automatique",
            "Se regarder dans un miroir",
            "Avoir des tics"
        ],
        "answer": "Imiter en miroir les gestes et mouvements de l'interlocuteur de façon automatique",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Comme l'écholalie (répétition des mots), c'est un comportement d'écho fréquent dans la schizophrénie ou la catatonie.",
        "tag": "Sémiologie"
    },
    {
        "q": "Selon Maurice Berger (cité dans votre cours), quel est l'objectif de l'évaluation en pédopsychiatrie ?",
        "options": [
            "Donner une note à l'enfant",
            "Observer le comportement pour évaluer la nature des soins nécessaires (l'intelligence est-elle préservée ? le développement affectif est-il compromis ?)",
            "Placer l'enfant en foyer",
            "Prescrire des médicaments"
        ],
        "answer": "Observer le comportement pour évaluer la nature des soins nécessaires (l'intelligence est-elle préservée ? le développement affectif est-il compromis ?)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Il faut distinguer ce qui relève d'une maladie (ex: génétique) de ce qui relève de l'environnement (carences, maltraitance).",
        "tag": "Démarche de Soin"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le concept de 'Bénéfice Secondaire' dans la maladie.",
        "type": "ouverte",
        "answer": "C'est l'avantage (conscient ou inconscient) que le patient tire de sa maladie : attention de l'entourage, évitement de responsabilités, arrêt de travail, compassion.",
        "level": "Avancé",
        "explanation": "C'est un frein à la guérison. Dans l'hystérie ou la pathomimie, la recherche de ce statut de malade est centrale.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que la 'Verbigération' ?",
        "options": [
            "Parler trop vite",
            "La répétition inlassable de mots ou de phrases dénués de sens ou de contexte (salade de mots)",
            "L'incapacité à parler",
            "L'accent étranger"
        ],
        "answer": "La répétition inlassable de mots ou de phrases dénués de sens ou de contexte (salade de mots)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un trouble du langage et de la pensée fréquent dans les états psychotiques ou démentiels avancés.",
        "tag": "Sémiologie"
    },
    {
        "q": "Dans la Catatonie, que signifie la 'Paratonie' (ou Gegenhalten) ?",
        "type": "ouverte",
        "answer": "C'est une impossibilité pour le patient de se relâcher volontairement. Plus l'examinateur essaie de mobiliser un membre passif, plus le patient se raidit proportionnellement à la force exercée (oppositionnelle).",
        "level": "Avancé",
        "explanation": "C'est le contraire de la flexibilité cireuse. C'est une hypertonie active et involontaire.",
        "tag": "Sémiologie Catatonie"
    },
    {
        "q": "Quelles sont les étiologies (causes) principales d'un syndrome catatonique ?",
        "options": [
            "Uniquement la dépression",
            "La Schizophrénie, les Troubles de l'Humeur (Mélancolie stuporeuse, Manie), mais aussi des causes organiques (encéphalites, iatrogénie)",
            "La fatigue",
            "L'arthrose"
        ],
        "answer": "La Schizophrénie, les Troubles de l'Humeur (Mélancolie stuporeuse, Manie), mais aussi des causes organiques (encéphalites, iatrogénie)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Attention, la catatonie n'est pas égale à schizophrénie. Il faut éliminer une cause organique en urgence.",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce que la 'Stupeur' psychiatrique ?",
        "type": "ouverte",
        "answer": "C'est un état de suspension de toute activité motrice et relationnelle (immobilité, mutisme, visage inexpressif), sans perte de conscience (le patient est éveillé mais 'absent').",
        "level": "Avancé",
        "explanation": "On la retrouve dans la mélancolie (dépression grave) ou la catatonie. C'est une urgence (risque de déshydratation, escarres).",
        "tag": "Sémiologie"
    },
    {
        "q": "Le cours mentionne la 'Compréhension raisonnable' dans le soin. Quelle en est la limite ?",
        "options": [
            "Elle est parfaite",
            "Elle risque de réduire ce qui arrive à l'autre à nos propres pensées (projection). On comprend 'que l'autre a mal' mais on ne peut pas vraiment comprendre 'ce qu'il vit'.",
            "Elle est inutile",
            "Elle prend trop de temps"
        ],
        "answer": "Elle risque de réduire ce qui arrive à l'autre à nos propres pensées (projection). On comprend 'que l'autre a mal' mais on ne peut pas vraiment comprendre 'ce qu'il vit'.",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une mise en garde épistémologique. Le soignant doit rester neutre et laisser le patient déployer sa propre réalité sans plaquer la sienne.",
        "tag": "Concept du Soin"
    },
    {
        "q": "En quoi l'errance médicale ('Nomadisme médical') est-elle un signe de trouble factice (Münchhausen) ?",
        "type": "ouverte",
        "answer": "Le patient change d'hôpital, de ville ou de médecin dès que l'équipe commence à suspecter que les symptômes sont simulés, afin de recommencer son scénario ailleurs.",
        "level": "Avancé",
        "explanation": "Leur dossier médical est souvent épais, complexe, avec de multiples interventions chirurgicales ('abdomen cicatriciel').",
        "tag": "Sémiologie"
    },
    {
        "q": "Qu'est-ce que l'Hyperkinésie dans le cadre de la catatonie ?",
        "options": [
            "Un TDAH",
            "Des accès paroxystiques d'agitation motrice soudaine, violente et sans but (fureur catatonique), alternant avec la stupeur",
            "Le fait de parler vite",
            "Une crise d'épilepsie"
        ],
        "answer": "Des accès paroxystiques d'agitation motrice soudaine, violente et sans but (fureur catatonique), alternant avec la stupeur",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est ce qui rend la catatonie dangereuse. Le patient peut passer de l'immobilité totale à une explosion motrice imprévisible.",
        "tag": "Sémiologie Catatonie"
    },
    {
        "q": "Selon la pensée psychosomatique (Marty, M'Buzan), qu'est-ce que la 'Pensée Opératoire' ?",
        "type": "ouverte",
        "answer": "C'est une pensée factuelle, collée au concret et à l'instant présent, pauvre en fantasmes et en vie imaginaire. Le patient décrit les faits sans charge affective.",
        "level": "Avancé",
        "explanation": "C'est le corollaire de l'alexithymie. Le patient 'fonctionne' bien mais semble robotique émotionnellement.",
        "tag": "Psychosomatique"
    },
    {
        "q": "Qu'est-ce que la 'Suggestion' ou 'Suggestibilité' pathologique ?",
        "options": [
            "Donner une bonne idée",
            "La réceptivité excessive aux influences extérieures sans critique (ex: le patient exécute n'importe quel ordre absurde)",
            "L'hypnose",
            "La psychothérapie"
        ],
        "answer": "La réceptivité excessive aux influences extérieures sans critique (ex: le patient exécute n'importe quel ordre absurde)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un symptôme de la catatonie (obéissance automatique) mais aussi de l'hystérie.",
        "tag": "Sémiologie"
    },
    {
        "q": "Quelle est la caractéristique fondamentale de la 'Psychose' (par opposition à la Névrose) ?",
        "options": [
            "Le patient est triste",
            "La perte de contact avec la réalité (délire/hallucinations) et l'absence de conscience du trouble (anosognosie)",
            "Le patient a peur des araignées",
            "C'est une maladie génétique"
        ],
        "answer": "La perte de contact avec la réalité (délire/hallucinations) et l'absence de conscience du trouble (anosognosie)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le névrosé a conscience de son trouble (ex: 'je sais que c'est bête de laver mes mains 10 fois'). Le psychotique est convaincu que son délire est réel.",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce qu'une Hallucination ?",
        "options": [
            "Une fausse croyance",
            "Une perception sans objet (entendre/voir quelque chose qui n'existe pas)",
            "Un cauchemar",
            "Une erreur de jugement"
        ],
        "answer": "Une perception sans objet (entendre/voir quelque chose qui n'existe pas)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "À distinguer de l'illusion (qui est une déformation d'un objet réel). Les plus fréquentes en psychiatrie sont auditives (entendre des voix).",
        "tag": "Sémiologie"
    },
    {
        "q": "Quel trouble était anciennement appelé 'Psychose Maniaco-Dépressive' (PMD) ?",
        "options": ["La Schizophrénie", "Le Trouble Bipolaire", "L'Autisme", "La Paranoïa"],
        "answer": "Le Trouble Bipolaire",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il se caractérise par l'alternance de phases d'excitation (Manie) et de phases de dépression, séparées par des intervalles normaux (euthymie).",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce que la 'Logorrhée' fréquente dans l'accès maniaque ?",
        "options": [
            "La peur des mots",
            "Un flux de paroles rapide, intarissable et continu (besoin irrésistible de parler)",
            "Une perte de la parole",
            "Le bégaiement"
        ],
        "answer": "Un flux de paroles rapide, intarissable et continu (besoin irrésistible de parler)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le reflet de l'accélération de la pensée (tachypsychie) du patient maniaque.",
        "tag": "Sémiologie"
    },
    {
        "q": "Quel est le risque majeur et immédiat de la Mélancolie (dépression grave) ?",
        "options": ["La prise de poids", "Le suicide (passage à l'acte auto-agressif)", "L'insomnie", "L'agressivité envers autrui"],
        "answer": "Le suicide (passage à l'acte auto-agressif)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le patient mélancolique est convaincu de son indignité et de sa culpabilité délirante. La mort lui apparaît comme la seule solution logique/méritée.",
        "tag": "Urgence Psychiatrique"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quels sont les trois groupes de symptômes (trépied) de la Schizophrénie ?",
        "type": "ouverte",
        "answer": "1. Symptômes Positifs (Délire, Hallucinations). 2. Symptômes Négatifs (Repli, Apragmatisme, Emoussement affectif). 3. Symptômes de Désorganisation (Dissociation, bizarrerie).",
        "level": "Intermédiaire",
        "explanation": "C'est la définition moderne (DSM). Anciennement, on parlait surtout de la dissociation (Spaltung).",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce que l'Apragmatisme ?",
        "options": [
            "Une difficulté à faire des gestes",
            "L'incapacité à entreprendre des actions (perte d'initiative et d'élan vital) malgré la capacité physique de le faire",
            "Un trouble de la parole",
            "Une hallucination"
        ],
        "answer": "L'incapacité à entreprendre des actions (perte d'initiative et d'élan vital) malgré la capacité physique de le faire",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le patient peut rester des heures au lit ou sur une chaise sans rien faire. C'est un symptôme négatif majeur.",
        "tag": "Sémiologie"
    },
    {
        "q": "Dans la Paranoïa, quel est le mécanisme principal du délire ?",
        "options": [
            "L'hallucination (il entend des voix)",
            "L'Interprétation (il donne un sens erroné et menaçant à des faits réels)",
            "L'imagination",
            "L'intuition"
        ],
        "answer": "L'Interprétation (il donne un sens erroné et menaçant à des faits réels)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "'Le voisin a fermé ses volets, C'EST LA PREUVE qu'il m'espionne'. Le fait est vrai (volets fermés), la déduction est délirante.",
        "tag": "Sémiologie"
    },
    {
        "q": "Qu'est-ce que l'Anhédonie ?",
        "type": "ouverte",
        "answer": "C'est la perte de la capacité à éprouver du plaisir (activités, nourriture, relations) qui procurait auparavant de la satisfaction.",
        "level": "Intermédiaire",
        "explanation": "Symptôme central de la dépression et de la schizophrénie (signe négatif).",
        "tag": "Sémiologie"
    },
    {
        "q": "Quelle est la différence entre un délire 'Systématisé' et 'Non-systématisé' ?",
        "options": [
            "Systématisé = Cohérent, logique (paranoïa). Non-systématisé = Flou, morcelé, incohérent (schizophrénie)",
            "Systématisé = Grave. Non-systématisé = Bénin",
            "Systématisé = Hallucinations. Non-systématisé = Interprétations",
            "C'est la même chose"
        ],
        "answer": "Systématisé = Cohérent, logique (paranoïa). Non-systématisé = Flou, morcelé, incohérent (schizophrénie)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Un paranoïaque peut vous convaincre (délire plausible). Un schizophrène raconte des choses absurdes et hermétiques.",
        "tag": "Sémiologie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le concept de 'Dissociation' (Spaltung) dans la Schizophrénie.",
        "type": "ouverte",
        "answer": "C'est la perte de l'unité psychique. Les idées, les émotions et les comportements ne sont plus accordés. (Ex: Rire immotivé en annonçant une nouvelle triste - discordance).",
        "level": "Avancé",
        "explanation": "C'est le trouble générateur de la schizophrénie selon Bleuler. Le patient est 'morcelé', bizarre, imprévisible.",
        "tag": "Concept Clé"
    },
    {
        "q": "Qu'est-ce que le 'Syndrome d'Automatisme Mental' (Clérambault) ?",
        "options": [
            "Avoir des tics",
            "La conviction délirante que quelqu'un d'autre pense, agit ou parle à sa place (vol de la pensée, écho de la pensée, gestes imposés)",
            "L'incapacité à réfléchir",
            "Un trouble moteur"
        ],
        "answer": "La conviction délirante que quelqu'un d'autre pense, agit ou parle à sa place (vol de la pensée, écho de la pensée, gestes imposés)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le patient se sent téléguidé, parasité. C'est le cœur des 'hallucinations psychiques' (voix intérieures).",
        "tag": "Sémiologie"
    },
    {
        "q": "En quoi consiste le délire érotomaniaque (Illusion délirante d'être aimé) ?",
        "type": "ouverte",
        "answer": "C'est la conviction inébranlable d'être aimé par quelqu'un (souvent d'un rang social plus élevé). Il évolue en 3 phases : Espoir, Dépit, Rancune (avec risque d'agression).",
        "level": "Avancé",
        "explanation": "C'est une forme de délire paranoïaque passionnel.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que la 'Tachypsychie' et la 'Fuite des idées' ?",
        "options": [
            "Un ralentissement de la pensée",
            "Une accélération anormale du rythme de la pensée (Manie), où les idées s'enchaînent trop vite, par coq-à-l'âne ou assonance, rendant le discours incohérent",
            "Une perte de mémoire",
            "Une obsession"
        ],
        "answer": "Une accélération anormale du rythme de la pensée (Manie), où les idées s'enchaînent trop vite, par coq-à-l'âne ou assonance, rendant le discours incohérent",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'inverse de la Bradypsychie (ralentissement) observée dans la dépression.",
        "tag": "Sémiologie"
    },
    {
        "q": "Quelle est la différence clinique entre une 'Bouffée Délirante Aiguë' (BDA) et l'entrée dans la Schizophrénie ?",
        "type": "ouverte",
        "answer": "La BDA est un épisode psychotique soudain et transitoire (< 1 mois) avec un délire riche et polymorphe, et un retour à la normale complet (critère de guérison). La Schizophrénie est une pathologie chronique (> 6 mois).",
        "level": "Avancé",
        "explanation": "Environ 30-40% des BDA évoluent vers une schizophrénie, mais ce n'est pas systématique.",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce que le 'Barrage' dans le discours du schizophrène ?",
        "options": [
            "Le patient refuse de parler",
            "Une suspension brusque et immotivée du discours (le patient s'arrête net), puis reprend sur un autre sujet ou le même, traduisant l'arrêt de la pensée",
            "Le bégaiement",
            "Une insulte"
        ],
        "answer": "Une suspension brusque et immotivée du discours (le patient s'arrête net), puis reprend sur un autre sujet ou le même, traduisant l'arrêt de la pensée",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le signe pathognomonique de la discordance/dissociation.",
        "tag": "Sémiologie"
    },
    {
        "q": "Dans la mélancolie, qu'est-ce que le 'Délire de Cotard' (ou délire de négation d'organes) ?",
        "type": "ouverte",
        "answer": "C'est une forme extrême de mélancolie où le patient pense qu'il n'a plus d'organes (plus de cœur, plus d'estomac), qu'il est déjà mort ou pourri de l'intérieur, voire immortel pour souffrir éternellement.",
        "level": "Avancé",
        "explanation": "C'est terrifiant pour le patient. Il peut refuser de manger car 'je n'ai plus d'estomac'.",
        "tag": "Sémiologie Rare"
    },
    {
        "q": "Qu'est-ce que l'Incurie fréquente dans les psychoses chroniques ?",
        "options": [
            "Une curiosité malsaine",
            "Une négligence totale de l'hygiène corporelle et vestimentaire, et de l'entretien du logement",
            "Une infection de la peau",
            "Un trouble de l'alimentation"
        ],
        "answer": "Une négligence totale de l'hygiène corporelle et vestimentaire, et de l'entretien du logement",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est souvent lié à l'apragmatisme (syndrome négatif). Le patient ne 'voit' plus la saleté ou n'a pas l'énergie de s'en occuper.",
        "tag": "Sémiologie"
    },
    {
        "q": "Pourquoi les antidépresseurs peuvent-ils être dangereux chez un patient bipolaire non diagnostiqué (sans régulateur d'humeur) ?",
        "type": "ouverte",
        "answer": "Ils risquent de provoquer un 'Virage Maniaque' : le patient passe brutalement de la dépression à l'excitation maniaque.",
        "level": "Avancé",
        "explanation": "C'est souvent ainsi qu'on découvre une bipolarité. On traite une dépression et le patient 'décolle' trop haut.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Qu'est-ce que la 'Rationalisme Morbide' chez le schizophrène ?",
        "options": [
            "Le fait d'être trop intelligent",
            "Une logique froide, géométrique et abstraite appliquée à des sujets vitaux, déconnectée de tout affect et de la réalité (ex: élaborer un système complexe pour expliquer pourquoi le sel est toxique)",
            "Un délire paranoïaque",
            "Une obsession de propreté"
        ],
        "answer": "Une logique froide, géométrique et abstraite appliquée à des sujets vitaux, déconnectée de tout affect et de la réalité (ex: élaborer un système complexe pour expliquer pourquoi le sel est toxique)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une forme de pensée autistique qui tourne à vide, coupée du bon sens (Spaltung intellectuelle).",
        "tag": "Sémiologie"
    },
    {
        "q": "Quelle est la définition clinique d'une Phobie ?",
        "options": [
            "Une peur rationnelle d'un danger réel",
            "Une crainte angoissante, irraisonnée et persistante d'un objet, d'une situation ou d'un être vivant, pourtant reconnu comme non dangereux par le sujet",
            "Le fait de ne pas aimer quelqu'un",
            "Une hallucination visuelle"
        ],
        "answer": "Une crainte angoissante, irraisonnée et persistante d'un objet, d'une situation ou d'un être vivant, pourtant reconnu comme non dangereux par le sujet",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le phobique SAIT que sa peur est absurde (conscience du trouble), mais il ne peut pas la contrôler. Il met en place des conduites d'évitement.",
        "tag": "Névrose Phobique"
    },
    {
        "q": "Qu'est-ce qu'une Obsession dans le TOC (Trouble Obsessionnel Compulsif) ?",
        "options": [
            "Une passion pour la musique",
            "Une idée, une image ou une impulsion qui s'impose à l'esprit de façon répétitive et parasite, générant une angoisse majeure",
            "Un geste répétitif",
            "Une voix qui parle"
        ],
        "answer": "Une idée, une image ou une impulsion qui s'impose à l'esprit de façon répétitive et parasite, générant une angoisse majeure",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'obsession est la pensée (ex: 'mes mains sont sales'). La compulsion est l'acte pour calmer l'angoisse (ex: se laver les mains).",
        "tag": "Névrose Obsessionnelle"
    },
    {
        "q": "Quelle est la caractéristique principale de la Personnalité Borderline (État Limite) ?",
        "options": [
            "L'instabilité émotionnelle, relationnelle et de l'image de soi, avec une impulsivité marquée et une peur de l'abandon",
            "La froideur et le détachement",
            "La méfiance et la suspicion",
            "L'ordre et la méticulosité"
        ],
        "answer": "L'instabilité émotionnelle, relationnelle et de l'image de soi, avec une impulsivité marquée et une peur de l'abandon",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Ce sont des patients 'écorchés vifs', passant de l'amour à la haine (clivage), avec un risque élevé de scarifications ou de tentatives de suicide.",
        "tag": "Trouble Personnalité"
    },
    {
        "q": "Qu'est-ce que l'Hystérie de conversion ?",
        "options": [
            "Crier très fort",
            "La transposition d'un conflit psychique inconscient en symptômes corporels (paralysie, cécité) sans lésion organique réelle",
            "Une maladie neurologique",
            "Un mensonge conscient"
        ],
        "answer": "La transposition d'un conflit psychique inconscient en symptômes corporels (paralysie, cécité) sans lésion organique réelle",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le symptôme a une valeur symbolique. Charcot a montré qu'on pouvait le faire disparaître par l'hypnose.",
        "tag": "Névrose Hystérique"
    },
    {
        "q": "Qu'est-ce qu'un objet 'Contraphobique' ?",
        "options": [
            "L'objet qui fait peur",
            "Un objet ou une personne dont la présence rassure le phobique et lui permet d'affronter la situation anxiogène",
            "Un médicament",
            "Une amulette magique"
        ],
        "answer": "Un objet ou une personne dont la présence rassure le phobique et lui permet d'affronter la situation anxiogène",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Exemple : L'agoraphobe ne peut pas sortir seul, mais peut traverser la ville si on lui tient le bras.",
        "tag": "Névrose Phobique"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle est la différence entre une Attaque de Panique et un Trouble Panique ?",
        "type": "ouverte",
        "answer": "L'Attaque de Panique est un épisode aigu isolé de peur intense. Le Trouble Panique est la répétition de ces attaques avec une 'anxiété anticipatoire' (peur d'avoir peur) qui modifie le comportement.",
        "level": "Intermédiaire",
        "explanation": "C'est l'anxiété anticipatoire qui crée le handicap social (on n'ose plus sortir).",
        "tag": "Trouble Anxieux"
    },
    {
        "q": "Quels sont les traits typiques de la Personnalité Paranoïaque (avant le délire) ?",
        "options": [
            "Indifférence et retrait",
            "Méfiance, Orgueil (hypertrophie du Moi), Psychorigidité et Fausseté du jugement",
            "Théâtralisme et séduction",
            "Impulsivité et instabilité"
        ],
        "answer": "Méfiance, Orgueil (hypertrophie du Moi), Psychorigidité et Fausseté du jugement",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Le paranoïaque ne pardonne rien, est procédurier et toujours sur la défensive.",
        "tag": "Trouble Personnalité"
    },
    {
        "q": "Qu'est-ce que la 'Belle indifférence' des hystériques décrite par Freud ?",
        "type": "ouverte",
        "answer": "C'est l'étonnante tranquillité ou détachement émotionnel du patient face à un symptôme pourtant grave (ex: être paralysé des jambes ne semble pas l'inquiéter outre mesure).",
        "level": "Intermédiaire",
        "explanation": "Cela prouve que l'angoisse a été convertie dans le corps. Le patient est soulagé psychiquement par son symptôme physique.",
        "tag": "Névrose Hystérique"
    },
    {
        "q": "Qu'est-ce qu'un 'Rituel' chez le patient obsessionnel ?",
        "options": [
            "Une habitude culturelle",
            "Un acte compulsif réalisé selon des règles précises et rigides pour conjurer l'angoisse liée à l'obsession",
            "Une prière religieuse",
            "Un tic moteur"
        ],
        "answer": "Un acte compulsif réalisé selon des règles précises et rigides pour conjurer l'angoisse liée à l'obsession",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Si le rituel est interrompu ou mal fait, l'angoisse remonte et le patient doit tout recommencer depuis le début.",
        "tag": "Névrose Obsessionnelle"
    },
    {
        "q": "Qu'est-ce que l'Agoraphobie ?",
        "options": [
            "La peur de la foule uniquement",
            "La peur des espaces d'où il serait difficile de s'échapper ou d'être secouru (foule, pont, tunnel, grands espaces vides)",
            "La peur des araignées",
            "La peur du vide"
        ],
        "answer": "La peur des espaces d'où il serait difficile de s'échapper ou d'être secouru (foule, pont, tunnel, grands espaces vides)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Ce n'est pas la peur des gens (phobie sociale), mais la peur de ne pas avoir d'issue de secours en cas de malaise.",
        "tag": "Névrose Phobique"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Dans la névrose obsessionnelle, expliquez le mécanisme de 'l'Annulation Rétroactive'.",
        "type": "ouverte",
        "answer": "C'est la pensée magique selon laquelle accomplir un acte contraire ou une pensée contraire efface l'acte ou la pensée précédente, comme si de rien n'était.",
        "level": "Avancé",
        "explanation": "Exemple : penser 'je veux qu'il meure', puis toucher du bois 3 fois pour 'annuler' cette pensée meurtrière.",
        "tag": "Mécanisme de Défense"
    },
    {
        "q": "Quelle est la structure de personnalité 'Schizoïde' ?",
        "options": [
            "Un début de schizophrénie",
            "Un détachement des relations sociales, une gamme d'émotions restreinte (froideur), une préférence pour les activités solitaires et l'introspection",
            "Une excentricité et des croyances bizarres (Schizotypique)",
            "Une peur des autres"
        ],
        "answer": "Un détachement des relations sociales, une gamme d'émotions restreinte (froideur), une préférence pour les activités solitaires et l'introspection",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le schizoïde ne souffre pas de son isolement (contrairement à l'évitant ou au phobique social). Il se suffit à lui-même.",
        "tag": "Trouble Personnalité"
    },
    {
        "q": "Qu'est-ce que le 'Bénéfice Primaire' du symptôme hystérique ?",
        "type": "ouverte",
        "answer": "C'est la réduction de l'angoisse interne grâce à la conversion somatique. Le conflit psychique est résolu (mal) en devenant un symptôme physique.",
        "level": "Avancé",
        "explanation": "Le bénéfice secondaire est l'avantage social (arrêt maladie). Le primaire est l'avantage psychique (on ne pense plus au conflit).",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que la 'Phobie d'Impulsion' ?",
        "options": [
            "Passer à l'acte violemment",
            "La peur obsédante de commettre un acte irrésistible et dangereux contre sa volonté (ex: peur de jeter son bébé par la fenêtre)",
            "La peur d'être impulsif",
            "Une hallucination motrice"
        ],
        "answer": "La peur obsédante de commettre un acte irrésistible et dangereux contre sa volonté (ex: peur de jeter son bébé par la fenêtre)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un symptôme obsessionnel (TOC) et non un passage à l'acte réel. Le patient lutte de toutes ses forces contre cette idée.",
        "tag": "Sémiologie"
    },
    {
        "q": "Qu'est-ce que la Personnalité Histrionique (Hystérique) ?",
        "options": [
            "Une personne qui crie tout le temps",
            "Une quête affective insatiable, un théâtralisme, une suggestibilité, un érotisation des rapports mais avec souvent une frigidité/inhibition sexuelle réelle",
            "Une personne dangereuse",
            "Une personne dépressive"
        ],
        "answer": "Une quête affective insatiable, un théâtralisme, une suggestibilité, un érotisation des rapports mais avec souvent une frigidité/inhibition sexuelle réelle",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle cherche à attirer l'attention pour être rassurée sur sa valeur. Elle joue un rôle.",
        "tag": "Trouble Personnalité"
    },
    {
        "q": "Qu'est-ce que la Dysmorphophobie ?",
        "options": [
            "La peur des formes",
            "La préoccupation obsédante concernant un défaut imaginaire ou minime de l'apparence physique",
            "La peur de grossir",
            "La peur des miroirs"
        ],
        "answer": "La préoccupation obsédante concernant un défaut imaginaire ou minime de l'apparence physique",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est une obsession centrée sur le corps (nez trop gros, peau moche), fréquente à l'adolescence, parfois début de schizophrénie.",
        "tag": "Sémiologie"
    },
    {
        "q": "Quelle est la différence entre une Névrose et un Trouble de la Personnalité ?",
        "type": "ouverte",
        "answer": "La Névrose est une maladie avec un début et une fin, des symptômes égodystoniques (qui gênent le patient). Le Trouble de la Personnalité est une manière d'être durable, rigide et égosyntonique (le patient pense qu'il est comme ça et que c'est les autres le problème).",
        "level": "Avancé",
        "explanation": "On 'a' une névrose, on 'est' une personnalité pathologique.",
        "tag": "Nosographie"
    },
    {
        "q": "Qu'est-ce que l'Asthénie névrotique ?",
        "options": [
            "Une fatigue liée au cancer",
            "Une fatigue présente dès le matin, paradoxalement améliorée par l'activité, sans cause organique",
            "Une flemme",
            "Une anémie"
        ],
        "answer": "Une fatigue présente dès le matin, paradoxalement améliorée par l'activité, sans cause organique",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'épuisement dû à la lutte permanente contre les conflits psychiques inconscients.",
        "tag": "Sémiologie"
    },
    {
        "q": "Dans la personnalité Narcissique, qu'est-ce qui cache souvent la mégalomanie apparente ?",
        "type": "ouverte",
        "answer": "Une estime de soi très fragile, une faille narcissique profonde et une dépendance au regard/admiration de l'autre pour exister.",
        "level": "Avancé",
        "explanation": "Le narcissique a besoin de mépriser les autres pour se sentir valorisé. Il ne supporte pas la critique.",
        "tag": "Trouble Personnalité"
    },
    {
        "q": "Qu'est-ce que la 'Conversion' symbolique ?",
        "type": "ouverte",
        "answer": "C'est quand le symptôme corporel 'raconte' le conflit. Exemple : une femme paralysée des jambes car elle est tiraillée entre partir avec son amant et rester avec son mari ('je ne peux plus avancer').",
        "level": "Avancé",
        "explanation": "Le corps devient un langage métaphorique.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Quelle est la triade symptomatique classique de l'Anorexie Mentale (les 3 A) ?",
        "options": [
            "Anxiété, Agitation, Agressivité",
            "Anorexie (lutte contre la faim), Amaigrissement, Aménorrhée (arrêt des règles)",
            "Asthme, Allergie, Anémie",
            "Appétit, Alcool, Amitié"
        ],
        "answer": "Anorexie (lutte contre la faim), Amaigrissement, Aménorrhée (arrêt des règles)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'anorexique a faim (au début) mais lutte activement contre elle pour contrôler son corps. L'aménorrhée signe la gravité biologique (le corps se met en veille).",
        "tag": "TCA"
    },
    {
        "q": "Qu'est-ce que le 'Craving' en addictologie ?",
        "options": [
            "L'envie de dormir",
            "Une envie irrépressible et violente de consommer la substance ou de réaliser le comportement, malgré la volonté d'arrêter",
            "La peur de l'eau",
            "La descente après la prise"
        ],
        "answer": "Une envie irrépressible et violente de consommer la substance ou de réaliser le comportement, malgré la volonté d'arrêter",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est le symptôme central de la dépendance. Le patient 'sait' qu'il ne doit pas, mais 'ne peut pas' résister.",
        "tag": "Addictologie"
    },
    {
        "q": "Quelle est la différence principale entre la Boulimie et l'Hyperphagie Boulimique (Binge Eating) ?",
        "options": [
            "Dans la boulimie, il y a des comportements compensatoires (vomissements, sport, laxatifs) pour ne pas grossir. Dans l'hyperphagie, il n'y en a pas (donc prise de poids).",
            "La boulimie concerne les hommes, l'hyperphagie les femmes",
            "C'est la même chose",
            "L'hyperphagie est moins grave"
        ],
        "answer": "Dans la boulimie, il y a des comportements compensatoires (vomissements, sport, laxatifs) pour ne pas grossir. Dans l'hyperphagie, il n'y en a pas (donc prise de poids).",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Les boulimiques ont souvent un poids normal ou fluctuant, alors que les hyperphagiques souffrent souvent d'obésité.",
        "tag": "TCA"
    },
    {
        "q": "Qu'est-ce que la 'Tolérance' (ou accoutumance) à un produit ?",
        "options": [
            "Le fait d'accepter les autres",
            "La nécessité d'augmenter les doses pour obtenir le même effet, car l'organisme s'habitue",
            "Une allergie au produit",
            "Le fait d'aimer le goût"
        ],
        "answer": "La nécessité d'augmenter les doses pour obtenir le même effet, car l'organisme s'habitue",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un piège physiologique qui pousse à la surconsommation et augmente le risque d'overdose.",
        "tag": "Addictologie"
    },
    {
        "q": "Qu'est-ce que la Potomanie ?",
        "options": [
            "L'addiction aux potes",
            "Le besoin irrépressible de boire de grandes quantités d'eau (parfois > 10L/jour)",
            "La peur de boire",
            "L'alcoolisme"
        ],
        "answer": "Le besoin irrépressible de boire de grandes quantités d'eau (parfois > 10L/jour)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un trouble psychiatrique (souvent psychotique) qui peut être mortel (intoxication par l'eau, hyponatrémie).",
        "tag": "TCA / Psychiatrie"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "En addictologie, comment définit-on le 'Sevrage' ?",
        "type": "ouverte",
        "answer": "C'est l'ensemble des symptômes physiques et psychiques (souffrance) qui apparaissent à l'arrêt brutal ou à la diminution de la consommation d'une substance dont le sujet est dépendant.",
        "level": "Intermédiaire",
        "explanation": "Le sevrage alcoolique (Delirium Tremens) peut être mortel sans surveillance médicale, contrairement au sevrage héroïne (très douloureux mais rarement mortel).",
        "tag": "Addictologie"
    },
    {
        "q": "Quelle est la particularité de l'Hyperactivité physique chez l'anorexique ?",
        "options": [
            "Elle est saine pour la santé",
            "C'est une hyperactivité compulsive et rigide visant à brûler des calories et à lutter contre la fatigue/faim, souvent niée par le patient",
            "C'est un TDAH associé",
            "Elle n'existe pas, les anorexiques sont fatiguées"
        ],
        "answer": "C'est une hyperactivité compulsive et rigide visant à brûler des calories et à lutter contre la fatigue/faim, souvent niée par le patient",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un symptôme paradoxal : plus elles sont épuisées, plus elles bougent ('marche ou crève').",
        "tag": "TCA"
    },
    {
        "q": "Qu'est-ce qu'une addiction 'comportementale' (sans substance) ?",
        "options": [
            "Fumer",
            "Une dépendance pathologique à une action : Jeux de hasard (Jeu pathologique), Jeux vidéo, Sexe, Sport (Bigorexie), Achats compulsifs",
            "Boire du café",
            "Manger du chocolat"
        ],
        "answer": "Une dépendance pathologique à une action : Jeux de hasard (Jeu pathologique), Jeux vidéo, Sexe, Sport (Bigorexie), Achats compulsifs",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Elles activent le même circuit de la récompense (dopamine) que les drogues.",
        "tag": "Addictologie"
    },
    {
        "q": "Qu'est-ce que le 'Lanugo' dans l'anorexie mentale ?",
        "options": [
            "Une dépression",
            "Un duvet fin qui pousse sur le corps pour tenter de le protéger du froid (thermorégulation) suite à la perte de graisse",
            "Un trouble des règles",
            "Une marque de médicament"
        ],
        "answer": "Un duvet fin qui pousse sur le corps pour tenter de le protéger du froid (thermorégulation) suite à la perte de graisse",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un signe clinique de dénutrition sévère.",
        "tag": "TCA"
    },
    {
        "q": "Quel est le mécanisme principal du 'Déni' dans l'anorexie ?",
        "type": "ouverte",
        "answer": "La patiente ne se voit pas maigre (dysmorphophobie) et ne ressent pas le danger. Elle affirme aller très bien ('je suis juste en forme'), refusant les soins.",
        "level": "Intermédiaire",
        "explanation": "C'est ce qui rend l'alliance thérapeutique si difficile. C'est une pathologie du lien et de l'image.",
        "tag": "TCA"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que le Syndrome de Korsakoff (souvent lié à l'alcoolisme chronique) ?",
        "options": [
            "Une cirrhose du foie",
            "Une encéphalopathie carentielle (manque de vitamine B1) caractérisée par une amnésie antérograde massive et des fabulations (fausses histoires pour combler les trous)",
            "Un délire de jalousie",
            "Une paralysie des jambes"
        ],
        "answer": "Une encéphalopathie carentielle (manque de vitamine B1) caractérisée par une amnésie antérograde massive et des fabulations (fausses histoires pour combler les trous)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est irréversible. Le patient oublie tout à mesure mais garde une façade sociale joviale.",
        "tag": "Addictologie / Neuropsy"
    },
    {
        "q": "Dans la boulimie, comment se déroule typiquement une crise ?",
        "type": "ouverte",
        "answer": "Sensation de vide/angoisse -> Ingestion brutale, massive et solitaire d'aliments (souvent sans plaisir, 'remplissage') -> Culpabilité/Honte -> Comportement compensatoire (Vomissement).",
        "level": "Avancé",
        "explanation": "La honte est centrale. Contrairement à l'anorexique qui s'exhibe (triomphe de la volonté), la boulimique se cache (échec de la volonté).",
        "tag": "TCA"
    },
    {
        "q": "Quel neurotransmetteur joue un rôle clé dans le 'Circuit de la Récompense' impliqué dans toutes les addictions ?",
        "options": ["L'Acétylcholine", "La Dopamine", "Le GABA", "L'Histamine"],
        "answer": "La Dopamine",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Les drogues piratent ce système naturel (fait pour manger/se reproduire) en provoquant une décharge massive de dopamine, créant une mémoire indélébile du plaisir.",
        "tag": "Neurobiologie"
    },
    {
        "q": "Qu'est-ce que le 'Mérycisme' ?",
        "type": "ouverte",
        "answer": "C'est un trouble (souvent chez le nourrisson ou le psychotique) consistant à régurgiter volontairement les aliments pour les remâcher et les ravaler (rumination).",
        "level": "Avancé",
        "explanation": "C'est un trouble de l'oralité et de la relation précoce.",
        "tag": "TCA"
    },
    {
        "q": "Qu'est-ce que la 'Co-dépendance' ou l'entourage 'Pathogène' ?",
        "options": [
            "Être accro à deux produits",
            "L'attitude de l'entourage qui, en voulant aider ou protéger l'addict (payer ses dettes, mentir pour lui), entretient involontairement l'addiction",
            "Se droguer ensemble",
            "Avoir un ami imaginaire"
        ],
        "answer": "L'attitude de l'entourage qui, en voulant aider ou protéger l'addict (payer ses dettes, mentir pour lui), entretient involontairement l'addiction",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le soin en addictologie inclut souvent la famille (thérapie systémique).",
        "tag": "Addictologie"
    },
    {
        "q": "Qu'est-ce que le 'Pica' ?",
        "options": [
            "Une danse",
            "L'ingestion répétée de substances non nutritives (terre, craie, papier, cheveux)",
            "Une forme d'anorexie",
            "Un pic de glycémie"
        ],
        "answer": "L'ingestion répétée de substances non nutritives (terre, craie, papier, cheveux)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le Pica est fréquent chez les jeunes enfants, les femmes enceintes (carences) ou dans les psychoses/déficiences intellectuelles.",
        "tag": "TCA"
    },
    {
        "q": "Pourquoi parle-t-on d'Addiction 'Iatrogène' ?",
        "options": [
            "C'est une addiction aux jeux",
            "C'est une dépendance provoquée par un traitement médical prescrit (ex: Benzodiazépines, Opioïdes antidouleur)",
            "C'est une addiction génétique",
            "C'est une addiction aux drogues dures"
        ],
        "answer": "C'est une dépendance provoquée par un traitement médical prescrit (ex: Benzodiazépines, Opioïdes antidouleur)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un problème de santé publique majeur. Le patient devient addict sur ordonnance.",
        "tag": "Addictologie"
    },
    {
        "q": "Dans l'Anorexie, quelle est la fonction psychique du symptôme selon l'approche psychodynamique ?",
        "type": "ouverte",
        "answer": "C'est une tentative de maîtrise absolue pour geler le temps, refuser la puberté (corps sexué) et rester dans une toute-puissance infantile, souvent pour ne pas se séparer psychiquement de la mère.",
        "level": "Avancé",
        "explanation": "Le corps maigre est un corps asexué, sans formes, un corps d'enfant ou d'ange qui n'a pas de besoins.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Qu'est-ce que l'Orthorexie ?",
        "options": [
            "Manger droit",
            "L'obsession pathologique de manger une nourriture saine (bio, sans gras, sans sucre), entraînant des évictions sociales et une angoisse majeure",
            "Aimer la viande",
            "Manger la nuit"
        ],
        "answer": "L'obsession pathologique de manger une nourriture saine (bio, sans gras, sans sucre), entraînant des évictions sociales et une angoisse majeure",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un nouveau TCA 'moderne'. Le plaisir de manger disparaît au profit du contrôle de la pureté de l'aliment.",
        "tag": "TCA"
    },
    {
        "q": "En addictologie, qu'est-ce que le modèle de Prochaska et DiClemente (Roue du changement) ?",
        "type": "ouverte",
        "answer": "C'est un modèle décrivant les stades de motivation à l'arrêt : Pré-contemplation (déni), Contemplation (ambivalence), Préparation, Action, Maintien, Rechute.",
        "level": "Avancé",
        "explanation": "Il est inutile de proposer un sevrage à quelqu'un en pré-contemplation. Il faut adapter le soin au stade de motivation.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Quelle est la classe de médicaments utilisée principalement pour traiter les psychoses et les hallucinations ?",
        "options": ["Les Antidépresseurs", "Les Neuroleptiques (ou Antipsychotiques)", "Les Anxiolytiques", "Les Antibiotiques"],
        "answer": "Les Neuroleptiques (ou Antipsychotiques)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Ils agissent en bloquant la dopamine. Ex: Haldol, Risperdal, Zyprexa. Ils ont pour but de réduire le délire et d'apaiser l'angoisse.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Quel est le risque principal d'une utilisation prolongée des Benzodiazépines (Anxiolytiques) ?",
        "options": [
            "La prise de muscle",
            "La dépendance (addiction) et l'accoutumance, ainsi que des troubles de la mémoire et des risques de chute",
            "L'hyperactivité",
            "La perte de cheveux"
        ],
        "answer": "La dépendance (addiction) et l'accoutumance, ainsi que des troubles de la mémoire et des risques de chute",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est pourquoi la durée de prescription doit être courte (4 à 12 semaines max en théorie). Ex: Valium, Xanax, Lexomil.",
        "tag": "Thérapeutique"
    },
    {
        "q": "En France, qui décide d'une Hospitalisation d'Office (HO), aujourd'hui appelée SDRE (Soins sur Décision du Représentant de l'État) ?",
        "options": ["Le psychiatre", "Le Préfet (ou le Maire en urgence)", "La famille", "Le patient"],
        "answer": "Le Préfet (ou le Maire en urgence)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une mesure administrative d'ordre public. Elle s'applique quand le patient est dangereux pour la sûreté des personnes ou l'ordre public.",
        "tag": "Législation"
    },
    {
        "q": "Quel médicament est le traitement de référence ('Gold Standard') pour réguler l'humeur dans le Trouble Bipolaire ?",
        "options": ["Le Doliprane", "Le Lithium", "La Vitamine C", "La Morphine"],
        "answer": "Le Lithium",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un thymorégulateur. Il nécessite des prises de sang régulières (lithiumémie) car la dose toxique est très proche de la dose efficace.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Qu'est-ce que le 'Consentement libre et éclairé' ?",
        "options": [
            "Signer un papier sans lire",
            "Le droit du patient d'accepter ou de refuser un soin après avoir reçu une information claire sur les bénéfices et les risques",
            "Obéir au médecin",
            "L'accord de la famille"
        ],
        "answer": "Le droit du patient d'accepter ou de refuser un soin après avoir reçu une information claire sur les bénéfices et les risques",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la base de l'éthique médicale (Loi Kouchner 2002). En psychiatrie, ce droit peut être suspendu en cas d'hospitalisation sous contrainte.",
        "tag": "Législation"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Pourquoi faut-il surveiller le début de traitement par antidépresseurs (le risque de 'levée de l'inhibition') ?",
        "type": "ouverte",
        "answer": "L'antidépresseur redonne de l'énergie motrice (au bout de quelques jours) AVANT d'améliorer l'humeur triste (qui prend 2-3 semaines). Il y a donc un risque accru de passage à l'acte suicidaire durant cette fenêtre.",
        "level": "Intermédiaire",
        "explanation": "Le patient a encore des idées noires mais retrouve la force de les mettre à exécution.",
        "tag": "Urgence / Thérapeutique"
    },
    {
        "q": "Qu'est-ce que le 'Syndrome Extrapyramidal', effet secondaire fréquent des neuroleptiques ?",
        "options": [
            "Un délire supplémentaire",
            "Des symptômes moteurs ressemblant à la maladie de Parkinson : tremblements, rigidité musculaire, raideur, marche à petits pas",
            "Une allergie cutanée",
            "Une perte de poids"
        ],
        "answer": "Des symptômes moteurs ressemblant à la maladie de Parkinson : tremblements, rigidité musculaire, raideur, marche à petits pas",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Très important pour le psychomotricien : ne pas confondre cette raideur iatrogène avec une catatonie ou une opposition.",
        "tag": "Thérapeutique / Psychomot"
    },
    {
        "q": "Quelles sont les conditions pour une ASPDT (anciennement HDT : Hospitalisation à la Demande d'un Tiers) ?",
        "options": [
            "Le patient est d'accord",
            "1. Troubles mentaux rendant impossible le consentement. 2. État imposant des soins immédiats et une surveillance constante. 3. Demande manuscrite d'un tiers (famille/proche) + 2 certificats médicaux.",
            "Le patient a commis un crime",
            "Le médecin est fatigué"
        ],
        "answer": "1. Troubles mentaux rendant impossible le consentement. 2. État imposant des soins immédiats et une surveillance constante. 3. Demande manuscrite d'un tiers (famille/proche) + 2 certificats médicaux.",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est la forme la plus courante d'hospitalisation sous contrainte.",
        "tag": "Législation"
    },
    {
        "q": "Qu'est-ce qu'un psychotrope 'Thymorégulateur' ?",
        "options": [
            "Il fait dormir",
            "Il stabilise l'humeur pour prévenir les récidives d'épisodes maniaques ou dépressifs (ex: Lithium, Dépakine)",
            "Il soigne la toux",
            "Il stimule l'appétit"
        ],
        "answer": "Il stabilise l'humeur pour prévenir les récidives d'épisodes maniaques ou dépressifs (ex: Lithium, Dépakine)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est le traitement de fond du trouble bipolaire.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Qu'est-ce que la 'Chambre d'Isolement' en psychiatrie ?",
        "type": "ouverte",
        "answer": "C'est une prescription médicale de dernier recours, pour une durée limitée, visant à contenir un patient en phase de crise (agitation, violence) pour sa sécurité et celle des autres, et non une punition.",
        "level": "Intermédiaire",
        "explanation": "Elle est très encadrée par la loi (registre, surveillance régulière).",
        "tag": "Soin Institutionnel"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que le 'Syndrome Malin des Neuroleptiques' ?",
        "options": [
            "Un effet secondaire bénin",
            "Une urgence vitale rare caractérisée par une hyperthermie majeure (40°C), une rigidité musculaire intense et des troubles de la conscience",
            "Une forme de dépression",
            "Une addiction aux neuroleptiques"
        ],
        "answer": "Une urgence vitale rare caractérisée par une hyperthermie majeure (40°C), une rigidité musculaire intense et des troubles de la conscience",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Il faut arrêter le traitement immédiatement et transférer en réanimation. Tout psychomotricien doit savoir qu'une fièvre inexpliquée sous neuroleptique est une alerte rouge.",
        "tag": "Urgence / Thérapeutique"
    },
    {
        "q": "Qu'est-ce que l'Akathisie (effet secondaire des neuroleptiques) ?",
        "type": "ouverte",
        "answer": "C'est une sensation pénible d'impatience musculaire (surtout dans les jambes) qui oblige le patient à bouger sans cesse, à piétiner ou à se lever (impossibilité de rester assis).",
        "level": "Avancé",
        "explanation": "C'est très handicapant. Souvent confondu à tort avec de l'agitation anxieuse ou psychotique.",
        "tag": "Sémiologie / Psychomot"
    },
    {
        "q": "Qu'est-ce que la 'Psychothérapie Institutionnelle' (courant historique) ?",
        "type": "ouverte",
        "answer": "C'est un mouvement (Oury, Tosquelles) qui considère que 'pour soigner les malades, il faut soigner l'hôpital'. Elle utilise la vie collective, les clubs thérapeutiques et la réunion soignants-soignés comme outils de soin.",
        "level": "Avancé",
        "explanation": "Elle lutte contre les effets nocifs de l'enfermement et de la hiérarchie rigide.",
        "tag": "Histoire / Soin"
    },
    {
        "q": "Quelle est la différence entre un effet Sédatif et un effet Anxiolytique ?",
        "options": [
            "Sédatif = Endort/Calme l'agitation. Anxiolytique = Apaise l'angoisse psychique",
            "Sédatif = Matin. Anxiolytique = Soir",
            "C'est la même chose",
            "Sédatif = Pour les enfants"
        ],
        "answer": "Sédatif = Endort/Calme l'agitation. Anxiolytique = Apaise l'angoisse psychique",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Certains neuroleptiques (Tercian, Loxapac) sont utilisés à visée sédative pour calmer une crise, même sans psychose.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Qu'est-ce que le programme de soins ambulatoires (soins sans consentement à domicile) ?",
        "type": "ouverte",
        "answer": "C'est une modalité légale qui permet d'obliger un patient à suivre son traitement et ses rendez-vous à l'extérieur de l'hôpital. En cas de non-respect, il peut être ré-hospitalisé.",
        "level": "Avancé",
        "explanation": "Cela permet de maintenir le lien thérapeutique pour des patients psychotiques qui arrêtent souvent leur traitement.",
        "tag": "Législation"
    },
    {
        "q": "Qu'est-ce que la Dyskinesie Tardive ?",
        "options": [
            "Un retard mental",
            "Des mouvements anormaux involontaires (mâchonnement, grimaces, mouvements des membres) apparaissant après un traitement prolongé par neuroleptiques, parfois irréversibles",
            "Une difficulté à marcher",
            "Une perte de la parole"
        ],
        "answer": "Des mouvements anormaux involontaires (mâchonnement, grimaces, mouvements des membres) apparaissant après un traitement prolongé par neuroleptiques, parfois irréversibles",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est la complication motrice à long terme la plus redoutée des neuroleptiques classiques.",
        "tag": "Thérapeutique / Psychomot"
    },
    {
        "q": "Qu'est-ce qu'un 'Raptus' ?",
        "options": [
            "Un dinosaure",
            "Une impulsion soudaine et violente conduisant à un passage à l'acte immédiat (suicidaire, agressif) sans préméditation apparente",
            "Un moment de joie",
            "Une fuite"
        ],
        "answer": "Une impulsion soudaine et violente conduisant à un passage à l'acte immédiat (suicidaire, agressif) sans préméditation apparente",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le raptus anxieux ou mélancolique est une urgence extrême.",
        "tag": "Urgence Psychiatrique"
    },
    {
        "q": "Pourquoi les hypnotiques (somnifères) de la famille des Z-drugs (Zolpidem) sont-ils apparentés aux Benzodiazépines ?",
        "type": "ouverte",
        "answer": "Ils agissent sur les mêmes récepteurs (GABA) et présentent les mêmes risques de dépendance et d'accoutumance, bien qu'ils soient vendus comme somnifères purs.",
        "level": "Avancé",
        "explanation": "Leur sevrage doit aussi être progressif.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Qu'est-ce que l'effet 'Anticholinergique' de certains psychotropes (bouche sèche, constipation, troubles de la vision) ?",
        "type": "ouverte",
        "answer": "C'est le blocage des récepteurs de l'acétylcholine (système parasympathique). Cela provoque une sécheresse des muqueuses, de la tachycardie, de la constipation et parfois de la confusion chez la personne âgée.",
        "level": "Avancé",
        "explanation": "C'est l'effet secondaire 'pénible' classique des vieux antidépresseurs et neuroleptiques.",
        "tag": "Thérapeutique"
    },
    {
        "q": "Dans le cadre de l'urgence psychiatrique, qu'est-ce que la CUMP ?",
        "options": [
            "Un médicament",
            "La Cellule d'Urgence Médico-Psychologique, déclenchée lors de catastrophes (attentats, accidents collectifs) pour une prise en charge immédiate des victimes (debriefing)",
            "Un centre de détention",
            "Une technique de massage"
        ],
        "answer": "La Cellule d'Urgence Médico-Psychologique, déclenchée lors de catastrophes (attentats, accidents collectifs) pour une prise en charge immédiate des victimes (debriefing)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le but est de prévenir l'apparition d'un état de stress post-traumatique (ESPT).",
        "tag": "Urgence"
    },
   
    ],

    "MODULE 6: Psychomotricité Théorique": [
        # DÉFINITIONS & HISTOIRE
        {
        "q": "Selon la définition générale, à quel croisement disciplinaire se situe la psychomotricité ?",
        "options": [
            "Entre le sport et la médecine",
            "Au croisement des disciplines biomédicales (anat/physio) et des sciences humaines (psycho/socio)",
            "Entre la kinésithérapie et l'ostéopathie",
            "Entre l'école et la maison"
        ],
        "answer": "Au croisement des disciplines biomédicales (anat/physio) et des sciences humaines (psycho/socio)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une profession 'bio-psycho-sociale'. Elle refuse de séparer le corps (organique) de l'esprit (psychique).",
        "tag": "Définition"
    },
    {
        "q": "Quels sont les 4 piliers du 'Paradigme Psychomoteur' cités dans votre cours ?",
        "options": [
            "Tête, Epaules, Genoux, Pieds",
            "Sensoriel, Cognitif, Motricité, Affectif",
            "Force, Vitesse, Endurance, Souplesse",
            "Manger, Bouger, Dormir, Parler"
        ],
        "answer": "Sensoriel, Cognitif, Motricité, Affectif",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le psychomotricien observe comment ces 4 dimensions s'articulent. Si l'une est touchée, les autres le sont aussi.",
        "tag": "Concept"
    },
    {
        "q": "Qui est considéré comme le 'père' de la psychomotricité française (création du premier diplôme en 1963) ?",
        "options": ["Sigmund Freud", "Julian de Ajuriaguerra", "Jean Piaget", "Françoise Dolto"],
        "answer": "Julian de Ajuriaguerra",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Neuropsychiatre d'origine basque, il a structuré la discipline à l'hôpital Henri Rousselle et créé l'école de la Pitié-Salpêtrière.",
        "tag": "Histoire"
    },
    {
        "q": "Quel texte législatif définit actuellement la liste des actes autorisés aux psychomotriciens ?",
        "options": [
            "Le Serment d'Hippocrate",
            "Le Décret de compétence n° 74-112 du 15 février 1974 (modifié)",
            "La Convention de Genève",
            "Le Code de la Route"
        ],
        "answer": "Le Décret de compétence n° 74-112 du 15 février 1974 (modifié)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est votre 'Bible' légale. Il stipule que les actes sont effectués sur prescription médicale.",
        "tag": "Législation"
    },
    {
        "q": "Qu'est-ce que le 'Tonus' en psychomotricité ?",
        "options": [
            "La force des biceps",
            "L'état de tension active des muscles au repos, toile de fond de l'action et des émotions",
            "La couleur de la peau",
            "La bonne humeur"
        ],
        "answer": "L'état de tension active des muscles au repos, toile de fond de l'action et des émotions",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il ne faut pas le confondre avec la force musculaire. On peut être très fort mais hypotonique, ou faible mais hypertonique (raide).",
        "tag": "Concept Tonus"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Quelle différence fondamentale faites-vous entre le 'Corps-Objet' et le 'Corps-Sujet' ?",
        "type": "ouverte",
        "answer": "Le Corps-Objet est le corps anatomique, 'avoir un corps' (vision médicale classique). Le Corps-Sujet est le corps vécu, ressenti, 'être son corps' (vision phénoménologique/psychomotrice).",
        "level": "Intermédiaire",
        "explanation": "Le psychomotricien travaille sur le Corps-Sujet. Il ne répare pas une mécanique, il aide une personne à habiter son corps.",
        "tag": "Philosophie"
    },
    {
        "q": "Que signifie le terme 'Instrumental' quand on parle de troubles instrumentaux ?",
        "options": [
            "Lié à la musique",
            "Lié aux outils de la pensée et de l'action (langage, geste, schéma corporel) qui permettent l'adaptation, sans déficit intellectuel global",
            "Lié à une paralysie",
            "Lié à la volonté"
        ],
        "answer": "Lié aux outils de la pensée et de l'action (langage, geste, schéma corporel) qui permettent l'adaptation, sans déficit intellectuel global",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "La dyspraxie est un trouble instrumental : l'intelligence est là, mais l'instrument 'corps/geste' dysfonctionne.",
        "tag": "Concept"
    },
    {
        "q": "Selon Dupré (début XXe), qu'est-ce que la 'Débilité Motrice' ?",
        "options": [
            "Une paralysie grave",
            "Un état pathologique congénital associant maladresse, hypertonie (paratonie) et syncinésies",
            "Une faiblesse musculaire",
            "Un retard mental profond"
        ],
        "answer": "Un état pathologique congénital associant maladresse, hypertonie (paratonie) et syncinésies",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un terme historique (aujourd'hui désuet) qui a fondé la psychomotricité en montrant le lien entre immaturité motrice et mentale.",
        "tag": "Histoire"
    },
    {
        "q": "Qu'est-ce qu'une 'Médiation' en séance de psychomotricité ?",
        "type": "ouverte",
        "answer": "C'est l'utilisation d'un objet (balle, cerceau), d'une matière (eau, argile) ou d'une technique (jeu, danse) comme tiers pour faciliter la relation et l'expression du patient.",
        "level": "Intermédiaire",
        "explanation": "La médiation permet d'éviter le face-à-face direct parfois angoissant et de détourner l'attention sur le 'faire'.",
        "tag": "Pratique"
    },
    {
        "q": "Qu'est-ce que la 'Dyspraxie' ?",
        "options": [
            "Un trouble de la parole",
            "Un trouble neurodéveloppemental de la planification et de l'automatisation des gestes volontaires (maladresse pathologique)",
            "Un trouble de la marche",
            "Une phobie du sport"
        ],
        "answer": "Un trouble neurodéveloppemental de la planification et de l'automatisation des gestes volontaires (maladresse pathologique)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est un trouble du 'comment faire'. L'enfant doit réfléchir à chaque étape d'un geste qui devrait être automatique (ex: lacer ses chaussures).",
        "tag": "Pathologie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Expliquez le concept de 'Dialogue Tonique' développé par Julian de Ajuriaguerra (et Wallon).",
        "type": "ouverte",
        "answer": "C'est un mode de communication infra-verbal, archaïque et émotionnel, qui passe par les variations de tension musculaire entre deux corps en relation (ex: mère-bébé, ou patient-thérapeute).",
        "level": "Avancé",
        "explanation": "Le corps de l'autre est ressenti comme accueillant (détente) ou rejetant (hypertonie). Le psychomotricien utilise son propre tonus pour apaiser le patient.",
        "tag": "Concept Clé"
    },
    {
        "q": "Quelle est la définition du 'Schéma Corporel' (SC) selon les auteurs classiques (Head, Schilder) ?",
        "options": [
            "L'image qu'on a de soi dans le miroir",
            "Une représentation neuro-physiologique tridimensionnelle de notre corps, construite par les afférences sensorielles, permettant de se repérer dans l'espace et de bouger",
            "Le dessin du bonhomme",
            "L'amour de son corps"
        ],
        "answer": "Une représentation neuro-physiologique tridimensionnelle de notre corps, construite par les afférences sensorielles, permettant de se repérer dans l'espace et de bouger",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le SC est une réalité de fait (neurobiologique). Il est le même pour tous (à peu près). C'est l'outil qui me permet de savoir où est ma main sans la regarder.",
        "tag": "Schéma Corporel"
    },
    {
        "q": "En quoi l'Image du Corps (IDC) diffère-t-elle radicalement du Schéma Corporel (SC) ?",
        "type": "ouverte",
        "answer": "L'IDC est subjective, inconsciente et éminemment relationnelle. Elle est liée à l'histoire affective du sujet, à ses désirs et ses blessures. Le SC est universel, l'IDC est propre à chacun.",
        "level": "Avancé",
        "explanation": "Dolto disait : 'Le schéma corporel est le même pour tous les individus de l'espèce humaine. L'image du corps est propre à chacun : elle est liée au sujet et à son histoire.'",
        "tag": "Image du Corps"
    },
    {
        "q": "Qu'est-ce que le 'Trouble Psychomoteur' selon la définition consensuelle ?",
        "options": [
            "Une maladie du muscle",
            "Un trouble neurodéveloppemental ou acquis affectant l'adaptation perceptivo-motrice de l'individu, avec une retentissement sur la relation à soi et à autrui",
            "Un problème psychiatrique pur",
            "Une simple maladresse"
        ],
        "answer": "Un trouble neurodéveloppemental ou acquis affectant l'adaptation perceptivo-motrice de l'individu, avec une retentissement sur la relation à soi et à autrui",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Il se manifeste par des signes 'mous' (soft signs) : paratonie, syncinésies, maladresse, instabilité... et non par des signes neurologiques durs (paralysie).",
        "tag": "Définition"
    },
    {
        "q": "Qu'est-ce que les 'Syncinésies' ?",
        "options": [
            "Des tics",
            "Des mouvements involontaires et parasites d'un groupe musculaire survenant lors de la réalisation d'un mouvement volontaire ailleurs (ex: tirer la langue en écrivant)",
            "Des mouvements coordonnés",
            "Des tremblements de repos"
        ],
        "answer": "Des mouvements involontaires et parasites d'un groupe musculaire survenant lors de la réalisation d'un mouvement volontaire ailleurs (ex: tirer la langue en écrivant)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elles sont normales chez le jeune enfant (immaturité) mais pathologiques si elles persistent (signe de débilité motrice ou de retard).",
        "tag": "Sémiologie"
    },
    {
        "q": "Pourquoi dit-on que la psychomotricité est une thérapie 'à médiation corporelle' ?",
        "type": "ouverte",
        "answer": "Parce qu'elle ne passe pas uniquement par la parole (verbal) mais engage le corps en mouvement et l'expérience sensorielle pour modifier le fonctionnement psychique.",
        "level": "Avancé",
        "explanation": "On part du corps pour soigner l'esprit ('Du corps au concept').",
        "tag": "Pratique"
    },
    {
        "q": "Selon Bullinger, qu'est-ce que l''Instrumentalisation' du corps ?",
        "options": [
            "Utiliser des outils",
            "Le processus par lequel l'enfant apprend à utiliser son corps comme un outil efficace pour agir sur le monde (passage du réflexe au volontaire)",
            "Jouer de la musique",
            "Se faire opérer"
        ],
        "answer": "Le processus par lequel l'enfant apprend à utiliser son corps comme un outil efficace pour agir sur le monde (passage du réflexe au volontaire)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est l'objectif du développement sensorimoteur : que le corps ne soit plus un obstacle mais un moyen.",
        "tag": "Développement"
    },
    {
        "q": "Qu'est-ce que la 'Paratonie' (signe essentiel en psychomotricité) ?",
        "type": "ouverte",
        "answer": "C'est une anomalie du tonus caractérisée par une impossibilité à obtenir un relâchement musculaire volontaire. Le patient se raidit dès qu'on le touche ou qu'on le mobilise (freinage tonique).",
        "level": "Avancé",
        "explanation": "C'est souvent le signe d'une anxiété corporelle ou d'un trouble de la relation.",
        "tag": "Sémiologie"
    },
    {
        "q": "Quel est le lien entre Tonus et Émotion selon la théorie de Wallon ?",
        "options": [
            "Aucun lien",
            "Le tonus est la substance de l'émotion : toute émotion est d'abord un événement tonique (hypertonie=colère/peur, hypotonie=bien-être/tristesse)",
            "L'émotion est dans la tête, le tonus dans les muscles",
            "Le tonus ne sert qu'à tenir debout"
        ],
        "answer": "Le tonus est la substance de l'émotion : toute émotion est d'abord un événement tonique (hypertonie=colère/peur, hypotonie=bien-être/tristesse)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Wallon dit : 'L'émotion est une variation du tonus'. C'est pourquoi relaxer le tonus peut apaiser l'émotion.",
        "tag": "Théorie Wallon"
    },
    {
        "q": "Qu'est-ce que l'Espace 'Kinesthésique' ?",
        "options": [
            "L'espace visuel",
            "L'espace interne ressenti par le mouvement de son propre corps (proprioception), sans forcément utiliser la vue",
            "L'espace de la salle de gym",
            "L'espace interplanétaire"
        ],
        "answer": "L'espace interne ressenti par le mouvement de son propre corps (proprioception), sans forcément utiliser la vue",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est le premier espace connu par le bébé (espace buccal, corporel) avant l'espace visuel lointain.",
        "tag": "Concept Espace"
    },
    {
        "q": "Qui est l'auteure de l'ouvrage de référence 'L'Image inconsciente du corps' ?",
        "options": ["Mélanie Klein", "Françoise Dolto", "Anna Freud", "Maria Montessori"],
        "answer": "Françoise Dolto",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elle a révolutionné la compréhension du corps en psychanalyse, montrant que le corps est le support du narcissisme et de l'histoire affective.",
        "tag": "Image du Corps"
    },
    {
        "q": "Le Schéma Corporel est-il identique pour tous ?",
        "options": [
            "Non, il dépend de l'humeur",
            "Oui, en tant que réalité neuro-anatomique de l'espèce (avoir deux bras, deux jambes), il est quasi identique pour tous",
            "Il dépend de la culture",
            "Il n'existe pas"
        ],
        "answer": "Oui, en tant que réalité neuro-anatomique de l'espèce (avoir deux bras, deux jambes), il est quasi identique pour tous",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'équipement de base. L'Image du Corps, elle, est unique à chacun.",
        "tag": "Schéma Corporel"
    },
    {
        "q": "Selon la métaphore de votre cours (De Vignemont), si l'Image du Corps est une 'peinture de la Renaissance' (riche, détaillée, émotionnelle), qu'est-ce que le Schéma Corporel ?",
        "options": [
            "Une sculpture",
            "Une esquisse anatomique au crayon ou une carte routière (précise, utile pour naviguer, sans fioritures)",
            "Un film",
            "Un roman"
        ],
        "answer": "Une esquisse anatomique au crayon ou une carte routière (précise, utile pour naviguer, sans fioritures)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le SC sert à l'action (naviguer). L'IDC sert à la contemplation et à l'identité.",
        "tag": "Concept"
    },
    {
        "q": "Le membre fantôme (sentir un bras amputé) est-il un trouble du Schéma Corporel ou de l'Image du Corps ?",
        "options": [
            "De l'Image du Corps",
            "Du Schéma Corporel (persistance de la représentation neurologique du membre malgré son absence physique)",
            "C'est une psychose",
            "C'est une invention"
        ],
        "answer": "Du Schéma Corporel (persistance de la représentation neurologique du membre malgré son absence physique)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Le cerveau n'a pas encore mis à jour la 'carte' neurologique. Il continue d'envoyer et de recevoir des signaux d'une zone vide.",
        "tag": "Neurologie"
    },
    {
        "q": "Lequel des deux est principalement inconscient selon Dolto ?",
        "options": ["Le Schéma Corporel", "L'Image du Corps", "Les deux", "Aucun"],
        "answer": "L'Image du Corps",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Bien qu'on puisse avoir conscience de son apparence (image spéculaire), l'Image du Corps profonde (liée aux castrations symboliques) est inconsciente.",
        "tag": "Image du Corps"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Paul Schilder (1935) est célèbre pour avoir...",
        "options": [
            "Découvert les neurones miroirs",
            "Unifié les approches neurologiques et psychanalytiques en définissant l'Image du Corps comme une structure tridimensionnelle, libidinale et sociale",
            "Inventé la relaxation",
            "Décrit l'autisme"
        ],
        "answer": "Unifié les approches neurologiques et psychanalytiques en définissant l'Image du Corps comme une structure tridimensionnelle, libidinale et sociale",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Son livre 'L'image du corps' est la bible du concept. Il insiste sur le fait que l'image du corps se construit au contact d'autrui.",
        "tag": "Histoire"
    },
    {
        "q": "Quelle est la différence fonctionnelle entre SC et IDC selon la métaphore Carte/Photo ?",
        "type": "ouverte",
        "answer": "Le Schéma Corporel (Carte) permet de naviguer et d'agir dans l'espace. L'Image du Corps (Photo) permet de se reconnaître, de s'identifier mais pas de piloter le mouvement.",
        "level": "Intermédiaire",
        "explanation": "On ne conduit pas une voiture en regardant une photo de la voiture. On la conduit grâce au schéma de la voiture intégré à notre corps.",
        "tag": "Concept"
    },
    {
        "q": "Dans l'anorexie mentale, quel est le trouble dominant ?",
        "options": [
            "Un trouble du Schéma Corporel (elle ne sait plus bouger)",
            "Un trouble de l'Image du Corps (dysmorphophobie : elle se voit et se sent énorme alors qu'elle est squelettique)",
            "Une paralysie",
            "Une cécité"
        ],
        "answer": "Un trouble de l'Image du Corps (dysmorphophobie : elle se voit et se sent énorme alors qu'elle est squelettique)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Son schéma corporel fonctionne (elle peut marcher, saisir), mais son image du corps est délirante.",
        "tag": "Pathologie"
    },
    {
        "q": "Qu'est-ce que la 'Cénesthésie' ?",
        "type": "ouverte",
        "answer": "C'est le sentiment global d'existence corporelle issu de la synthèse des sensations internes (viscérales, respiratoires, proprioceptives), souvent vague et diffus.",
        "level": "Intermédiaire",
        "explanation": "C'est le 'bruit de fond' du corps. Quand on va bien, on l'oublie (silence des organes). Quand on est malade, la cénesthésie devient pénible.",
        "tag": "Concept"
    },
    {
        "q": "Qui sont les premiers auteurs (neurologues) à avoir défini le Schéma Corporel vers 1911 ?",
        "options": ["Freud et Jung", "Head et Holmes", "Piaget et Wallon", "Broca et Wernicke"],
        "answer": "Head et Holmes",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Ils ont observé que des patients cérébrolésés perdaient la notion de la position de leurs membres. Ils ont théorisé le 'Postural Schema'.",
        "tag": "Histoire"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Selon Jacques Paillard, quelle est la distinction entre 'Corps identifié' et 'Corps situant' ?",
        "type": "ouverte",
        "answer": "Corps identifié = Image du Corps (référentiel allocentré, savoir 'ce que c'est'). Corps situant = Schéma Corporel (référentiel égocentré, savoir 'où c'est' pour agir).",
        "level": "Avancé",
        "explanation": "Cette distinction neurocognitive recoupe la différence SC/IDC. Deux circuits cérébraux différents (Voie du 'What' et voie du 'Where').",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Pour Françoise Dolto, comment le Schéma Corporel et l'Image du Corps évoluent-ils différemment ?",
        "options": [
            "Ils évoluent pareil",
            "Le Schéma Corporel est évolutif (grandit avec l'âge et l'apprentissage). L'Image du Corps est archaïque et peut rester figée (infantile) ou être en décalage",
            "Le Schéma Corporel est figé, l'Image du Corps change tout le temps",
            "L'Image du Corps meurt à l'adolescence"
        ],
        "answer": "Le Schéma Corporel est évolutif (grandit avec l'âge et l'apprentissage). L'Image du Corps est archaïque et peut rester figée (infantile) ou être en décalage",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "On peut avoir un corps d'adulte (SC) mais garder une image du corps de petit enfant dépendant.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Qu'est-ce que l'Asomatognosie ?",
        "type": "ouverte",
        "answer": "C'est la perte de la reconnaissance d'une partie de son propre corps. Le patient ignore son hémicorps paralysé (souvent gauche), refuse d'admettre qu'il lui appartient ('cette main n'est pas à moi').",
        "level": "Avancé",
        "explanation": "C'est une pathologie majeure du Schéma Corporel et de la conscience de soi (lésion pariétale).",
        "tag": "Pathologie"
    },
    {
        "q": "En quoi l'utilisation d'un outil (marteau, voiture, canne) modifie-t-elle le Schéma Corporel ?",
        "options": [
            "Elle ne change rien",
            "L'outil est incorporé au Schéma Corporel (assimilation fonctionnelle) : les limites du corps s'étendent jusqu'au bout de l'outil",
            "Elle détruit le schéma corporel",
            "Elle crée une image du corps fausse"
        ],
        "answer": "L'outil est incorporé au Schéma Corporel (assimilation fonctionnelle) : les limites du corps s'étendent jusqu'au bout de l'outil",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'aveugle 'sent' le trottoir au bout de sa canne, pas dans sa main. La canne est devenue une extension de son corps sensible.",
        "tag": "Neuroplasticité"
    },
    {
        "q": "Qu'est-ce que l'Image Spéculaire ?",
        "options": [
            "L'image mentale",
            "Le reflet du corps dans le miroir",
            "L'image des autres",
            "L'image radiologique"
        ],
        "answer": "Le reflet du corps dans le miroir",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Pour Dolto, l'image spéculaire (consciente) n'est que le 'couvercle' de l'image du corps (inconsciente). Avoir un beau reflet ne garantit pas une belle image du corps.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Selon Dolto, les 'Castrations symboligènes' (ombilicale, anale...) sont nécessaires pour...",
        "type": "ouverte",
        "answer": "Permettre la construction d'une Image du Corps saine et limitrophe. Chaque castration détache l'enfant d'une zone de fusion avec la mère et humanise son corps par le langage.",
        "level": "Avancé",
        "explanation": "Si la castration ne se fait pas (ex: mère gavage), l'image du corps reste incomplète ou trouée.",
        "tag": "Psychanalyse"
    },
    {
        "q": "Dans la perspective de Wallon, comment se construit le Schéma Corporel ?",
        "options": [
            "Par la génétique uniquement",
            "Par l'intégration progressive des données extéroceptives (monde), proprioceptives (soi) et intéroceptives (viscères), unifiées par l'émotion et le tonus",
            "Par le langage",
            "Par le dessin"
        ],
        "answer": "Par l'intégration progressive des données extéroceptives (monde), proprioceptives (soi) et intéroceptives (viscères), unifiées par l'émotion et le tonus",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Wallon insiste sur le fait que le corps se construit 'dans le rapport à l'autre'.",
        "tag": "Développement"
    },
    {
        "q": "Qu'est-ce que l'Héautoscopie ?",
        "type": "ouverte",
        "answer": "C'est une hallucination complexe où le sujet voit sa propre image corporelle projetée à l'extérieur de lui (voir son double), souvent de face.",
        "level": "Avancé",
        "explanation": "Phénomène rare (psychose, épilepsie temporale, expérience de mort imminente). Trouble extrême de l'Image du Corps.",
        "tag": "Psychopathologie"
    },
    {
        "q": "Pourquoi Gisela Pankow parle-t-elle de 'Corps vécu' dans la psychose ?",
        "options": [
            "Car le psychotique vit bien son corps",
            "Car chez le psychotique, le corps est souvent morcelé ou dissocié (trouble de la fonction symbolique du corps), et la thérapie vise à reconstruire ce corps vécu",
            "Car le corps est absent",
            "C'est un terme de sport"
        ],
        "answer": "Car chez le psychotique, le corps est souvent morcelé ou dissocié (trouble de la fonction symbolique du corps), et la thérapie vise à reconstruire ce corps vécu",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Elle utilise la pâte à modeler pour aider les patients à 'rassembler' les morceaux de leur image du corps.",
        "tag": "Thérapie"
    },
    {
        "q": "Quelle est la définition de la Somatognosie ?",
        "type": "ouverte",
        "answer": "C'est la connaissance (gnosie) et la conscience que l'on a de son propre corps et de ses parties, ainsi que de leur position dans l'espace.",
        "level": "Avancé",
        "explanation": "C'est un synonyme plus cognitif de Schéma Corporel. Les troubles sont des asomatognosies.",
        "tag": "Définition"
    },
    {
        "q": "Qu'est-ce que la Latéralité ?",
        "options": [
            "Savoir écrire de la main droite",
            "La prédominance fonctionnelle d'un hémicorps (droite ou gauche) sur l'autre, au niveau de la main, de l'œil, du pied et de l'oreille",
            "Être ambidextre",
            "Avoir deux mains gauches"
        ],
        "answer": "La prédominance fonctionnelle d'un hémicorps (droite ou gauche) sur l'autre, au niveau de la main, de l'œil, du pied et de l'oreille",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Elle traduit la spécialisation hémisphérique du cerveau. On est droitier si notre hémisphère gauche (moteur) est dominant.",
        "tag": "Latéralité"
    },
    {
        "q": "Qu'appelle-t-on une Latéralité 'Homogène' ?",
        "options": [
            "Être tout droitier (Main D, Œil D, Pied D) ou tout gaucher (Main G, Œil G, Pied G)",
            "Être droitier de la main et gaucher de l'œil",
            "Être ambidextre",
            "Changer de main tout le temps"
        ],
        "answer": "Être tout droitier (Main D, Œil D, Pied D) ou tout gaucher (Main G, Œil G, Pied G)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est la configuration la plus fréquente et la plus efficace sur le plan psychomoteur.",
        "tag": "Latéralité"
    },
    {
        "q": "En psychomotricité, l'Espace 'Topologique' (le premier acquis par l'enfant) concerne :",
        "options": [
            "Les distances métriques précises (cm, km)",
            "Les relations de voisinage, de séparation, d'ordre, d'enveloppement (Dedans/Dehors, Près/Loin) sans notion de mesure",
            "Les points cardinaux (Nord/Sud)",
            "La perspective"
        ],
        "answer": "Les relations de voisinage, de séparation, d'ordre, d'enveloppement (Dedans/Dehors, Près/Loin) sans notion de mesure",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est l'espace du vécu immédiat. 'Je suis DANS la maison', 'Le doudou est SUR le lit'. C'est un espace déformable (comme de la pâte à modeler).",
        "tag": "Espace"
    },
    {
        "q": "Qu'est-ce que le 'Rythme' ?",
        "options": [
            "La vitesse",
            "L'organisation structurée de la durée, caractérisée par la répétition périodique d'un événement (structure temporelle)",
            "Le fait d'être à l'heure",
            "Une danse"
        ],
        "answer": "L'organisation structurée de la durée, caractérisée par la répétition périodique d'un événement (structure temporelle)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La vie est rythmique (cœur, respiration, jour/nuit). Le trouble du rythme (arythmie) est souvent associé à la dyspraxie ou la dyslexie.",
        "tag": "Temps"
    },
    {
        "q": "Vers quel âge la latéralité manuelle est-elle généralement définitivement acquise et stable ?",
        "options": ["6 mois", "2 ans", "Vers 6-7 ans", "15 ans"],
        "answer": "Vers 6-7 ans",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Avant 4-5 ans, l'enfant peut encore fluctuer. À 6 ans (entrée au CP/écriture), le choix doit être fait.",
        "tag": "Développement"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce qu'une Latéralité 'Croisée' ?",
        "type": "ouverte",
        "answer": "C'est une discordance entre les différentes dominances latérales. Exemple classique : Droitier de la main mais Gaucher de l'œil (OGD).",
        "level": "Intermédiaire",
        "explanation": "Cela peut entraîner des difficultés d'apprentissage (lecture/tir de précision) mais ce n'est pas pathologique en soi. Nadal est droitier de la main au quotidien mais joue au tennis main gauche.",
        "tag": "Latéralité"
    },
    {
        "q": "Quelle est la différence entre l'Espace 'Vécu' et l'Espace 'Représenté' ?",
        "options": [
            "Vécu = agir dedans (sensorimoteur). Représenté = penser l'espace (mentalisation, plans, cartes)",
            "Vécu = Adulte. Représenté = Enfant",
            "Vécu = Dehors. Représenté = Dedans",
            "C'est pareil"
        ],
        "answer": "Vécu = agir dedans (sensorimoteur). Représenté = penser l'espace (mentalisation, plans, cartes)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "L'enfant passe du corps (je bouge) à l'action (je manipule) puis à la pensée (je visualise le trajet).",
        "tag": "Concept Espace"
    },
    {
        "q": "Qu'est-ce qu'une Latéralité 'Contrariée' ?",
        "type": "ouverte",
        "answer": "C'est une latéralité qui a été modifiée par une influence extérieure (éducation, accident). Ex: un gaucher génétique forcé d'écrire de la main droite.",
        "level": "Intermédiaire",
        "explanation": "Cela provoquait autrefois des bégaiements et des troubles de l'écriture. Aujourd'hui, on respecte la main spontanée.",
        "tag": "Latéralité"
    },
    {
        "q": "Qu'est-ce que l'Orientation Temporelle ?",
        "options": [
            "Savoir lire l'heure",
            "La capacité à se situer dans la chronologie (Passé, Présent, Futur) et à utiliser les repères conventionnels (jours, mois, heures)",
            "Avoir le sens du rythme",
            "Savoir courir vite"
        ],
        "answer": "La capacité à se situer dans la chronologie (Passé, Présent, Futur) et à utiliser les repères conventionnels (jours, mois, heures)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est une acquisition cognitive tardive. Le jeune enfant vit dans un 'éternel présent'.",
        "tag": "Temps"
    },
    {
        "q": "Dans le développement spatial, qu'est-ce que l'Espace 'Projectif' (Piaget) ?",
        "options": [
            "L'espace des rêves",
            "L'apparition de la notion de point de vue et de perspective. L'objet n'est plus isolé, il est situé PAR RAPPORT à un autre ou à soi (devant, derrière, à gauche de...)",
            "L'espace métrique",
            "L'espace tactile"
        ],
        "answer": "L'apparition de la notion de point de vue et de perspective. L'objet n'est plus isolé, il est situé PAR RAPPORT à un autre ou à soi (devant, derrière, à gauche de...)",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est la sortie de l'égocentrisme spatial. L'enfant comprend que ce qui est à SA gauche peut être à LA droite de la personne en face.",
        "tag": "Espace"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que l'Ambidextrie réelle (et non la mal-latéralisation) ?",
        "type": "ouverte",
        "answer": "C'est la capacité rare d'utiliser les deux mains avec la même efficacité et la même précision pour des tâches complexes (écriture, outils).",
        "level": "Avancé",
        "explanation": "Souvent, ce qu'on appelle ambidextrie est en fait une 'ambigüité latérale' (l'enfant est maladroit des deux mains ou change selon la fatigue), ce qui est un signe d'immaturité.",
        "tag": "Latéralité"
    },
    {
        "q": "En psychomotricité, qu'est-ce que la 'Structuration Temporelle' ?",
        "options": [
            "L'agenda du patient",
            "La capacité d'organiser ses actions dans une succession logique (séquençage), de percevoir la durée et d'ajuster son mouvement à une cadence extérieure (synchronisation)",
            "La mémoire des dates",
            "Le sommeil"
        ],
        "answer": "La capacité d'organiser ses actions dans une succession logique (séquençage), de percevoir la durée et d'ajuster son mouvement à une cadence extérieure (synchronisation)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Un enfant dyspraxique a souvent du mal à séquencer (s'habiller dans l'ordre) et à se synchroniser (danser en rythme).",
        "tag": "Temps"
    },
    {
        "q": "Quel est le dernier stade de l'espace selon Piaget, permettant la géométrie ?",
        "options": [
            "L'espace Buccal",
            "L'espace Euclidien (Métrique)",
            "L'espace Topologique",
            "L'espace Projectif"
        ],
        "answer": "L'espace Euclidien (Métrique)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Il introduit la conservation des longueurs, des surfaces et des volumes, et l'utilisation d'un système de coordonnées fixes (axes X, Y, Z) indépendant du sujet.",
        "tag": "Espace"
    },
    {
        "q": "Qu'est-ce que la 'Notion de Corps Propre' (Zazzo) ?",
        "type": "ouverte",
        "answer": "C'est la conscience d'être soi-même, distinct de l'autre, unifié et situé dans l'espace. Elle est le fruit de l'intégration du schéma corporel et de l'image du corps.",
        "level": "Avancé",
        "explanation": "C'est le socle de l'identité. Sans corps propre bien défini, l'espace environnant est angoissant (espace indifférencié de la psychose).",
        "tag": "Concept"
    },
    {
        "q": "Pourquoi tester l'œil directeur est-il important en bilan psychomoteur ?",
        "options": [
            "Pour prescrire des lunettes",
            "Pour vérifier l'homogénéité de la latéralité. Un œil directeur croisé par rapport à la main (ex: Oeil G / Main D) peut gêner l'apprentissage de la lecture/écriture (balayage visuel)",
            "Pour voir s'il est daltonien",
            "Ça ne sert à rien"
        ],
        "answer": "Pour vérifier l'homogénéité de la latéralité. Un œil directeur croisé par rapport à la main (ex: Oeil G / Main D) peut gêner l'apprentissage de la lecture/écriture (balayage visuel)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "On teste l'œil directeur avec le test du trou dans la feuille (viseur). L'œil qui s'aligne spontanément est le directeur.",
        "tag": "Bilan"
    },
    {
        "q": "Qu'est-ce que le 'Temps Subjectif' vs 'Temps Objectif' ?",
        "type": "ouverte",
        "answer": "Temps Subjectif : la durée ressentie (l'ennui allonge le temps, le plaisir le raccourcit). Temps Objectif : le temps de l'horloge, social, mesurable et constant.",
        "level": "Avancé",
        "explanation": "En pathologie (dépression), le temps subjectif est ralenti ('ça ne passe jamais'). En manie, il est accéléré.",
        "tag": "Temps"
    },
    {
        "q": "Qu'est-ce que l'Espace 'Proximal' vs 'Distal' ?",
        "options": [
            "Proximal = Loin, Distal = Près",
            "Proximal = Espace de préhension (à portée de main). Distal = Espace locomoteur (hors d'atteinte, nécessite un déplacement)",
            "Proximal = Espace visuel. Distal = Espace auditif",
            "C'est de l'anatomie"
        ],
        "answer": "Proximal = Espace de préhension (à portée de main). Distal = Espace locomoteur (hors d'atteinte, nécessite un déplacement)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le bébé conquiert d'abord l'espace proximal (manipulation) avant de conquérir l'espace distal par la marche.",
        "tag": "Espace"
    },
    {
        "q": "Expliquez le lien entre Latéralisation et Organisation Spatiale.",
        "type": "ouverte",
        "answer": "La latéralisation donne à l'enfant un axe de référence corporel stable (sa propre Gauche/Droite). C'est à partir de cet axe qu'il peut orienter l'espace extérieur (la gauche de la feuille, la droite de la route).",
        "level": "Avancé",
        "explanation": "Si la latéralité est floue, l'orientation spatiale est souvent déficitaire (confusion b/d, p/q, inversions en lecture).",
        "tag": "Développement"
    },
    {
        "q": "Qu'est-ce que le 'Temps Vécu' (Minkowski) ?",
        "options": [
            "Le temps passé",
            "La dimension qualitative du temps, liée à l'élan vital et à la projection vers l'avenir (devenir)",
            "Le temps de l'horloge",
            "L'heure du repas"
        ],
        "answer": "La dimension qualitative du temps, liée à l'élan vital et à la projection vers l'avenir (devenir)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Pour Minkowski, la santé mentale est la capacité à se projeter dans l'avenir. Le dépressif est 'figé' dans le passé ou le présent douloureux.",
        "tag": "Phénoménologie"
    },
    {
        "q": "Qu'est-ce que l'Agnosie Digitale ?",
        "type": "ouverte",
        "answer": "C'est l'incapacité à reconnaître, nommer ou distinguer ses propres doigts ou ceux de l'examinateur. Elle fait partie du Syndrome de Gerstmann (avec acalculie, indistinction droite/gauche, agraphie).",
        "level": "Avancé",
        "explanation": "Cela montre le lien étroit entre la connaissance du corps (les doigts) et des fonctions cognitives complexes comme le calcul (compter sur ses doigts).",
        "tag": "Neuropsychologie"
    },
    {
        "q": "Quelle est la Loi 'Céphalo-Caudale' du développement moteur ?",
        "options": [
            "Le développement se fait des pieds vers la tête",
            "Le contrôle tonique et moteur se développe de la tête vers les pieds (Tête -> Dos -> Bassin -> Jambes)",
            "Le développement se fait du centre vers les mains",
            "Le développement est aléatoire"
        ],
        "answer": "Le contrôle tonique et moteur se développe de la tête vers les pieds (Tête -> Dos -> Bassin -> Jambes)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est pourquoi le bébé tient sa tête (3 mois) avant de tenir assis (6-8 mois) et de marcher (12-15 mois).",
        "tag": "Loi de Développement"
    },
    {
        "q": "À quel âge un enfant acquiert-il généralement la marche autonome (sans aide) ?",
        "options": ["6 mois", "9 mois", "Entre 12 et 15 mois", "24 mois"],
        "answer": "Entre 12 et 15 mois",
        "type": "qcm",
        "level": "Basique",
        "explanation": "La fourchette normale est large (10 à 18 mois). Au-delà de 18-20 mois sans marche, on s'inquiète.",
        "tag": "Développement Moteur"
    },
    {
        "q": "Qu'est-ce qu'un Réflexe Archaïque (ou Primaire) ?",
        "options": [
            "Un réflexe acquis par l'apprentissage",
            "Un mouvement involontaire et automatique présent à la naissance, témoignant de la maturation du tronc cérébral, qui doit disparaître (s'intégrer) pour laisser place à la motricité volontaire",
            "Un réflexe de peur",
            "Un hoquet"
        ],
        "answer": "Un mouvement involontaire et automatique présent à la naissance, témoignant de la maturation du tronc cérébral, qui doit disparaître (s'intégrer) pour laisser place à la motricité volontaire",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Exemples : Grasping, Moro, Marche automatique. S'ils persistent trop longtemps, ils parasitent le développement.",
        "tag": "Neurologie Développementale"
    },
    {
        "q": "Quelle est la Loi 'Proximo-Distale' ?",
        "options": [
            "Le contrôle moteur se développe du centre du corps (axe) vers les extrémités (mains/doigts)",
            "Le contrôle se fait des doigts vers l'épaule",
            "Le contrôle se fait de la tête aux pieds",
            "Le contrôle se fait de droite à gauche"
        ],
        "answer": "Le contrôle moteur se développe du centre du corps (axe) vers les extrémités (mains/doigts)",
        "type": "qcm",
        "level": "Basique",
        "explanation": "L'enfant maîtrise son épaule, puis son coude, puis son poignet, et enfin ses doigts (motricité fine).",
        "tag": "Loi de Développement"
    },
    {
        "q": "Qu'est-ce que le 'Grasping' (Réflexe d'agrippement) ?",
        "options": [
            "L'enfant rejette ce qu'on lui donne",
            "La fermeture automatique et très forte de la main lorsqu'on stimule la paume",
            "L'enfant suce son pouce",
            "L'enfant tourne la tête"
        ],
        "answer": "La fermeture automatique et très forte de la main lorsqu'on stimule la paume",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un réflexe de survie (s'accrocher à la fourrure de la mère chez le primate). Il disparaît vers 3-4 mois pour permettre la préhension volontaire.",
        "tag": "Réflexes"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "À quel âge apparaît la 'Pince Inférieure' (pince pouce-index maladroite ou 'en râteau') ?",
        "options": ["3 mois", "6-7 mois", "9-10 mois", "2 ans"],
        "answer": "6-7 mois",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est le début de l'utilisation du pouce. La pince fine supérieure (très précise) arrive vers 9-10 mois.",
        "tag": "Motricité Fine"
    },
    {
        "q": "Qu'est-ce que le 'Réflexe de Moro' ?",
        "type": "ouverte",
        "answer": "C'est une réaction d'extension brutale des bras et d'ouverture des mains (suivie d'un cri) en réponse à une sensation de chute arrière ou à un bruit fort.",
        "level": "Intermédiaire",
        "explanation": "C'est un réflexe de défense/alerte. Son absence à la naissance est inquiétante (hypotonie, lésion).",
        "tag": "Réflexes"
    },
    {
        "q": "Qu'est-ce que le niveau d'évolution motrice 'ramper' et quand survient-il ?",
        "options": [
            "Se déplacer sur les fesses (8 mois)",
            "Se déplacer à plat ventre par traction des bras (reptation), vers 7-9 mois, avant le quatre pattes",
            "Se déplacer debout",
            "Rouler sur le côté"
        ],
        "answer": "Se déplacer à plat ventre par traction des bras (reptation), vers 7-9 mois, avant le quatre pattes",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est la première forme de déplacement autonome au sol (le commando).",
        "tag": "Développement Moteur"
    },
    {
        "q": "Qu'est-ce que le 'Tonus de fond' vs 'Tonus d'action' ?",
        "type": "ouverte",
        "answer": "Tonus de fond : tension passive au repos (testée par le ballant). Tonus d'action : tension active nécessaire pour réaliser un mouvement ou une posture.",
        "level": "Intermédiaire",
        "explanation": "Chez le bébé, le tonus de fond est hypotonique (mou) au niveau de l'axe au début, alors que les membres sont hypertoniques.",
        "tag": "Concept Tonus"
    },
    {
        "q": "Qu'appelle-t-on la 'Position du Chevalier Servant' dans le développement ?",
        "options": [
            "Une position de yoga",
            "L'étape intermédiaire pour se relever : un genou à terre, l'autre pied à plat, pour passer du sol à la position debout",
            "La position assise",
            "La marche à reculons"
        ],
        "answer": "L'étape intermédiaire pour se relever : un genou à terre, l'autre pied à plat, pour passer du sol à la position debout",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "Elle nécessite un bon équilibre et une dissociation des ceintures. Elle précède la marche autonome.",
        "tag": "Développement Moteur"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que le RTAC (Réflexe Tonique Asymétrique du Cou) ou 'Position de l'Escrimeur' ?",
        "type": "ouverte",
        "answer": "Quand on tourne la tête du bébé d'un côté, le bras du côté visage s'étend et le bras côté crâne se fléchit.",
        "level": "Avancé",
        "explanation": "Ce réflexe est crucial pour la coordination œil-main (le bébé regarde sa main tendue). S'il persiste, il empêche l'écriture et le croisement de la ligne médiane.",
        "tag": "Réflexes"
    },
    {
        "q": "Selon André Bullinger, quels sont les deux temps de la construction de l'espace moteur ?",
        "options": [
            "Le temps du rêve et le temps de l'action",
            "Le temps du Rassemblement (sensation du dos, appuis, axe) et le temps du Déploiement (exploration, préhension)",
            "Le temps de la marche et de la course",
            "Le temps de la main et du pied"
        ],
        "answer": "Le temps du Rassemblement (sensation du dos, appuis, axe) et le temps du Déploiement (exploration, préhension)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "L'enfant doit d'abord sentir ses appuis postérieurs (dos) pour pouvoir libérer ses mains vers l'avant. 'Sans appui, pas de mouvement'.",
        "tag": "Théorie Bullinger"
    },
    {
        "q": "Qu'est-ce que la 'Loi de Différenciation' ?",
        "type": "ouverte",
        "answer": "La motricité passe d'une activité globale, diffuse et involontaire (tout le corps bouge quand on est content) à une activité localisée, fine et adaptée.",
        "level": "Avancé",
        "explanation": "Au début, le bébé bouge tout le bras pour attraper. À la fin, il ne bouge que le bout des doigts.",
        "tag": "Loi de Développement"
    },
    {
        "q": "Qu'est-ce que la 'Dissociation des ceintures' ?",
        "options": [
            "Enlever sa ceinture",
            "La capacité (acquise lors de la marche et du ramper) à tourner les épaules dans un sens et le bassin dans l'autre (marche croisée)",
            "Séparer le haut et le bas du corps en le coupant",
            "Avoir mal au dos"
        ],
        "answer": "La capacité (acquise lors de la marche et du ramper) à tourner les épaules dans un sens et le bassin dans l'autre (marche croisée)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Indispensable pour la fluidité de la marche. Si l'enfant marche 'en bloc' (comme un robot), il n'y a pas de dissociation.",
        "tag": "Psychomotricité"
    },
    {
        "q": "Qu'est-ce que le 'Relâchement volontaire' (Manœuvre de la Poupée) ?",
        "type": "ouverte",
        "answer": "C'est la capacité de l'enfant à laisser ses membres mous (passifs) quand l'examinateur les mobilise. C'est un signe de maturité neurologique et de confiance.",
        "level": "Avancé",
        "explanation": "L'enfant paratonique (débilité motrice) ne peut pas se relâcher, il résiste ou aide le mouvement malgré lui.",
        "tag": "Bilan"
    },
    {
        "q": "Quelle est l'évolution de la Préhension selon Halverson (les 3 temps) ?",
        "options": [
            "Cubito-palmaire -> Radio-palmaire -> Radio-digitale",
            "Digitale -> Palmaire -> Cubitale",
            "Bouche -> Main -> Pied",
            "Gauche -> Droite -> Milieu"
        ],
        "answer": "Cubito-palmaire -> Radio-palmaire -> Radio-digitale",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "D'abord on attrape avec le côté du petit doigt (cubital), puis avec la paume, puis avec le pouce et l'index (radial/digital) qui est le plus précis.",
        "tag": "Motricité Fine"
    },
    {
        "q": "Qu'est-ce que le 'Dialogue Tonico-Émotionnel' dans le développement ?",
        "type": "ouverte",
        "answer": "C'est l'ajustement réciproque des tensions musculaires entre la mère et l'enfant lors du portage. Un bon ajustement crée un sentiment de sécurité (holding).",
        "level": "Avancé",
        "explanation": "Si la mère est raide (hypertonique) ou absente (hypotonique), le bébé réagit par des troubles toniques ou du comportement.",
        "tag": "Concept Wallon"
    },
    {
        "q": "Qu'est-ce que l'Hypotonie Axiale physiologique du nouveau-né ?",
        "options": [
            "Une maladie grave",
            "L'état normal à la naissance : le dos et le cou sont mous (ne tiennent pas), alors que les membres sont fléchis et raides (Hypertonie périphérique)",
            "Le bébé est tout mou partout",
            "Le bébé est tout raide partout"
        ],
        "answer": "L'état normal à la naissance : le dos et le cou sont mous (ne tiennent pas), alors que les membres sont fléchis et raides (Hypertonie périphérique)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le développement va consister à inverser cela : tonifier l'axe (pour tenir debout) et détendre les membres (pour attraper).",
        "tag": "Neurologie Développementale"
    },
    {
        "q": "Qu'est-ce que la 'Marche Automatique' ?",
        "type": "ouverte",
        "answer": "Un réflexe archaïque : si on tient le nouveau-né debout penché en avant, il fait des pas alternés. Ce réflexe disparaît vers 2 mois (phase abasique) avant la vraie marche volontaire.",
        "level": "Avancé",
        "explanation": "Si elle persiste anormalement, c'est un signe neurologique suspect (IMC).",
        "tag": "Réflexes"
    },
    {
        "q": "Qu'est-ce que la 'Réaction Parachute' ?",
        "options": [
            "La peur du vide",
            "Un réflexe de protection (vers 7-9 mois) : si on projette l'enfant vers l'avant, il étend ses bras pour se recevoir et protéger sa tête",
            "Sauter d'une chaise",
            "Fermer les yeux"
        ],
        "answer": "Un réflexe de protection (vers 7-9 mois) : si on projette l'enfant vers l'avant, il étend ses bras pour se recevoir et protéger sa tête",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un réflexe 'définitif' (il reste à vie). Indispensable pour ne pas se blesser en marchant.",
        "tag": "Réflexes"
    },
    {
        "q": "Quel est l'objectif principal du Bilan Psychomoteur ?",
        "options": [
            "Donner une note à l'enfant",
            "Évaluer les compétences et les difficultés psychomotrices du patient pour poser un diagnostic et élaborer un projet thérapeutique",
            "Voir si l'enfant est intelligent",
            "Prescrire des médicaments"
        ],
        "answer": "Évaluer les compétences et les difficultés psychomotrices du patient pour poser un diagnostic et élaborer un projet thérapeutique",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est un acte fondateur. Il comprend l'entretien, les tests standardisés et l'observation clinique.",
        "tag": "Bilan"
    },
    {
        "q": "En relaxation, quelle est la méthode 'Schultz' (Training Autogène) ?",
        "options": [
            "La contraction musculaire forte",
            "L'induction par la pensée de sensations de pesanteur (lourdeur) et de chaleur dans le corps",
            "La respiration rapide",
            "Le massage"
        ],
        "answer": "L'induction par la pensée de sensations de pesanteur (lourdeur) et de chaleur dans le corps",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une méthode d'auto-hypnose centrée sur le ressenti interne et vasculaire.",
        "tag": "Relaxation"
    },
    {
        "q": "Quelle est la fonction principale du 'Jeu Symbolique' (faire semblant) chez l'enfant ?",
        "options": [
            "Perdre du temps",
            "Assimiler le réel au moi, exprimer ses conflits et désirs, et développer sa capacité de représentation",
            "Apprendre à compter",
            "Muscler ses doigts"
        ],
        "answer": "Assimiler le réel au moi, exprimer ses conflits et désirs, et développer sa capacité de représentation",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Quand l'enfant joue au docteur, il inverse les rôles pour maîtriser sa peur de la piqûre. C'est cathartique.",
        "tag": "Jeu"
    },
    {
        "q": "Qu'est-ce que le test M-ABC 2 (Movement Assessment Battery for Children) ?",
        "options": [
            "Un test de lecture",
            "Un test de référence pour diagnostiquer le TDC (Trouble du Développement de la Coordination) ou dyspraxie",
            "Un test de QI",
            "Un test de vision"
        ],
        "answer": "Un test de référence pour diagnostiquer le TDC (Trouble du Développement de la Coordination) ou dyspraxie",
        "type": "qcm",
        "level": "Basique",
        "explanation": "Il évalue la dextérité manuelle, l'équilibre et la visée-attrape.",
        "tag": "Bilan - Tests"
    },
    {
        "q": "Quelle est la méthode de relaxation 'Jacobson' ?",
        "options": [
            "L'hypnose",
            "La relaxation progressive basée sur le contraste entre contraction musculaire forte et relâchement soudain",
            "Le yoga",
            "La sophrologie"
        ],
        "answer": "La relaxation progressive basée sur le contraste entre contraction musculaire forte et relâchement soudain",
        "type": "qcm",
        "level": "Basique",
        "explanation": "C'est une approche physiologique et périphérique, idéale pour ceux qui ont du mal à 'lâcher prise' mentalement.",
        "tag": "Relaxation"
    },

    # --- NIVEAU INTERMÉDIAIRE (25%) ---
    {
        "q": "Qu'est-ce que le BHK (Brazelton) ?",
        "options": [
            "Un test de marche",
            "Une échelle d'évaluation rapide de l'écriture (qualité et vitesse) pour dépister la dysgraphie",
            "Un test de dessin",
            "Un test de mémoire"
        ],
        "answer": "Une échelle d'évaluation rapide de l'écriture (qualité et vitesse) pour dépister la dysgraphie",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "L'enfant doit copier un texte standard pendant 5 minutes. On compte les fautes et la longueur.",
        "tag": "Bilan - Tests"
    },
    {
        "q": "Selon Winnicott, quelle est la différence entre le 'Game' et le 'Play' ?",
        "type": "ouverte",
        "answer": "Le 'Game' est le jeu à règles, social et organisé. Le 'Play' est le jeu libre, créatif, transitionnel, où l'enfant déploie son imaginaire sans contrainte.",
        "level": "Intermédiaire",
        "explanation": "En thérapie, on cherche souvent à ramener l'enfant vers le 'Play' (capacité à jouer) avant de le confronter au 'Game'.",
        "tag": "Théorie du Jeu"
    },
    {
        "q": "Qu'est-ce que la Figure de Rey (Figure Complexe) ?",
        "options": [
            "Une danse",
            "Un test de copie de figure géométrique complexe qui évalue les capacités visuo-spatiales, la planification et la mémoire visuelle",
            "Un test de personnalité",
            "Un test de lecture"
        ],
        "answer": "Un test de copie de figure géométrique complexe qui évalue les capacités visuo-spatiales, la planification et la mémoire visuelle",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "On regarde COMMENT l'enfant copie (par le cadre global ou par les détails). C'est très révélateur des stratégies cognitives.",
        "tag": "Bilan - Tests"
    },
    {
        "q": "Quelle est la particularité de la méthode de relaxation 'Soubiran' (Psychomotrice) ?",
        "type": "ouverte",
        "answer": "Elle est active et en mouvement (mobilisations passives, balancements). Elle permet au patient de sentir ses limites corporelles et son tonus sans passer par l'immobilité angoissante.",
        "level": "Intermédiaire",
        "explanation": "Créée par une psychomotricienne pour des patients qui ne supportent pas le Schultz (trop régressif).",
        "tag": "Relaxation"
    },
    {
        "q": "Dans un test standardisé, qu'est-ce que l'Écart-Type (Standard Deviation) ?",
        "options": [
            "Une erreur de calcul",
            "Une mesure de la dispersion des scores par rapport à la moyenne. Un score à -2 Écarts-Types (ET) signe généralement un trouble pathologique",
            "La note moyenne",
            "Le temps total"
        ],
        "answer": "Une mesure de la dispersion des scores par rapport à la moyenne. Un score à -2 Écarts-Types (ET) signe généralement un trouble pathologique",
        "type": "qcm",
        "level": "Intermédiaire",
        "explanation": "C'est la base de la psychométrie. Entre -1 et +1 ET, on est dans la moyenne.",
        "tag": "Psychométrie"
    },

    # --- NIVEAU AVANCÉ (50%) ---
    {
        "q": "Qu'est-ce que le 'Jeu Sensorimoteur' et pourquoi est-il thérapeutique ?",
        "type": "ouverte",
        "answer": "C'est le jeu centré sur le plaisir du mouvement, des sensations fortes (sauter, chuter, tourner, se cacher). Il permet de réassurer l'enveloppe corporelle et de vivre le plaisir d'être cause (sentiment d'agence).",
        "level": "Avancé",
        "explanation": "C'est la base de la thérapie Aucouturier (Pratique Psychomotrice). On rejoue les archaïsmes pour les dépasser.",
        "tag": "Thérapie"
    },
    {
        "q": "Qu'est-ce que le NP-MOT (Vaivre-Douret) ?",
        "options": [
            "Un médicament",
            "Une batterie d'évaluation des fonctions Neuro-Psychomotrices de l'enfant (tonus, latéralité, gnosies, praxies, rythme)",
            "Un test de QI",
            "Un test de sport"
        ],
        "answer": "Une batterie d'évaluation des fonctions Neuro-Psychomotrices de l'enfant (tonus, latéralité, gnosies, praxies, rythme)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "C'est un outil très complet et spécifiquement français pour le bilan psychomoteur.",
        "tag": "Bilan - Tests"
    },
    {
        "q": "Quelle est la contre-indication majeure à la relaxation (type Schultz/Hypnose) ?",
        "options": [
            "L'asthme",
            "Les états psychotiques aigus ou décompensés (risque de bouffée délirante ou d'angoisse de morcellement par perte des limites corporelles)",
            "Le mal de dos",
            "L'hypertension"
        ],
        "answer": "Les états psychotiques aigus ou décompensés (risque de bouffée délirante ou d'angoisse de morcellement par perte des limites corporelles)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Faire fermer les yeux à un paranoïaque ou un schizophrène peut être vécu comme une menace terrible.",
        "tag": "Relaxation"
    },
    {
        "q": "Qu'est-ce que l'Étalonnage d'un test ?",
        "type": "ouverte",
        "answer": "C'est la table de conversion qui permet de transformer le score brut du patient (ex: 25 points) en score standard comparé à une population de même âge (ex: percentile 10).",
        "level": "Avancé",
        "explanation": "Sans étalonnage récent et valide, un test ne vaut rien.",
        "tag": "Psychométrie"
    },
    {
        "q": "Qu'est-ce que le 'Wintrebert' ?",
        "options": [
            "Un gâteau",
            "Une méthode de relaxation pour enfant utilisant les mobilisations passives et la comparaison 'poupée de chiffon' / 'poupée de bois'",
            "Un test de lecture",
            "Une danse"
        ],
        "answer": "Une méthode de relaxation pour enfant utilisant les mobilisations passives et la comparaison 'poupée de chiffon' / 'poupée de bois'",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Permet d'aborder la régulation tonique de façon ludique et concrète.",
        "tag": "Relaxation"
    },
    {
        "q": "Dans le bilan, quelle est la différence entre 'Performance' et 'Compétence' ?",
        "type": "ouverte",
        "answer": "Performance = Le résultat chiffré au test (ce qu'il a fait). Compétence = Le potentiel réel de l'enfant (ce qu'il peut faire).",
        "level": "Avancé",
        "explanation": "Un enfant stressé ou opposant peut avoir une mauvaise performance (échec au test) mais une compétence intacte. L'observation clinique sert à faire la part des choses.",
        "tag": "Concept Bilan"
    },
    {
        "q": "Qu'est-ce que la NEPSY-II ?",
        "options": [
            "Un soda",
            "Une batterie complète d'évaluation neuropsychologique de l'enfant (Attention, Mémoire, Langage, Fonctions Exécutives, Visuo-spatial)",
            "Un test de marche",
            "Un questionnaire parents"
        ],
        "answer": "Une batterie complète d'évaluation neuropsychologique de l'enfant (Attention, Mémoire, Langage, Fonctions Exécutives, Visuo-spatial)",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le psychomotricien utilise souvent les subtests 'Visuo-spatial' et 'Sensorimoteur' de la NEPSY.",
        "tag": "Bilan - Tests"
    },
    {
        "q": "Qu'est-ce que l'Espace Transitionnel de Jeu (Winnicott) ?",
        "type": "ouverte",
        "answer": "C'est un espace intermédiaire entre le dedans (réalité psychique) et le dehors (réalité extérieure). C'est le lieu de la créativité et de la culture, où la question 'est-ce vrai ou faux ?' ne se pose pas.",
        "level": "Avancé",
        "explanation": "La séance de psychomotricité doit être un espace transitionnel où l'on peut 'jouer' ses difficultés sans danger.",
        "tag": "Théorie du Jeu"
    },
    {
        "q": "En relaxation Sapir, quel est le rôle de l'induction verbale (la voix du thérapeute) ?",
        "options": [
            "Donner des ordres",
            "Accompagner la sensation, faire liaison et enveloppe sonore pour contenir l'angoisse du patient",
            "Endormir le patient",
            "Raconter une histoire"
        ],
        "answer": "Accompagner la sensation, faire liaison et enveloppe sonore pour contenir l'angoisse du patient",
        "type": "qcm",
        "level": "Avancé",
        "explanation": "Le ton, le rythme et la prosodie (musique de la voix) comptent autant que les mots.",
        "tag": "Relaxation"
    },
    {
        "q": "Pourquoi observe-t-on la 'Qualité du geste' (fluidité, mélodie kinétique) et pas seulement la réussite de la tâche ?",
        "type": "ouverte",
        "answer": "Parce qu'un enfant peut réussir la tâche par compensation intellectuelle ou force, mais avec un coût attentionnel énorme et une raideur pathologique. La dyspraxie se voit souvent dans le 'comment' plus que dans le 'combien'.",
        "level": "Avancé",
        "explanation": "C'est la spécificité du regard du psychomotricien par rapport à un score d'ordinateur.",
        "tag": "Clinique"
    },
    ]
}

# =========================================================
# ⚙️ MOTEUR INTELLIGENT (ALÉATOIRE & SUIVI & SAUVEGARDE)
# =========================================================

# --- GESTION DE L'ÉTAT (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = [] 
if 'current_score' not in st.session_state:
    st.session_state.current_score = 0
if 'current_mistakes' not in st.session_state:
    st.session_state.current_mistakes = [] 
if 'validated_questions' not in st.session_state:
    st.session_state.validated_questions = set() 
if 'show_explanation' not in st.session_state:
    st.session_state.show_explanation = {}
if 'quiz_batch' not in st.session_state:
    st.session_state.quiz_batch = []

# --- CONSTANTE MODIFIÉE ---
QUESTIONS_PAR_QUIZ = 20  # <--- C'est ici que ça se passe !

# --- BARRE LATÉRALE : SAUVEGARDE & CHARGEMENT ---
st.sidebar.image("https://img.icons8.com/color/96/000000/brain--v1.png", width=60)
st.sidebar.title("🧠 Psychomot'")

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Sauvegarde")

# BOUTON CHARGER
uploaded_file = st.sidebar.file_uploader("Charger une progression", type="json")
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        if isinstance(data, list):
            st.session_state.history = data
            st.sidebar.success("✅ Progression chargée !")
    except:
        st.sidebar.error("Fichier invalide.")

# BOUTON SAUVEGARDER
if st.session_state.history:
    json_history = json.dumps(st.session_state.history)
    st.sidebar.download_button(
        label="📥 Sauvegarder ma progression",
        data=json_history,
        file_name="ma_progression_psychomot.json",
        mime="application/json"
    )
else:
    st.sidebar.caption("Fais au moins un quiz pour pouvoir sauvegarder.")

st.sidebar.markdown("---")

# --- NAVIGATION ---
menu = st.sidebar.radio("📌 Navigation", ["Tableau de Bord", "Passer un Quiz"])

# --- FONCTIONS UTILES ---



# --- OUTILS POUR DISTRACTEURS "PROF" (génération à la volée, sans modifier db_questions) ---

MODULE_PDF_PATHS = {
    "MODULE 1: Santé Pub, Pharma, Hygiène": "MODULE 1 (SANTE PUBLIC,PHARMACOLOGIE,HYGYENE).pdf",
    "MODULE 2: Anatomie & Neuroanatomie": "MODULE 2 anatomie et neuroanatomie.pdf",
    "MODULE 3: Physiologie": "MODULE 3 PHYSIOLOGIE.pdf",
    "MODULE 4: Psychologie": "MODULE 4 PSYCOLOGIE.pdf",
    "MODULE 5: Psychiatrie": "module 5 spychiatrie.pdf",
    "MODULE 6: Psychomotricité Théorique": "module 6 psychomotricité théorique.pdf",
}

_FR_STOPWORDS = {
    "le","la","les","un","une","des","du","de","d","et","ou","où","au","aux","en","dans","sur","pour","par","avec","sans","chez",
    "ce","cette","ces","cet","cela","ça","qui","que","quoi","dont","où","quand","comment","pourquoi",
    "est","sont","être","a","ont","avait","avaient","sera","seront","été","fait","faire","peut","peuvent","doit","doivent",
    "plus","moins","très","trop","pas","ne","ni","se","sa","son","ses","leur","leurs","mon","ma","mes","ton","ta","tes",
    "il","elle","ils","elles","on","nous","vous","je","tu",
    "à","y","l","m","t","s","n"
}

_ANTONYM_SWAPS = [
    (r"\baugmente\b", "diminue"),
    (r"\bdiminue\b", "augmente"),
    (r"\bactive\b", "inhibe"),
    (r"\binhibe\b", "active"),
    (r"\bstimule\b", "freine"),
    (r"\bfreine\b", "stimule"),
    (r"\bexcitation\b", "inhibition"),
    (r"\binhibition\b", "excitation"),
    (r"\bcentral\b", "périphérique"),
    (r"\bpériphérique\b", "central"),
    (r"\binterne\b", "externe"),
    (r"\bexterne\b", "interne"),
    (r"\bsympathique\b", "parasympathique"),
    (r"\bparasympathique\b", "sympathique"),
]

# Règles ciblées (ex : ZPD/Vygotski) : si on détecte un motif, on fabrique 3 distracteurs "near miss".
_TARGETED_RULES = [
    # Zone proximale de développement (ZPD)
    (
        re.compile(r"\bzone\s+proximale\s+de\s+d[ée]veloppement\b|\bZPD\b", re.IGNORECASE),
        lambda q, a: [
            "L’écart entre le niveau de développement réel (ce que l’enfant sait faire seul) et ce qu’il sait faire après apprentissage stabilisé.",
            "La capacité maximale de l’enfant à réussir seul une tâche, sans étayage ni guidance de l’adulte ou des pairs.",
            "L’ensemble des situations scolaires et sociales dans lesquelles l’enfant apprend, indépendamment de l’aide apportée."
        ],
    ),
    # Conditionnement : renforcement / punition
    (
        re.compile(r"\b(renforcement|punition|conditionnement)\b", re.IGNORECASE),
        lambda q, a: [
            "Un procédé qui augmente la probabilité d’un comportement en ajoutant ou retirant un stimulus, sans nécessairement viser la compréhension.",
            "Une conséquence appliquée après un comportement pour en diminuer la fréquence, même si le sujet ressent un soulagement immédiat.",
            "Un apprentissage par association temporelle entre deux événements, sans lien de causalité conscient pour le sujet."
        ],
    ),
]

@st.cache_data(show_spinner=False)
def _load_module_texts():
    """Charge le texte des PDF (si disponibles) pour nourrir un petit 'lexique' par module.
    Si PyPDF2 n'est pas dispo ou fichier absent, on retourne {}."""
    if PyPDF2 is None:
        return {}
    base_dir = Path(__file__).resolve().parent
    texts = {}
    for module, fname in MODULE_PDF_PATHS.items():
        p = base_dir / fname
        if not p.exists():
            continue
        try:
            reader = PyPDF2.PdfReader(str(p))
            full = []
            for page in reader.pages:
                t = page.extract_text() or ""
                if t:
                    full.append(t)
            texts[module] = "\n".join(full)
        except Exception:
            continue
    return texts

def _tokenize_fr(text: str):
    text = (text or "").lower()
    text = re.sub(r"[^a-zàâäéèêëîïôöùûüç0-9\-\s']", " ", text)
    toks = [t.strip("'-") for t in text.split()]
    toks = [t for t in toks if len(t) >= 4 and t not in _FR_STOPWORDS and not t.isdigit()]
    return toks

@st.cache_data(show_spinner=False)
def _build_term_bank():
    """Construit un 'banque de termes' par module à partir des PDF + db_questions."""
    module_texts = _load_module_texts()
    bank = {}
    for module, qs in db_questions.items():
        corpus_parts = []
        # PDF
        if module in module_texts:
            corpus_parts.append(module_texts[module])
        # Questions + options
        for item in qs:
            corpus_parts.append(item.get("q",""))
            for opt in item.get("options",[]) or []:
                corpus_parts.append(str(opt))
            corpus_parts.append(str(item.get("answer","")))
        corpus = "\n".join(corpus_parts)
        toks = _tokenize_fr(corpus)
        counts = collections.Counter(toks)
        # On garde des termes fréquents (évite le bruit)
        terms = [w for w, c in counts.most_common(500) if c >= 3]
        bank[module] = terms
    return bank

def _apply_antonym_swaps(text: str) -> str:
    out = text
    for pat, rep in _ANTONYM_SWAPS:
        if re.search(pat, out, flags=re.IGNORECASE):
            out = re.sub(pat, rep, out, flags=re.IGNORECASE)
            break
    return out

def _make_near_miss(answer: str, module: str, forbid: set, rng: random.Random) -> str:
    """Fabrique une proposition fausse mais plausible en partant de la bonne réponse."""
    a = str(answer).strip()
    bank = _build_term_bank().get(module, [])
    # 1) swaps 'classiques' (augmente/diminue, etc.)
    cand = _apply_antonym_swaps(a)

    # 2) substitution de 1-2 termes (mêmes champs lexicaux)
    toks = _tokenize_fr(cand)
    key_toks = [t for t in toks if t in set(_tokenize_fr(a))][:6]
    # Si pas de clé, prendre des mots longs
    if not key_toks:
        key_toks = sorted(set(toks), key=len, reverse=True)[:4]

    bank_pool = [t for t in bank if t not in toks and t not in _FR_STOPWORDS]
    rng.shuffle(bank_pool)

    replaced = 0
    for kt in key_toks[:2]:
        if not bank_pool:
            break
        repl = bank_pool.pop()
        # remplacer un mot entier
        cand2 = re.sub(rf"\b{re.escape(kt)}\b", repl, cand, count=1, flags=re.IGNORECASE)
        if cand2 != cand:
            cand = cand2
            replaced += 1

    # 3) Garde-fous : éviter doublons/bonne réponse
    cand = cand.strip()
    if cand in forbid or cand.lower() == a.lower():
        cand = _apply_antonym_swaps(a)  # fallback simple
    return cand

def _rewrite_distractors(question: dict, module: str, rng: random.Random) -> list:
    """Retourne une nouvelle liste d'options: bonne réponse inchangée, distracteurs régénérés."""
    options = list(question.get("options") or [])
    answer = str(question.get("answer","")).strip()
    qtext = str(question.get("q",""))

    # si pas un QCM classique, ne rien faire
    if not options or answer == "":
        return options

    # Appliquer règles ciblées si on match
    for rx, gen in _TARGETED_RULES:
        if rx.search(qtext) or rx.search(answer):
            distractors = gen(qtext, answer)
            # On garde 3 distracteurs uniques et pas identiques à l'answer
            cleaned = []
            forbid = {answer}
            for d in distractors:
                d = str(d).strip()
                if d and d not in forbid:
                    forbid.add(d)
                    cleaned.append(d)
                if len(cleaned) >= 3:
                    break
            if len(cleaned) == 3:
                new_opts = cleaned + [answer]
                rng.shuffle(new_opts)
                return new_opts

    # Générique : 3 near-miss autour de la bonne réponse
    forbid = {answer}
    distractors = []
    for _ in range(12):  # essais pour trouver 3 uniques
        cand = _make_near_miss(answer, module, forbid, rng)
        cand = cand.strip()
        if cand and cand not in forbid and cand.lower() != answer.lower():
            forbid.add(cand)
            distractors.append(cand)
            if len(distractors) >= 3:
                break

    # Si on n'arrive pas à 3, on retombe sur les distracteurs existants (en les conservant)
    if len(distractors) < 3:
        existing = [o for o in options if str(o).strip() != answer]
        rng.shuffle(existing)
        for o in existing:
            o = str(o).strip()
            if o and o not in forbid:
                distractors.append(o)
                forbid.add(o)
            if len(distractors) >= 3:
                break

    # Harmonisation de longueur (sans '...') : on coupe au même ordre de grandeur
    target_len = max(60, min(220, len(answer)))
    def clip(s: str) -> str:
        s = " ".join(s.split())
        if len(s) <= target_len:
            return s
        # coupe à la dernière ponctuation/espace avant target_len
        cut = s.rfind(" ", 0, target_len)
        if cut < 40:
            cut = target_len
        return s[:cut].rstrip(" ,;:.") + "."
    distractors = [clip(d) for d in distractors[:3]]
    answer_clean = " ".join(answer.split())
    # on ne clippe pas l'answer (sens inchangé) mais on peut juste normaliser espaces
    new_opts = distractors + [answer_clean]
    rng.shuffle(new_opts)
    return new_opts
def _prepare_question_for_quiz(q: dict, module: str) -> dict:
    """Retourne une copie de la question pour le quiz.

    - Mélange l'ordre des options (QCM)
    - Régénère les distracteurs pour qu'ils soient plausibles et d'une longueur comparable
      à la bonne réponse (sans changer le sens de la bonne réponse).
    Important: on ne modifie pas db_questions en place.
    """
    q2 = copy.deepcopy(q)
    if q2.get("type") == "qcm" and isinstance(q2.get("options"), list) and q2.get("answer"):
        rng = random.Random()
        # Déterminisme léger par question (pour éviter que ça change à chaque rerun Streamlit)
        seed_base = (str(q2.get("q","")) + "||" + str(q2.get("answer","")) + "||" + str(module)).encode("utf-8", "ignore")
        rng.seed(sum(seed_base) % (2**32 - 1))

        # Remplacer les distracteurs par des distracteurs plausibles
        q2["options"] = _rewrite_distractors(q2, module, rng)

        # Mélange final (au cas où)
        rng.shuffle(q2["options"])
    return q2


def get_global_stats():
    if not st.session_state.history:
        return None
    df = pd.DataFrame(st.session_state.history)
    df['note_20'] = df['score_percent'] / 5
    avg_per_module = df.groupby("module")["note_20"].mean().reset_index()
    return avg_per_module

def get_best_worst():
    if not st.session_state.history:
        return None, None
    df = pd.DataFrame(st.session_state.history)
    df['note_20'] = df['score_percent'] / 5
    
    # Meilleur score
    idx_max = df['note_20'].idxmax()
    best = df.loc[idx_max]
    best_txt = f"{best['note_20']:.1f}/20 ({best['module']})"
    
    # Pire score
    idx_min = df['note_20'].idxmin()
    worst = df.loc[idx_min]
    worst_txt = f"{worst['note_20']:.1f}/20 ({worst['module']})"
    
    return best_txt, worst_txt

def get_weaknesses():
    all_mistakes = []
    for session in st.session_state.history:
        all_mistakes.extend(session['mistakes'])
    if not all_mistakes:
        return []
    from collections import Counter
    counts = Counter(all_mistakes)
    return counts.most_common(5)

def generer_nouveau_quiz(module):
    if module not in db_questions:
        st.error("Erreur de chargement du module.")
        return
    all_questions = db_questions[module]
    nb_to_take = min(len(all_questions), QUESTIONS_PAR_QUIZ)
    st.session_state.quiz_batch = [_prepare_question_for_quiz(q, module) for q in random.sample(all_questions, nb_to_take)]
    st.session_state.current_score = 0
    st.session_state.current_mistakes = []
    st.session_state.validated_questions = set()
    st.session_state.show_explanation = {}
    st.session_state.active_module = module

# =========================================================
# PAGE 1 : TABLEAU DE BORD
# =========================================================
if menu == "Tableau de Bord":
    st.title("📊 Tableau de Bord de Révision")
    stats = get_global_stats()
    
    if stats is None:
        st.info("👋 Bienvenue ! Aucune donnée pour l'instant. Va dans l'onglet 'Passer un Quiz' pour commencer.")
    else:
        # 1. Indicateurs (BEST & WORST)
        best_txt, worst_txt = get_best_worst()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quiz réalisés", len(st.session_state.history))
        with col2:
            st.metric("🏆 Meilleur Score", best_txt)
        with col3:
            st.metric("⚠️ Pire Score", worst_txt)
        
        st.write("---")
        
        col_graph1, col_graph2 = st.columns(2)
        
        # 2. Graphique Bâtons (/20)
        with col_graph1:
            st.subheader("📈 Moyenne par matière (/20)")
            fig_bar = px.bar(stats, x='module', y='note_20', range_y=[0, 20], 
                         labels={'note_20': 'Note sur 20'},
                         color='note_20', color_continuous_scale='Bluered')
            st.plotly_chart(fig_bar, use_container_width=True)

        # 3. Graphique Évolution (Axe X entier de 1 en 1)
        with col_graph2:
            st.subheader("🚀 Évolution des notes")
            df_hist = pd.DataFrame(st.session_state.history)
            df_hist['note_20'] = df_hist['score_percent'] / 5
            df_hist['Essai'] = range(1, len(df_hist) + 1)
            
            fig_line = px.line(df_hist, x='Essai', y='note_20', color='module', markers=True,
                               range_y=[0, 21],
                               labels={'Essai': 'Numéro du Quiz', 'note_20': 'Note / 20'},
                               title="Progression au fil des essais")
            
            fig_line.update_xaxes(dtick=1)
            st.plotly_chart(fig_line, use_container_width=True)
        
        st.write("---")
        st.subheader("⚠️ Tes points faibles (tous quiz confondus)")
        weaknesses = get_weaknesses()
        if weaknesses:
            cols = st.columns(5)
            for i, (tag, count) in enumerate(weaknesses):
                with cols[i % 5]:
                    st.markdown(f"<div class='metric-card' style='border-left: 5px solid #ff4d4d;'><b>{tag}</b><br>{count} erreurs</div>", unsafe_allow_html=True)
        else:
            st.success("Aucune lacune récurrente détectée !")

# =========================================================
# PAGE 2 : QUIZ (MODE ALÉATOIRE)
# =========================================================
elif menu == "Passer un Quiz":
    st.sidebar.header("🎯 Nouveau Tirage")
    module_choisi = st.sidebar.selectbox("Choisir le module :", list(db_questions.keys()))
    
    # Mise à jour du bouton avec "20 Q"
    if st.sidebar.button("🎲 GÉNÉRER UN NOUVEAU QUIZ (20 Q)", type="primary"):
        generer_nouveau_quiz(module_choisi)
        st.rerun()

    if 'active_module' not in st.session_state or st.session_state.active_module != module_choisi:
        generer_nouveau_quiz(module_choisi)
    
    st.title(f"📝 {module_choisi}")
    
    if not st.session_state.quiz_batch:
        st.warning("Aucune question chargée. Clique sur 'Générer un nouveau quiz'.")
    else:
        st.caption(f"Série aléatoire de {len(st.session_state.quiz_batch)} questions.")
        questions = st.session_state.quiz_batch
        
        for i, q in enumerate(questions):
            st.markdown(f"<div class='question-card'><h5>Question {i+1} <span style='background:#eee;padding:2px 5px;border-radius:5px;font-size:0.7em'>{q['tag']}</span></h5>", unsafe_allow_html=True)
            st.write(f"**{q['q']}**")
            q_hash = hash(q['q']) 
            q_id = f"{module_choisi}_{q_hash}"
            
            if q["type"] == "qcm":
                # On garde la valeur "originale" (texte complet) pour la correction,
                # mais on affiche une version raccourcie pour éviter les indices de longueur.
                options_with_id = list(enumerate(q["options"]))
                selected = st.radio(
                    "Réponse :",
                    options_with_id,
                    key=f"radio_{q_id}",
                    index=None,
                    format_func=lambda t: f"{chr(65 + t[0])}. {_shorten_option_for_display(t[1])}",
                )
                user_choice = selected[1] if selected is not None else None
                if st.button(f"Valider", key=f"btn_{q_id}"):
                    st.session_state.show_explanation[q_id] = True
                    if q_id not in st.session_state.validated_questions:
                        st.session_state.validated_questions.add(q_id)
                        if user_choice == q["answer"]:
                            st.session_state.current_score += 1
                        else:
                            st.session_state.current_mistakes.append(q["tag"])
                
                if st.session_state.show_explanation.get(q_id):
                    if user_choice == q["answer"]:
                        st.success("Correct !")
                    else:
                        st.error(f"Faux. Réponse : {q['answer']}")
                    st.info(f"💡 {q['explanation']}")

            elif q["type"] == "ouverte":
                st.text_area("Ta réflexion :", key=f"txt_{q_id}")
                if st.button(f"Vérifier", key=f"btn_{q_id}"):
                    st.session_state.show_explanation[q_id] = True
                    if q_id not in st.session_state.validated_questions:
                        st.session_state.validated_questions.add(q_id)
                
                if st.session_state.show_explanation.get(q_id):
                    st.markdown(f"<div class='feedback-box'>✅ <b>Réponse attendue :</b> {q['answer']}<br><i>(Auto-évaluation)</i></div>", unsafe_allow_html=True)
                    col_a, col_b = st.columns(2)
                    if f"eval_{q_id}" not in st.session_state:
                        if col_a.button("J'ai eu bon ✅", key=f"good_{q_id}"):
                            st.session_state.current_score += 1
                            st.session_state[f"eval_{q_id}"] = True
                            st.rerun()
                        if col_b.button("J'ai eu faux ❌", key=f"bad_{q_id}"):
                            st.session_state.current_mistakes.append(q["tag"])
                            st.session_state[f"eval_{q_id}"] = True
                            st.rerun()
            st.markdown("---")

        if st.button("🏁 TERMINER CE TEST", type="primary"):
            total_q = len(questions)
            score = st.session_state.current_score
            percent = (score / total_q) * 100
            
            st.session_state.history.append({
                "module": module_choisi, 
                "score": score, 
                "total": total_q,
                "score_percent": percent, 
                "mistakes": st.session_state.current_mistakes,
                "date": str(datetime.now())
            })
            st.balloons()
            
            note_sur_20 = score / total_q * 20
            
            st.markdown(f"""
            <div style="background-color:#d4edda;padding:20px;border-radius:10px;text-align:center;">
                <h2>Score : {score}/{total_q}</h2>
                <h3>Note : {note_sur_20:.1f}/20</h3>
            </div>
            """, unsafe_allow_html=True)
            

            st.info("Résultat enregistré ! Pense à sauvegarder ta progression dans le menu de gauche.")


