import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Psychomot' Master - Suivi & Performance", page_icon="🧠", layout="wide")

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
        # PHARMACOLOGIE - BASES
        {"q": "Quelle est la définition exacte d'un médicament ?", "type": "ouverte", "answer": "Substance ou composition présentant des propriétés curatives ou préventives à l'égard des maladies humaines ou animales (diagnostic, restauration, correction fonctionnelle).", "explanation": "Définition légale. Inclut le préventif (vaccin) et le curatif.", "tag": "Définition"},
        {"q": "Qu'est-ce qu'un excipient à 'effet notoire' ?", "options": ["Un excipient inactif", "Un excipient susceptible d'avoir un effet négatif (allergie, intolérance) chez certains patients", "Un excipient qui change la couleur"], "answer": "Un excipient susceptible d'avoir un effet négatif (allergie, intolérance) chez certains patients", "type": "qcm", "explanation": "Exemples : sucre (diabétique), alcool, gluten, lactose.", "tag": "Galénique"},
        {"q": "Quelle est la différence entre DCI et Nom de marque ?", "options": ["C'est pareil", "DCI = Nom scientifique international de la molécule / Marque = Nom commercial", "DCI = Nom du laboratoire"], "answer": "DCI = Nom scientifique international de la molécule / Marque = Nom commercial", "type": "qcm", "explanation": "Ex: Paracétamol (DCI) vs Doliprane (Marque).", "tag": "Législation"},
        {"q": "Qu'est-ce que la Bioéquivalence pour un générique ?", "type": "ouverte", "answer": "Le fait que le générique a la même biodisponibilité (vitesse et quantité de principe actif absorbé) que le princeps.", "explanation": "Même composition qualitative et quantitative en PA, même forme pharma.", "tag": "Générique"},
        {"q": "Qu'est-ce que la marge thérapeutique ?", "options": ["La différence entre la dose efficace et la dose toxique", "Le prix du médicament", "La durée du traitement"], "answer": "La différence entre la dose efficace et la dose toxique", "type": "qcm", "explanation": "Si la marge est étroite (ex: lithium, digoxine), le risque de surdosage est élevé.", "tag": "Sécurité"},
        {"q": "Pic plasmatique (Tmax) : définition ?", "type": "ouverte", "answer": "Le moment où la concentration du médicament dans le sang est maximale.", "explanation": "C'est là que l'effet est le plus fort (et le risque d'effet secondaire aussi).", "tag": "PK"},
        {"q": "Que signifie la voie 'Per Os' ?", "answer": "Par la bouche (Voie orale)", "type": "qcm", "options": ["Par la bouche", "Par l'os", "Par injection"], "explanation": "C'est la voie la plus courante mais la plus lente.", "tag": "Galénique"},
        {"q": "Formes à libération prolongée (LP) : Peut-on les écraser ?", "options": ["Oui", "Non, jamais"], "answer": "Non, jamais", "type": "qcm", "explanation": "Cela libèrerait toute la dose d'un coup (risque de surdosage mortel).", "tag": "Galénique"},
        {"q": "Qu'est-ce qu'un médicament tératogène ?", "type": "ouverte", "answer": "Un médicament qui provoque des malformations chez le fœtus s'il est pris pendant la grossesse.", "explanation": "Ex: Thalidomide, Dépakine.", "tag": "Risques"},
        {"q": "Définition de la iatrogénie ?", "type": "ouverte", "answer": "Tout effet indésirable ou négatif provoqué par l'acte médical ou les médicaments.", "explanation": "Peut être évitable (erreur) ou inévitable (aléa).", "tag": "Risques"},
        {"q": "Automédication : principaux risques ?", "type": "ouverte", "answer": "Erreur de diagnostic, retard de prise en charge, interactions médicamenteuses, surdosage, masquage des symptômes.", "explanation": "Surtout avec les AINS (Ibuprofène) ou Paracétamol.", "tag": "Risques"},
        {"q": "AMM : Signification ?", "options": ["Autorisation de Mise sur le Marché", "Aide Médicale aux Malades"], "answer": "Autorisation de Mise sur le Marché", "type": "qcm", "explanation": "Délivrée par l'ANSM (France) ou l'EMA (Europe).", "tag": "Législation"},
        {"q": "Niveau SMR (Service Médical Rendu) : à quoi ça sert ?", "options": ["À fixer le taux de remboursement", "À fixer le prix"], "answer": "À fixer le taux de remboursement", "type": "qcm", "explanation": "Majeur (65%), Modéré (30%), Faible (15%).", "tag": "Législation"},
        
        # PHARMACOCINÉTIQUE (ADME)
        {"q": "Que signifie ADME ?", "options": ["Absorption, Digestion, Mouvement, Élimination", "Absorption, Distribution, Métabolisme, Élimination", "Action, Distribution, Molécule, Effet"], "answer": "Absorption, Distribution, Métabolisme, Élimination", "type": "qcm", "explanation": "Les 4 étapes du devenir du médicament dans l'organisme.", "tag": "PK"},
        {"q": "Qu'est-ce que la Biodisponibilité ?", "type": "ouverte", "answer": "Fraction (%) de la dose administrée qui atteint la circulation générale sous forme inchangée.", "explanation": "100% par voie IV. <100% par voie orale (barrière digestive + foie).", "tag": "PK"},
        {"q": "Qu'est-ce que l'effet de premier passage hépatique ?", "type": "ouverte", "answer": "La perte de principe actif lors de son premier passage par le foie (via veine porte) avant d'atteindre le sang.", "explanation": "Le foie filtre et métabolise une partie du médicament absorbé par voie orale.", "tag": "PK"},
        {"q": "Quel organe est le principal responsable du métabolisme des médicaments ?", "options": ["Rein", "Foie", "Poumon"], "answer": "Foie", "type": "qcm", "explanation": "Via les enzymes (Cytochromes P450).", "tag": "PK"},
        {"q": "Qu'est-ce que la demi-vie (T1/2) ?", "type": "ouverte", "answer": "Temps nécessaire pour que la concentration plasmatique du médicament diminue de 50%.", "explanation": "Il faut 5 à 7 demi-vies pour éliminer quasi totalement le produit.", "tag": "PK"},
        {"q": "Qu'est-ce que la clairance ?", "options": ["Volume de plasma totalement épuré d'une substance par unité de temps", "Quantité d'urine", "Vitesse de filtration"], "answer": "Volume de plasma totalement épuré d'une substance par unité de temps", "type": "qcm", "explanation": "Reflète la capacité d'élimination (rénale ou hépatique).", "tag": "PK"},
        {"q": "Liaison aux protéines plasmatiques : quelle protéine fixe majoritairement les médicaments ?", "options": ["Hémoglobine", "Albumine", "Insuline"], "answer": "Albumine", "type": "qcm", "explanation": "Seule la fraction 'libre' (non liée) du médicament est active.", "tag": "PK"},


        # PSYCHOTROPES & DOULEUR
        {"q": "Quelles sont les 4 propriétés des Benzodiazépines ?", "type": "ouverte", "answer": "Anxiolytique, Sédatif/Hypnotique, Myorelaxant, Anticonvulsivant.", "explanation": "Et aussi amnésiante. Attention au risque de dépendance.", "tag": "Psychotropes"},
        {"q": "Définition de l'addiction (Critères) ?", "type": "ouverte", "answer": "Perte de contrôle, Craving (besoin irrépressible), Poursuite malgré les conséquences négatives, Tolérance, Sevrage.", "explanation": "C'est une pathologie de la liberté (addictus = esclave).", "tag": "Addicto"},
        {"q": "Différence douleur par excès de nociception et neuropathique ?", "type": "ouverte", "answer": "Nociception = Stimulation des récepteurs (lésion tissulaire). Neuropathique = Lésion du système nerveux lui-même.", "explanation": "Neuro = décharge électrique, brûlure, paresthésies.", "tag": "Douleur"},
        
        # SANTÉ PUBLIQUE & HISTOIRE
        {"q": "Loi Kouchner (4 mars 2002) ?", "options": ["Création Sécu", "Droit des malades et qualité du système de santé", "Loi HPST"], "answer": "Droit des malades et qualité du système de santé", "type": "qcm", "explanation": "Accès direct au dossier médical, consentement éclairé.", "tag": "Loi"},
        {"q": "Lois Jules Ferry (1881-1882) ?", "options": ["École laïque, gratuite et obligatoire", "Vote des femmes"], "answer": "École laïque, gratuite et obligatoire", "type": "qcm", "explanation": "Fondement de l'instruction publique.", "tag": "Histoire"},
        {"q": "Définition Santé OMS (1946) ?", "type": "ouverte", "answer": "État de complet bien-être physique, mental et social, et ne consiste pas seulement en une absence de maladie ou d'infirmité.", "explanation": "Approche globale.", "tag": "Concept"},
        {"q": "Qu'est-ce que la PMI ?", "options": ["Protection Médicale Interne", "Protection Maternelle et Infantile"], "answer": "Protection Maternelle et Infantile", "type": "qcm", "explanation": "Suivi 0-6 ans (prévention, dépistage).", "tag": "Santé Pub"},
        {"q": "Vaccins obligatoires : combien y en a-t-il pour les enfants nés après 2018 ?", "options": ["3", "11", "8"], "answer": "11", "type": "qcm", "explanation": "DTP, Coqueluche, HiB, Hépatite B, Pneumocoque, Méningocoque C, ROR.", "tag": "Santé Pub"},
        {"q": "Loi Leonetti (2005) ?", "type": "ouverte", "answer": "Loi sur la fin de vie. Interdiction de l'obstination déraisonnable (acharnement thérapeutique), droit aux soins palliatifs.", "explanation": "Renforcée par la loi Claeys-Leonetti (2016) : sédation profonde et continue.", "tag": "Loi"},
        {"q": "Qu'est-ce qu'un AES ?", "type": "ouverte", "answer": "Accident d'Exposition au Sang (piqûre, coupure, projection sur muqueuse).", "explanation": "Urgence médicale (lavage, antisepsie, évaluation risque VIH/VHB/VHC).", "tag": "Risques Pro"},
        {"q": "Précautions 'Air' : pour quelles maladies ?", "options": ["Grippe", "Tuberculose, Rougeole, Varicelle", "Gastro"], "answer": "Tuberculose, Rougeole, Varicelle", "type": "qcm", "explanation": "Masque FFP2 obligatoire pour le soignant. Porte fermée.", "tag": "Hygiène"},
        {"q": "Précautions 'Gouttelettes' : pour quelles maladies ?", "options": ["Grippe, Méningite, Coqueluche", "Tuberculose"], "answer": "Grippe, Méningite, Coqueluche", "type": "qcm", "explanation": "Masque chirurgical suffit (portée < 1m).", "tag": "Hygiène"},
        {"q": "Clostridium difficile : particularité hygiène ?", "type": "ouverte", "answer": "C'est une bactérie sporulée résistante à l'alcool. Il faut se laver les mains au SAVON après la friction SHA.", "explanation": "Seul cas où le lavage des mains remplace la friction.", "tag": "Hygiène"},
        {"q": "Bactérie commensale : définition ?", "type": "ouverte", "answer": "Bactérie présente naturellement sur/dans le corps (flore cutanée, digestive) sans causer de maladie (sauf si déséquilibre).", "explanation": "Contraire de bactérie pathogène.", "tag": "Microbio"},
        {"q": "Différence Endémie / Épidémie / Pandémie ?", "type": "ouverte", "answer": "Endémie = Présence constante. Épidémie = Augmentation brutale des cas localisés. Pandémie = Épidémie mondiale.", "explanation": "Ex: Paludisme (Endémie), Grippe (Épidémie), Covid-19 (Pandémie).", "tag": "Concept"},
        {"q": "Loi 1905 ?", "answer": "Séparation Église et État", "type": "qcm", "options": ["Séparation Église et État", "École laïque"], "explanation": "Impact sur la laïcité à l'hôpital public.", "tag": "Histoire"},
        {"q": "Qu'est-ce que l'éducation thérapeutique du patient (ETP) ?", "type": "ouverte", "answer": "Aider le patient à acquérir les compétences pour gérer sa maladie chronique (comprendre, traiter, surveiller).", "explanation": "Rend le patient autonome.", "tag": "Soin"},
        {"q": "Secret professionnel : peut-on le lever ?", "options": ["Jamais", "Oui, dans des cas précis (maltraitance, péril imminent)", "Oui, à la famille"], "answer": "Oui, dans des cas précis (maltraitance, péril imminent)", "type": "qcm", "explanation": "Code pénal. Le secret couvre tout ce qui a été vu, entendu, compris.", "tag": "Législation"},
        {"q": "Hépatite B : quel type de transmission ?", "options": ["Sanguine et Sexuelle", "Respiratoire", "Digestive"], "answer": "Sanguine et Sexuelle", "type": "qcm", "explanation": "Comme le VIH. L'Hépatite A est digestive (mains sales).", "tag": "Maladie"},
        {"q": "Gale : quel type de transmission ?", "options": ["Contact direct (peau à peau) et linge", "Air"], "answer": "Contact direct (peau à peau) et linge", "type": "qcm", "explanation": "Nécessite précautions contact renforcées.", "tag": "Maladie"},
        {"q": "Qu'est-ce que la désinfection ?", "type": "ouverte", "answer": "Opération au résultat momentané permettant d'éliminer ou de tuer les micro-organismes sur des milieux inertes.", "explanation": "Spectre d'activité : bactéricide, virucide, fongicide...", "tag": "Hygiène"},
        {"q": "Ordre lors de la toilette ?", "type": "ouverte", "answer": "Du plus propre au plus sale. Du haut vers le bas.", "explanation": "Visage -> Corps -> Jambes -> Siège.", "tag": "Hygiène"},

        # HYGIÈNE & MICROBIO
        {"q": "Différence Eucaryote / Procaryote ?", "type": "ouverte", "answer": "Eucaryote = avec noyau (homme, champignon). Procaryote = sans noyau (bactérie).", "explanation": "Les virus sont acellulaires.", "tag": "Microbio"},
        {"q": "Qu'est-ce qu'un biofilm ?", "type": "ouverte", "answer": "Communauté de micro-organismes adhérant entre eux et à une surface, sécrétant une matrice protectrice.", "explanation": "Très résistant (ex: sur prothèse).", "tag": "Microbio"},
        {"q": "Infection Nosocomiale (IAS) : quel délai ?", "options": ["Dès l'admission", "> 48h après admission", "> 7 jours"], "answer": "> 48h après admission", "type": "qcm", "explanation": "Si prothèse/implant : délai de 1 an (voire 30 jours pour site op).", "tag": "IAS"},
        {"q": "Les 5 moments de l'hygiène des mains (OMS) ?", "type": "ouverte", "answer": "Avant contact patient, Avant geste aseptique, Après liquide bio, Après contact patient, Après contact environnement.", "explanation": "Friction SHA privilégiée.", "tag": "Hygiène"},
        {"q": "Durée friction SHA ?", "options": ["15s", "30s (ou jusqu'à séchage)", "1min"], "answer": "30s (ou jusqu'à séchage)", "type": "qcm", "explanation": "Sur mains sèches et non souillées.", "tag": "Hygiène"},
        {"q": "Définition Asepsie vs Antisepsie ?", "type": "ouverte", "answer": "Asepsie = Préventif (empêcher l'apport de germes). Antisepsie = Curatif (éliminer les germes sur tissus vivants).", "explanation": "On désinfecte du matériel (inerte), on antiseptise la peau (vivant).", "tag": "Hygiène"},
        {"q": "Déchets : Que veut dire DASRI ?", "options": ["Déchets d'Activités de Soins à Risques Infectieux", "Déchets Assimilables aux Soins"], "answer": "Déchets d'Activités de Soins à Risques Infectieux", "type": "qcm", "explanation": "Filière jaune (piquants, coupants, sang).", "tag": "Déchets"},
        {"q": "Que met-on dans les déchets OPCT ?", "options": ["Couches", "Objets Piquants Coupants Tranchants", "Papiers"], "answer": "Objets Piquants Coupants Tranchants", "type": "qcm", "explanation": "Aiguilles, lames, ampoules (boîte jaune rigide).", "tag": "Déchets"},
        {"q": "Cercle de Sinner (Nettoyage) : quels sont les 4 facteurs ?", "type": "ouverte", "answer": "Température, Temps d'action, Action Chimique, Action Mécanique.", "explanation": "Si on diminue l'un, il faut augmenter les autres.", "tag": "Hygiène"},
        {"q": "Isolement 'Contact' : quelles mesures ?", "type": "ouverte", "answer": "Tablier/Surblouse si soin mouillant, Gants si risque liquide bio, Hygiène mains, Matériel dédié.", "explanation": "Pour BMR, Gale, Clostridium...", "tag": "Isolement"},
        {"q": "BMR : Donner 2 exemples.", "type": "ouverte", "answer": "SARM (Staph Doré Résistant Méthicilline), EBLSE (Entérobactérie BLSE).", "explanation": "Bactéries Multi-Résistantes.", "tag": "Microbio"},
    ],

    "MODULE 2: Anatomie & Neuroanatomie": [
        # OSTEOLOGIE TRONC
        {"q": "Limites du Thorax ?", "type": "ouverte", "answer": "Avant: Sternum. Arrière: Rachis. Haut: 1ère côte. Bas: Diaphragme. Latéral: Côtes.", "explanation": "Protège cœur et poumons.", "tag": "Thorax"},
        {"q": "Rachis : Nombre de vertèbres par étage ?", "options": ["C5 T10 L7", "C7 T12 L5", "C12 T7 L5"], "answer": "C7 T12 L5", "type": "qcm", "explanation": "7 Cervicales, 12 Thoraciques, 5 Lombaires (+ Sacrum/Coccyx).", "tag": "Rachis"},
        {"q": "Noms spécifiques de C1 et C2 ?", "options": ["Atlas et Axis", "Axis et Atlas"], "answer": "Atlas et Axis", "type": "qcm", "explanation": "C1 Atlas porte la tête. C2 Axis possède la dent (processus odontoïde).", "tag": "Rachis"},
        {"q": "Quelles sont les courbures sagittales du rachis ?", "type": "ouverte", "answer": "Lordose cervicale, Cyphose thoracique, Lordose lombaire, Cyphose sacrée.", "explanation": "Lordose = creux (concave arrière). Cyphose = bosse (convexe arrière).", "tag": "Rachis"},
        {"q": "Sternum : parties ?", "type": "ouverte", "answer": "Manubrium, Corps, Processus Xiphoïde.", "explanation": "S'articule avec les clavicules et les côtes.", "tag": "Thorax"},

        # MEMBRE SUPÉRIEUR
        {"q": "Os de la ceinture scapulaire ?", "options": ["Clavicule + Scapula (+ Sternum)", "Humérus + Scapula"], "answer": "Clavicule + Scapula (+ Sternum)", "type": "qcm", "explanation": "Relie le membre supérieur au tronc.", "tag": "Épaule"},
        {"q": "Forme de la clavicule ?", "options": ["Os plat", "Os long en S italique", "Os court"], "answer": "Os long en S italique", "type": "qcm", "explanation": "Seul os reliant le bras au tronc.", "tag": "Épaule"},
        {"q": "Scapula : combien de bords et d'angles ?", "options": ["3 bords, 3 angles", "4 bords, 2 angles"], "answer": "3 bords, 3 angles", "type": "qcm", "explanation": "Os plat triangulaire.", "tag": "Épaule"},
        {"q": "Muscles de la coiffe des rotateurs (4) ?", "type": "ouverte", "answer": "Supra-épineux, Infra-épineux, Petit rond, Subscapulaire.", "explanation": "Stabilisent la tête humérale. (Le grand rond n'en fait pas partie !).", "tag": "Épaule"},
        {"q": "Humérus : quel col casse le plus souvent ?", "options": ["Col anatomique", "Col chirurgical"], "answer": "Col chirurgical", "type": "qcm", "explanation": "Zone de faiblesse métaphysaire.", "tag": "Humérus"},
        {"q": "Quel nerf passe dans le sillon à la face post de l'humérus ?", "answer": "Nerf Radial", "type": "qcm", "options": ["Radial", "Ulnaire", "Médian"], "explanation": "Risque de paralysie radiale (main tombante) si fracture.", "tag": "Humérus"},
        {"q": "Triade terrible du coude ?", "type": "ouverte", "answer": "Luxation postérieure coude + Fracture tête radiale + Fracture processus coronoïde.", "explanation": "Grande instabilité.", "tag": "Coude"},
        {"q": "Os du Carpe (Phrase mnémotechnique) ?", "type": "ouverte", "answer": "Scaphoïde, Lunatum, Triquetrum, Pisiforme (Rangée 1) / Trapèze, Trapézoïde, Capitatum, Hamatum (Rangée 2).", "explanation": "'Sous Le Temps Pluvieux...'", "tag": "Main"},
        {"q": "Nerf 'petit juif' (coude) ?", "answer": "Nerf Ulnaire", "type": "qcm", "options": ["Radial", "Ulnaire"], "explanation": "Passe dans la gouttière épitrochléenne (médial).", "tag": "Coude"},
        {"q": "Nerf Médian : territoire sensitif ?", "type": "ouverte", "answer": "Paume, Pouce, Index, Majeur et moitié de l'Annulaire.", "explanation": "Nerf de la pince pouce-index et du canal carpien.", "tag": "Main"},
        {"q": "Muscle Deltoïde : action ?", "options": ["Abduction de l'épaule", "Flexion coude"], "answer": "Abduction de l'épaule", "type": "qcm", "explanation": "Le 'galbe' de l'épaule. Il permet de lever le bras sur le côté.", "tag": "Épaule"},
        {"q": "Articulation du coude : combien d'articulations ?", "options": ["1", "3"], "answer": "3", "type": "qcm", "explanation": "Huméro-ulnaire, Huméro-radiale, Radio-ulnaire proximale.", "tag": "Coude"},
        {"q": "Pronation / Supination : définition ?", "type": "ouverte", "answer": "Supination = Paume vers le ciel (demander). Pronation = Paume vers le sol (prendre).", "explanation": "Mouvement de l'avant-bras (radius tourne autour de l'ulna).", "tag": "Mouvement"},
        {"q": "Os pisiforme : localisation ?", "options": ["Carpe (poignet)", "Tarse (cheville)"], "answer": "Carpe (poignet)", "type": "qcm", "explanation": "Petit os rond sur le triquetrum.", "tag": "Main"},
        {"q": "Flexors des doigts : origine ?", "options": ["Épicondyle médial (Épitrochlée)", "Épicondyle latéral"], "answer": "Épicondyle médial (Épitrochlée)", "type": "qcm", "explanation": "Les extenseurs partent de l'épicondyle latéral.", "tag": "Myologie"},

        # MEMBRE INFÉRIEUR
        {"q": "Os coxal : composition ?", "type": "ouverte", "answer": "Ilion (Aile iliaque), Ischion, Pubis.", "explanation": "Se réunissent au niveau de l'acétabulum (Y cartilagineux).", "tag": "Bassin"},
        {"q": "Qu'est-ce que l'acétabulum ?", "type": "ouverte", "answer": "Cavité articulaire de l'os coxal recevant la tête fémorale.", "explanation": "Forme une énarthrose.", "tag": "Hanche"},
        {"q": "Classification de Garden (Col fémur) - Stade 3 ?", "options": ["Non déplacée", "Déplacée en varus, charnière conservée", "Tête libre"], "answer": "Déplacée en varus, charnière conservée", "type": "qcm", "explanation": "Risque de nécrose de la tête (artère circonflexe). Stade 4 = tête libre.", "tag": "Trauma"},
        {"q": "Classification de Levin (Luxation Hanche) : la plus fréquente ?", "options": ["Antérieure", "Postérieure (Tableau de bord)"], "answer": "Postérieure (Tableau de bord)", "type": "qcm", "explanation": "La jambe tape le tableau de bord, le fémur recule.", "tag": "Trauma"},
        {"q": "Dysplasie de hanche : traitement nourrisson ?", "type": "ouverte", "answer": "Maintien en Abduction (Lange Câlin, Harnais de Pavlik).", "explanation": "Pour centrer la tête dans le cotyle.", "tag": "Pédia"},
        {"q": "Genou : Rôle des ligaments croisés ?", "type": "ouverte", "answer": "Pivot central. Stabilité antéro-postérieure.", "explanation": "LCA (Antérieur) et LCP (Postérieur).", "tag": "Genou"},
        {"q": "Triade malheureuse du genou ?", "type": "ouverte", "answer": "Rupture LCA + Lli (Collatéral Médial) + Ménisque médial.", "explanation": "Sur valgus flexion rotation externe.", "tag": "Genou"},
        {"q": "Quel os est sésamoïde dans le genou ?", "answer": "Patella (Rotule)", "type": "qcm", "options": ["Patella", "Fabella"], "explanation": "Dans le tendon du quadriceps.", "tag": "Genou"},
        {"q": "Osgood-Schlatter ?", "type": "ouverte", "answer": "Ostéochondrose de la tubérosité tibiale antérieure (TTA).", "explanation": "Douleur croissance chez l'ado sportif.", "tag": "Pédia"},
        {"q": "Classification de Weber (Cheville) : Type B ?", "options": ["Sous les ligaments", "Au niveau de la syndesmose", "Au dessus"], "answer": "Au niveau de la syndesmose", "type": "qcm", "explanation": "Fracture de la fibula. A=Sous, B=Niveau, C=Sus (rupture membrane).", "tag": "Trauma"},
        {"q": "Tarse : Nombre d'os ?", "options": ["5", "7", "8"], "answer": "7", "type": "qcm", "explanation": "Talus, Calcanéus, Cuboïde, Naviculaire, 3 Cunéiformes.", "tag": "Pied"},
        {"q": "Ménisques du genou : Formes ?", "type": "ouverte", "answer": "Interne en C (IC), Externe en O (OE).", "explanation": "Moyen mnémotechnique : CITROEN (C-Interne, O-Externe).", "tag": "Genou"},
        {"q": "Muscle Quadriceps : combien de chefs ?", "options": ["3", "4", "2"], "answer": "4", "type": "qcm", "explanation": "Droit fémoral, Vaste interne, Vaste externe, Vaste intermédiaire.", "tag": "Myologie"},
        {"q": "Ischio-jambiers : Action principale ?", "options": ["Extension genou", "Flexion genou (+ Extension hanche)"], "answer": "Flexion genou (+ Extension hanche)", "type": "qcm", "explanation": "Antagonistes du quadriceps.", "tag": "Myologie"},
        {"q": "Triceps Sural (Mollet) : composition ?", "type": "ouverte", "answer": "Gastrocnémiens (Jumeaux) + Soléaire.", "explanation": "Se terminent par le tendon d'Achille.", "tag": "Myologie"},
        {"q": "Os du tarse postérieur ?", "type": "ouverte", "answer": "Talus (Astragale) et Calcanéus.", "explanation": "Le Talus s'articule avec le Tibia.", "tag": "Pied"},
        {"q": "Malléole externe : quel os ?", "options": ["Tibia", "Fibula (Péroné)"], "answer": "Fibula (Péroné)", "type": "qcm", "explanation": "La malléole interne est sur le Tibia.", "tag": "Cheville"},
        {"q": "Ligament Latéral Externe (Cheville) : faisceaux ?", "options": ["3", "1", "5"], "answer": "3", "type": "qcm", "explanation": "Antérieur (talofibulaire), Moyen (calcanéofibulaire), Postérieur. L'antérieur casse dans l'entorse classique.", "tag": "Cheville"},
        {"q": "Artère principale de la cuisse ?", "answer": "Artère Fémorale", "type": "qcm", "options": ["Fémorale", "Humérale", "Aorte"], "explanation": "Devient artère poplitée derrière le genou.", "tag": "Vasculaire"},
        {"q": "Nerf Sciatique : trajet ?", "type": "ouverte", "answer": "Sort de la fesse, descend face postérieure cuisse, se divise en tibial et fibulaire commun.", "explanation": "Le plus gros nerf du corps.", "tag": "Neuro"},
        {"q": "Hanche : type d'articulation ?", "options": ["Sphéroïde (Enarthrose)", "Ginglyme (Charnière)"], "answer": "Sphéroïde (Enarthrose)", "type": "qcm", "explanation": "3 degrés de liberté (très mobile).", "tag": "Hanche"},

        # CRÂNE & FACE
        {"q": "Squelette tête : 2 parties ?", "options": ["Crâne et Face", "Haut et Bas"], "answer": "Crâne et Face", "type": "qcm", "explanation": "Crâne (Neurocrâne) protège encéphale. Face (Viscérocrâne) organes sens.", "tag": "Crâne"},
        {"q": "Combien d'os au crâne ?", "options": ["8", "14", "22"], "answer": "8", "type": "qcm", "explanation": "Frontal, Occipital, Sphénoïde, Ethmoïde (impairs) + 2 Pariétaux, 2 Temporaux (pairs).", "tag": "Crâne"},
        {"q": "Combien d'os à la face ?", "options": ["14", "8"], "answer": "14", "type": "qcm", "explanation": "Dont Mandibule, Vomer (impairs).", "tag": "Face"},
        {"q": "Seul os mobile de la face ?", "answer": "Mandibule", "type": "qcm", "options": ["Maxillaire", "Mandibule"], "explanation": "S'articule avec l'os temporal (ATM).", "tag": "Face"},
        {"q": "Fontanelles : combien à la naissance ?", "options": ["2", "4", "6"], "answer": "6", "type": "qcm", "explanation": "Bregma (grande), Lambda (petite), + Ptériques et Astériques.", "tag": "Crâne"},
        {"q": "Os Zygomatique : localisation ?", "options": ["Pommette", "Nez", "Mâchoire"], "answer": "Pommette", "type": "qcm", "explanation": "Bord latéral de l'orbite.", "tag": "Face"},

        # NEURO-ANATOMIE
        {"q": "Composition du SNC ?", "options": ["Encéphale + Moelle épinière", "Cerveau + Nerfs"], "answer": "Encéphale + Moelle épinière", "type": "qcm", "explanation": "Protégé par os (crâne/rachis) et méninges.", "tag": "Neuro"},
        {"q": "Composition de l'Encéphale ?", "type": "ouverte", "answer": "Cerveau + Cervelet + Tronc Cérébral.", "explanation": "Situé dans la boîte crânienne.", "tag": "Neuro"},
        {"q": "Substance grise vs Blanche ?", "type": "ouverte", "answer": "Grise = Corps cellulaires (Cortex, Noyaux). Blanche = Axones/Fibres (Myéline).", "explanation": "La myéline donne la couleur blanche (graisse).", "tag": "Neuro"},
        {"q": "Lobe occipital : fonction principale ?", "options": ["Vision", "Audition", "Motricité"], "answer": "Vision", "type": "qcm", "explanation": "Cortex visuel primaire.", "tag": "Neuro"},
        {"q": "Où circule le LCS (Liquide Cérébro-Spinal) ?", "options": ["Espace Sous-Arachnoïdien", "Espace Épidural"], "answer": "Espace Sous-Arachnoïdien", "type": "qcm", "explanation": "Entre l'arachnoïde et la pie-mère.", "tag": "Neuro"},
        {"q": "Rôle du Cervelet ?", "type": "ouverte", "answer": "Équilibre, Coordination, Tonus, Apprentissage moteur.", "explanation": "Chef d'orchestre du mouvement.", "tag": "Neuro"},
        {"q": "Système Pyramidal vs Extra-pyramidal ?", "type": "ouverte", "answer": "Pyramidal = Motricité volontaire. Extra-pyramidal = Automatique/Involontaire/Tonus.", "explanation": "Le bébé est d'abord extra-pyramidal (réflexes).", "tag": "Neuro"},

        # ANATO RACHIS & CRÂNE
        {"q": "Disque intervertébral : composition ?", "type": "ouverte", "answer": "Nucleus Pulposus (Noyau gélatineux) + Annulus Fibrosus (Anneau fibreux).", "explanation": "Hernie discale = le noyau sort de l'anneau.", "tag": "Rachis"},
        {"q": "Atlas (C1) : particularité ?", "options": ["Pas de corps vertébral", "Pas de trou"], "answer": "Pas de corps vertébral", "type": "qcm", "explanation": "C'est un anneau osseux.", "tag": "Rachis"},
        {"q": "Os Sphénoïde : forme ?", "options": ["Chauve-souris / Papillon", "Cube", "Disque"], "answer": "Chauve-souris / Papillon", "type": "qcm", "explanation": "Os clé de la base du crâne, s'articule avec presque tous les autres.", "tag": "Crâne"},
        {"q": "Suture coronale : entre quels os ?", "options": ["Frontal et Pariétaux", "Pariétaux et Occipital"], "answer": "Frontal et Pariétaux", "type": "qcm", "explanation": "Suture sagittale = entre les deux pariétaux.", "tag": "Crâne"},
        {"q": "Muscles masticateurs principaux ?", "type": "ouverte", "answer": "Masséter et Temporal.", "explanation": "Ferment la mâchoire.", "tag": "Face"},
        {"q": "Nerf Facial (VII) : fonction ?", "options": ["Motricité de la face (mimique)", "Sensibilité de la face"], "answer": "Motricité de la face (mimique)", "type": "qcm", "explanation": "Si paralysie faciale : visage asymétrique.", "tag": "Neuro"},
        {"q": "Polygone de Willis : c'est quoi ?", "type": "ouverte", "answer": "Cercle artériel à la base du cerveau assurant la vascularisation et la suppléance.", "explanation": "Réunion des carotides internes et vertébrales.", "tag": "Vasculaire"},
        {"q": "Trou occipital (Foramen Magnum) : que passe-t-il ?", "options": ["Moelle épinière / Tronc cérébral", "Nerf optique"], "answer": "Moelle épinière / Tronc cérébral", "type": "qcm", "explanation": "Jonction crâne-rachis.", "tag": "Crâne"},
    ],

    "MODULE 3: Physiologie": [
        # CELLULE & HOMÉOSTASIE
        {"q": "Définition de l'homéostasie ?", "type": "ouverte", "answer": "Capacité de l'organisme à maintenir son milieu intérieur stable (pH, T°, glycémie) malgré les variations extérieures.", "explanation": "Claude Bernard. Vital pour la survie cellulaire.", "tag": "Cellule"},
        {"q": "Quelle organite produit l'énergie (ATP) de la cellule ?", "options": ["Noyau", "Mitochondrie", "Ribosome"], "answer": "Mitochondrie", "type": "qcm", "explanation": "La 'centrale électrique' de la cellule via la respiration cellulaire.", "tag": "Cellule"},
        {"q": "Milieu Intérieur : composition ?", "type": "ouverte", "answer": "Liquide extracellulaire : Plasma (sang) + Liquide Interstitiel (entre les cellules).", "explanation": "Représente environ 20% du poids du corps.", "tag": "Cellule"},
        {"q": "Transport actif vs passif ?", "type": "ouverte", "answer": "Passif = sans énergie, suit le gradient de concentration. Actif = consomme ATP, contre le gradient.", "explanation": "Ex: Pompe Na+/K+ est un transport actif.", "tag": "Cellule"},
        {"q": "Osmose : définition ?", "type": "ouverte", "answer": "Mouvement d'eau à travers une membrane semi-perméable du milieu le moins concentré vers le plus concentré.", "explanation": "Pour équilibrer les concentrations.", "tag": "Cellule"},

        # NEUROPHYSIOLOGIE
        {"q": "Potentiel de repos d'un neurone : valeur ?", "options": ["0 mV", "-70 mV", "+30 mV"], "answer": "-70 mV", "type": "qcm", "explanation": "L'intérieur est négatif par rapport à l'extérieur.", "tag": "Neurophy"},
        {"q": "Loi du 'Tout ou Rien' ?", "type": "ouverte", "answer": "Si le seuil de dépolarisation est atteint, le PA se déclenche avec la même amplitude. Sinon, rien ne se passe.", "explanation": "Le PA ne varie pas en intensité, mais en fréquence.", "tag": "Neurophy"},
        {"q": "Rôle de la Myéline ?", "options": ["Nourrir le neurone", "Accélérer la conduction (conduction saltatoire)", "Freiner le message"], "answer": "Accélérer la conduction (conduction saltatoire)", "type": "qcm", "explanation": "L'influx saute de nœud de Ranvier en nœud de Ranvier.", "tag": "Neurophy"},
        {"q": "Synapse chimique : étapes ?", "type": "ouverte", "answer": "1. Arrivée PA -> 2. Entrée Ca2+ -> 3. Libération neurotransmetteur -> 4. Fixation sur récepteurs post-synaptiques.", "explanation": "Transforme un signal électrique en signal chimique.", "tag": "Neurophy"},
        {"q": "Neurotransmetteur inhibiteur principal ?", "options": ["Glutamate", "GABA", "Dopamine"], "answer": "GABA", "type": "qcm", "explanation": "Le Glutamate est excitateur.", "tag": "Neurophy"},

        # MUSCLE
        {"q": "Unité contractile du muscle ?", "options": ["Sarcomère", "Sarcolemme", "Tubule T"], "answer": "Sarcomère", "type": "qcm", "explanation": "Situé entre deux stries Z.", "tag": "Muscle"},
        {"q": "Quel ion déclenche la contraction musculaire ?", "options": ["Sodium", "Calcium (Ca2+)", "Potassium"], "answer": "Calcium (Ca2+)", "type": "qcm", "explanation": "Libéré par le réticulum sarcoplasmique, il se fixe sur la troponine.", "tag": "Muscle"},
        {"q": "Rôle de l'ATP dans la contraction ?", "type": "ouverte", "answer": "Permet le détachement de la tête de myosine et son redressement.", "explanation": "Sans ATP = Rigidité cadavérique (Rigor Mortis).", "tag": "Muscle"},
        {"q": "Types de fibres musculaires ?", "type": "ouverte", "answer": "Type I (Lentes, rouges, endurantes) et Type II (Rapides, blanches, explosives).", "explanation": "I = Posture. II = Sprint.", "tag": "Muscle"},
        {"q": "Tétanos physiologique ?", "type": "ouverte", "answer": "Contraction maintenue et lisse due à la sommation temporelle des stimulations nerveuses.", "explanation": "C'est le mode normal de contraction volontaire.", "tag": "Muscle"},

        # CARDIO-VASCULAIRE
        {"q": "Petite vs Grande Circulation ?", "type": "ouverte", "answer": "Petite (Pulmonaire) = Cœur Droit -> Poumons -> Cœur Gauche (Oxygénation). Grande (Systémique) = Cœur Gauche -> Corps -> Cœur Droit.", "explanation": "Circulation en série.", "tag": "Cardio"},
        {"q": "Débit Cardiaque (Formule) ?", "options": ["FC x Pression", "FC x VES (Volume d'Éjection Systolique)", "Pression / Résistance"], "answer": "FC x VES (Volume d'Éjection Systolique)", "type": "qcm", "explanation": "Environ 5L/min au repos.", "tag": "Cardio"},
        {"q": "Tension Artérielle : 12/8 signifie ?", "type": "ouverte", "answer": "120 mmHg de pression systolique (max) et 80 mmHg de pression diastolique (min).", "explanation": "Pression exercée par le sang sur la paroi des artères.", "tag": "Cardio"},
        {"q": "Retour veineux : facteurs favorisants ?", "type": "ouverte", "answer": "Pompe musculaire (mollets), valvules anti-reflux, aspiration thoracique (respiration).", "explanation": "La marche favorise le retour veineux.", "tag": "Cardio"},
        {"q": "Bruits du cœur (Boum-Tac) ?", "type": "ouverte", "answer": "B1 = Fermeture valves Auriculo-Ventriculaires (Mitrale/Tricuspide). B2 = Fermeture valves Artérielles (Aortique/Pulmonaire).", "explanation": "Correspondent au début systole et début diastole.", "tag": "Cardio"},
        {"q": "ECG : Onde P correspond à ?", "options": ["Dépolarisation Auriculaire", "Dépolarisation Ventriculaire", "Repolarisation"], "answer": "Dépolarisation Auriculaire", "type": "qcm", "explanation": "QRS = Ventricules. T = Repolarisation.", "tag": "Cardio"},
        {"q": "Barorécepteurs : rôle ?", "type": "ouverte", "answer": "Capteurs de pression (Crosse aortique/Carotide) qui régulent la TA via le système nerveux autonome.", "explanation": "Réflexe rapide (ex: se lever vite).", "tag": "Cardio"},

        # RESPIRATOIRE
        {"q": "Surfactant : rôle ?", "options": ["Tuer les bactéries", "Empêcher le collapsus alvéolaire (réduit tension superficielle)", "Transporter O2"], "answer": "Empêcher le collapsus alvéolaire (réduit tension superficielle)", "type": "qcm", "explanation": "Manque chez le prématuré.", "tag": "Respi"},
        {"q": "Volume Courant (VC) moyen ?", "options": ["0.5 L", "1.5 L", "3 L"], "answer": "0.5 L", "type": "qcm", "explanation": "Volume d'air inspiré/expiré au repos.", "tag": "Respi"},
        {"q": "Capacité Vitale ?", "type": "ouverte", "answer": "Volume max mobilisable (VC + VRI + VRE).", "explanation": "Tout sauf le volume résiduel.", "tag": "Respi"},
        {"q": "Transport de l'Oxygène ?", "options": ["Dissous dans le plasma", "Lié à l'hémoglobine (98%)"], "answer": "Lié à l'hémoglobine (98%)", "type": "qcm", "explanation": "4 molécules d'O2 par hémoglobine.", "tag": "Respi"},
        {"q": "Contrôle de la respiration : quel gaz est le stimulus principal ?", "options": ["Manque d'O2", "Excès de CO2"], "answer": "Excès de CO2", "type": "qcm", "explanation": "L'hypercapnie déclenche l'inspiration réflexe.", "tag": "Respi"},
        {"q": "Hématose : lieu ?", "answer": "Alvéoles pulmonaires", "type": "qcm", "options": ["Bronches", "Alvéoles pulmonaires", "Trachée"], "explanation": "Barrière alvéolo-capillaire très fine.", "tag": "Respi"},

        # RÉNAL & LIQUIDES
        {"q": "Filtration glomérulaire : sélectivité ?", "type": "ouverte", "answer": "Laisse passer eau/ions/déchets. Ne laisse PAS passer grosses protéines (Albumine) ni cellules sanguines.", "explanation": "Si protéines dans urines = problème rénal.", "tag": "Rénal"},
        {"q": "Réabsorption : où va l'eau filtrée ?", "options": ["Dans l'urine", "Retourne dans le sang (99%)"], "answer": "Retourne dans le sang (99%)", "type": "qcm", "explanation": "On filtre 180L/jour mais on urine 1.5L.", "tag": "Rénal"},
        {"q": "Système Rénine-Angiotensine-Aldostérone (SRAA) : but ?", "type": "ouverte", "answer": "Remonter la tension artérielle (Vasoconstriction + Réabsorption eau/sel).", "explanation": "Activé en cas d'hypotension/hémorragie.", "tag": "Rénal"},
        {"q": "ADH (Hormone Antidiurétique) ?", "type": "ouverte", "answer": "Sécrétée par l'hypophyse, elle augmente la réabsorption d'eau pure pour concentrer les urines.", "explanation": "Agit en cas de déshydratation.", "tag": "Rénal"},
        {"q": "Équilibre Acide-Base : rôle du rein ?", "type": "ouverte", "answer": "Éliminer les ions H+ (acides) et réabsorber les Bicarbonates (basiques).", "explanation": "Régulation lente (vs poumon rapide).", "tag": "Rénal"},

        # DIGESTIF
        {"q": "Enzyme salivaire ?", "options": ["Pepsine", "Amylase"], "answer": "Amylase", "type": "qcm", "explanation": "Débute la digestion des glucides (amidon).", "tag": "Digestif"},
        {"q": "Estomac : pH ?", "options": ["Acide (1-2)", "Neutre (7)", "Basique (9)"], "answer": "Acide (1-2)", "type": "qcm", "explanation": "L'acide chlorhydrique tue les bactéries et active la pepsine.", "tag": "Digestif"},
        {"q": "Où se fait l'absorption des nutriments ?", "options": ["Estomac", "Intestin Grêle (Jéjunum/Iléon)", "Côlon"], "answer": "Intestin Grêle (Jéjunum/Iléon)", "type": "qcm", "explanation": "Grande surface grâce aux villosités.", "tag": "Digestif"},
        {"q": "Rôle du Pancréas exocrine ?", "type": "ouverte", "answer": "Sécréter le suc pancréatique (enzymes digestives + bicarbonates pour neutraliser l'acidité).", "explanation": "Lipase, Protéase, Amylase.", "tag": "Digestif"},
        {"q": "Foie : Rôle métabolique ?", "type": "ouverte", "answer": "Stockage glycogène, synthèse protéines (albumine), détoxification, production bile.", "explanation": "Usine chimique du corps.", "tag": "Digestif"},
        {"q": "Bile : stockage ?", "answer": "Vésicule biliaire", "type": "qcm", "options": ["Foie", "Vésicule biliaire", "Pancréas"], "explanation": "Produite par le foie en continu, stockée et concentrée.", "tag": "Digestif"},

        # ENDOCRINO & NERVEUX AUTONOME
        {"q": "Insuline : effet ?", "options": ["Hypoglycémiant", "Hyperglycémiant"], "answer": "Hypoglycémiant", "type": "qcm", "explanation": "Fait entrer le sucre dans les cellules. Seule hormone hypoglycémiante.", "tag": "Endocrino"},
        {"q": "Glucagon : effet ?", "options": ["Hypoglycémiant", "Hyperglycémiant"], "answer": "Hyperglycémiant", "type": "qcm", "explanation": "Libère le sucre stocké dans le foie.", "tag": "Endocrino"},
        {"q": "Système Sympathique : effets ?", "type": "ouverte", "answer": "Fuite ou Combat : Augmente FC, Dilate pupilles, Bronchodilatation, Ralentit digestion.", "explanation": "Médiateur : Adrénaline/Noradrénaline.", "tag": "SNA"},
        {"q": "Système Parasympathique : effets ?", "type": "ouverte", "answer": "Repos et Digestion : Ralentit FC, Myosis, Active digestion.", "explanation": "Médiateur : Acétylcholine (Nerf Vague).", "tag": "SNA"},
        {"q": "Cortisol : hormone de... ?", "options": ["Sommeil", "Stress", "Croissance"], "answer": "Stress", "type": "qcm", "explanation": "Anti-inflammatoire et hyperglycémiant.", "tag": "Endocrino"},
        {"q": "Axe Hypothalamo-Hypophysaire ?", "type": "ouverte", "answer": "Chef d'orchestre endocrinien. L'hypothalamus commande l'hypophyse qui commande les glandes (Thyroïde, Surrénales, Gonades).", "explanation": "Rétrocontrôle négatif (Feedback).", "tag": "Endocrino"},
    ],

    "MODULE 4: Psychologie": [
        # GÉNÉRALITÉS & DÉVELOPPEMENT
        {"q": "Définition Affect ?", "type": "ouverte", "answer": "État émotionnel immédiat, ressenti dans le corps et la psyché, avec une tonalité (plaisir/douleur).", "explanation": "Brut et immédiat.", "tag": "Déf"},
        {"q": "Différence Émotion / Sentiment ?", "type": "ouverte", "answer": "Émotion = Réaction physio/comportementale brève à un événement. Sentiment = État affectif durable et stabilisé, intégré à la conscience.", "explanation": "La peur est une émotion, l'amour est un sentiment.", "tag": "Déf"},
        {"q": "Relation d'Objet (Déf) ?", "type": "ouverte", "answer": "Manière dont le sujet se relie à l'autre (l'objet) et dont il l'a intériorisé.", "explanation": "L'objet est ce qui permet la satisfaction de la pulsion.", "tag": "Psycho"},
        {"q": "Inné vs Acquis ?", "type": "ouverte", "answer": "Inné = Bagage génétique/biologique. Acquis = Environnement/Expérience. Le développement est une interaction des deux.", "explanation": "Epigénétique.", "tag": "Dvlpmt"},
        
        # FREUD & PSYCHANALYSE
        {"q": "Pulsion (Trieb) : définition ?", "type": "ouverte", "answer": "Poussée énergétique issue du corps tendant vers un but (satisfaction) via un objet.", "explanation": "Source -> Poussée -> But -> Objet.", "tag": "Freud"},
        {"q": "1ère Topique ?", "options": ["Ça/Moi/Surmoi", "Inconscient/Préconscient/Conscient"], "answer": "Inconscient/Préconscient/Conscient", "type": "qcm", "explanation": "Image de l'iceberg. 1900.", "tag": "Freud"},
        {"q": "2ème Topique ?", "options": ["Ça/Moi/Surmoi", "Inconscient/Préconscient/Conscient"], "answer": "Ça/Moi/Surmoi", "type": "qcm", "explanation": "Structure dynamique. 1920.", "tag": "Freud"},
        {"q": "Le Ça ?", "type": "ouverte", "answer": "Pôle pulsionnel, totalement inconscient, régi par le principe de plaisir. Pas de temps, pas de logique.", "explanation": "Réservoir de la libido.", "tag": "Freud"},
        {"q": "Le Moi ?", "type": "ouverte", "answer": "Médiateur entre le Ça, le Surmoi et la Réalité. Pôle défensif.", "explanation": "Régi par le principe de réalité.", "tag": "Freud"},
        {"q": "Le Surmoi ?", "type": "ouverte", "answer": "Instance morale, interdits intériorisés, Idéal du Moi. Héritier du complexe d'Oedipe.", "explanation": "Juge et censeur.", "tag": "Freud"},
        {"q": "Stade Oral : Zone et Mode ?", "type": "ouverte", "answer": "Zone : Bouche. Mode : Incorporation (sucer, mordre).", "explanation": "Relation anaclitique (étayage).", "tag": "Freud"},
        {"q": "Stade Anal : Enjeux ?", "type": "ouverte", "answer": "Contrôle, Propreté, Autonomie, Ambivalence (Don/Retenue), Sadisme/Masochisme.", "explanation": "L'enfant dit 'Non'.", "tag": "Freud"},
        {"q": "Stade Phallique : Angoisse principale ?", "options": ["Abandon", "Morcellement", "Castration"], "answer": "Castration", "type": "qcm", "explanation": "Peur de perdre la puissance/l'intégrité.", "tag": "Freud"},
        {"q": "Période de Latence (6-12 ans) ?", "type": "ouverte", "answer": "Mise en veille des pulsions sexuelles. Investissement des apprentissages scolaires et sociaux (sublimation).", "explanation": "Calme avant la tempête ado.", "tag": "Freud"},
        {"q": "Mécanisme de Défense : Refoulement ?", "type": "ouverte", "answer": "Rejet dans l'inconscient de représentations inconciliables avec le Moi.", "explanation": "Défense principale de la névrose.", "tag": "Défense"},
        {"q": "Mécanisme : Projection ?", "type": "ouverte", "answer": "Attribuer à l'autre ses propres désirs ou sentiments inavouables.", "explanation": "'Il me déteste' (alors que c'est moi qui le déteste).", "tag": "Défense"},
        {"q": "Mécanisme : Déni ?", "options": ["Oublier", "Refuser de reconnaître la réalité d'une perception", "Transformer en contraire"], "answer": "Refuser de reconnaître la réalité d'une perception", "type": "qcm", "explanation": "Porte sur la réalité extérieure (≠ refoulement intrapsychique).", "tag": "Défense"},

        # WINNICOTT
        {"q": "Mère suffisamment bonne ?", "type": "ouverte", "answer": "Mère qui s'adapte activement aux besoins du bébé au début, puis se désadapte progressivement pour favoriser l'autonomie.", "explanation": "Ni parfaite, ni carencée.", "tag": "Winnicott"},
        {"q": "Holding ?", "type": "ouverte", "answer": "Manière de tenir/porter le bébé (physiquement et psychiquement). Fonction de maintien.", "explanation": "Permet l'intégration du Moi.", "tag": "Winnicott"},
        {"q": "Handling ?", "type": "ouverte", "answer": "Soins corporels, manipulations. Permet l'habitation du corps (Psyché dans Soma).", "explanation": "Personnalisation.", "tag": "Winnicott"},
        {"q": "Object Presenting ?", "type": "ouverte", "answer": "Présentation du monde/objet au moment où l'enfant a l'illusion de le créer.", "explanation": "Illusion de toute-puissance créatrice.", "tag": "Winnicott"},
        {"q": "Objet Transitionnel : caractéristiques ?", "type": "ouverte", "answer": "Objet trouvé-créé, doit survivre à l'amour et à la haine (agressivité), ni moi ni non-moi.", "explanation": "Doudou. Aire de jeu.", "tag": "Winnicott"},
        {"q": "Capacité à être seul ?", "type": "ouverte", "answer": "Être seul en présence de quelqu'un (au début). Signe de sécurité interne.", "explanation": "L'objet est intériorisé.", "tag": "Winnicott"},
        {"q": "Vrai Self vs Faux Self ?", "type": "ouverte", "answer": "Vrai Self = Geste spontané, vivant. Faux Self = Adaptation excessive à l'environnement pour se protéger (carapace).", "explanation": "Faux self pathologique si coupe du vrai self.", "tag": "Winnicott"},

        # BOWLBY & ATTACHEMENT
        {"q": "Définition Attachement ?", "type": "ouverte", "answer": "Besoin inné de proximité avec une figure spécifique pour la protection.", "explanation": "Système comportemental activé par le stress.", "tag": "Bowlby"},
        {"q": "Caregiving ?", "type": "ouverte", "answer": "Système de soin des parents répondant aux besoins d'attachement de l'enfant.", "explanation": "Réponse sensible et appropriée.", "tag": "Bowlby"},
        {"q": "Base de sécurité ?", "type": "ouverte", "answer": "L'enfant explore le monde s'il sait qu'il peut revenir vers la figure d'attachement en cas de danger.", "explanation": "Équilibre Exploration / Attachement.", "tag": "Bowlby"},
        {"q": "Attachement Sécure (B) ?", "type": "ouverte", "answer": "Détresse à la séparation, réconfort rapide au retour, retour à l'exploration.", "explanation": "Confiance.", "tag": "Bowlby"},
        {"q": "Attachement Anxieux-Évitant (A) ?", "type": "ouverte", "answer": "Indifférence apparente à la séparation et au retour. Focalisation sur les objets.", "explanation": "Défense contre le rejet.", "tag": "Bowlby"},
        {"q": "Attachement Résistant/Ambivalent (C) ?", "type": "ouverte", "answer": "Détresse massive, inconsolable au retour (colère/accrochage), pas d'exploration.", "explanation": "Réponse parentale imprévisible.", "tag": "Bowlby"},
        {"q": "MIO (Modèles Internes Opérants) ?", "type": "ouverte", "answer": "Représentations mentales de soi et des autres construites à partir des expériences d'attachement.", "explanation": "Filtrent les relations futures.", "tag": "Bowlby"},

        # AUTRES AUTEURS (Spitz, Klein, Wallon, Bion)
        {"q": "Spitz : Hospitalisme ?", "type": "ouverte", "answer": "Dépression grave et dépérissement des bébés en institution privés de lien affectif (carence affective totale).", "explanation": "Suit la dépression anaclitique.", "tag": "Spitz"},
        {"q": "Spitz : Les 3 organisateurs ?", "options": ["Sourire, Angoisse 8 mois, Non", "Marche, Langage, Propreté"], "answer": "Sourire, Angoisse 8 mois, Non", "type": "qcm", "explanation": "Étapes structurantes du psychisme.", "tag": "Spitz"},
        {"q": "Angoisse du 8ème mois ?", "type": "ouverte", "answer": "L'enfant différencie sa mère des étrangers. Peur de l'étranger = signe que la mère est l'objet d'amour spécifique.", "explanation": "Preuve de l'objet libidinal.", "tag": "Spitz"},
        {"q": "Mélanie Klein : Position Schizo-Paranoïde (0-4 mois) ?", "type": "ouverte", "answer": "Clivage Bon/Mauvais objet. Angoisse de persécution/morcellement.", "explanation": "Mécanisme archaïque.", "tag": "Klein"},
        {"q": "Mélanie Klein : Position Dépressive (4-6 mois) ?", "type": "ouverte", "answer": "Unification de l'objet (Mère totale). Ambivalence (Amour/Haine). Culpabilité et désir de réparation.", "explanation": "Accès à la gratitude.", "tag": "Klein"},
        {"q": "Identification Projective (Klein) ?", "type": "ouverte", "answer": "Mettre en l'autre des parties de soi (bonnes ou mauvaises) pour les contrôler ou s'en débarrasser.", "explanation": "Base de l'empathie ou de la pathologie.", "tag": "Klein"},
        {"q": "Bion : Fonction Alpha ?", "type": "ouverte", "answer": "Capacité de la mère (Rêverie) à digérer les impressions sensorielles brutes (Bêta) du bébé pour les rendre pensables (Alpha).", "explanation": "Permet de construire l'appareil à penser.", "tag": "Bion"},
        {"q": "Bion : Contenant / Contenu ?", "type": "ouverte", "answer": "La mère sert de contenant psychique aux angoisses (contenu) de l'enfant.", "explanation": "Nécessaire pour la sécurité.", "tag": "Bion"},
        {"q": "Wallon : Acte moteur et mental ?", "type": "ouverte", "answer": "L'acte moteur prépare l'acte mental. La pensée naît de l'action et de l'interaction.", "explanation": "Psychologie génétique.", "tag": "Wallon"},
        {"q": "Stade du Miroir (Wallon/Lacan) : âge ?", "options": ["6-18 mois", "0-3 mois", "3 ans"], "answer": "6-18 mois", "type": "qcm", "explanation": "Jubilation devant l'image unifiée. Sortie du corps morcelé.", "tag": "Wallon"},

        # COMMUNICATION NON VERBALE (CNV) & TOUCHER
        {"q": "Canaux de la CNV ?", "type": "ouverte", "answer": "Visage (mimiques), Regard, Posture, Gestes, Toucher, Proxémie, Apparence, Paralangage (voix).", "explanation": "Tout sauf les mots.", "tag": "CNV"},
        {"q": "Proxémie (Hall) : Distance intime ?", "options": ["0-45 cm", "45cm-1m20", "> 3m"], "answer": "0-45 cm", "type": "qcm", "explanation": "Zone du soin, du toucher, de l'affect. Risque d'intrusion.", "tag": "CNV"},
        {"q": "Distance Personnelle ?", "options": ["45cm - 1.20m", "1.20m - 3.60m"], "answer": "45cm - 1.20m", "type": "qcm", "explanation": "Bulle 'longueur de bras'. Interaction amicale.", "tag": "CNV"},
        {"q": "Toucher instrumental vs Relationnel ?", "type": "ouverte", "answer": "Instrumental = Technique, utilitaire (soin). Relationnel = Affectif, rassurant, communiquant.", "explanation": "En psychomot, on lie les deux.", "tag": "Toucher"},
        {"q": "Haptique : définition ?", "type": "ouverte", "answer": "Science du toucher et de la kinesthésie. Sens actif d'exploration.", "explanation": "Pas seulement passif (être touché) mais actif (toucher).", "tag": "Toucher"},
        {"q": "Peau : fonctions psychiques (Anzieu) ?", "type": "ouverte", "answer": "Moi-Peau : Contenance (Sac), Limite (Frontière dedans/dehors), Communication (Inscriptions).", "explanation": "Enveloppe psychique.", "tag": "Concept"},
        {"q": "Effet du toucher (Guéguen) ?", "type": "ouverte", "answer": "Augmente la compliance, la confiance, l'humeur positive.", "explanation": "Preuves expérimentales (ex: main sur épaule).", "tag": "Toucher"},
        {"q": "Regard : fonction ?", "type": "ouverte", "answer": "Régulation de l'échange, Feedback, Expression émotionnelle, Attention conjointe.", "explanation": "Premier organisateur (Spitz : le visage).", "tag": "CNV"},
        {"q": "Congruence ?", "type": "ouverte", "answer": "Accord entre le verbal (mots) et le non-verbal (corps).", "explanation": "Si discordance = Double Contrainte (pathogène).", "tag": "CNV"},
    ],

    "MODULE 5: Psychiatrie": [
        # HISTOIRE & CADRE LÉGAL
        {"q": "Philippe Pinel (1793) : acte fondateur ?", "options": ["Invente les médicaments", "Libère les aliénés de leurs chaînes (Bicêtre)", "Invente la psychanalyse"], "answer": "Libère les aliénés de leurs chaînes (Bicêtre)", "type": "qcm", "explanation": "Naissance du 'Traitement Moral' et de la psychiatrie moderne.", "tag": "Histoire"},
        {"q": "Loi du 30 juin 1838 (Esquirol) ?", "type": "ouverte", "answer": "Oblige chaque département à avoir un asile d'aliénés. Crée le Placement Volontaire (PV) et le Placement d'Office (PO).", "explanation": "Institutionnalise l'enfermement.", "tag": "Loi"},
        {"q": "Politique de Sectorisation (1960) ?", "type": "ouverte", "answer": "Découpage géo-démographique (1 secteur = ~70 000 hab). Une même équipe suit le patient à l'hôpital et à l'extérieur (CMP).", "explanation": "But : soigner le malade près de chez lui, continuité des soins, 'hors les murs'.", "tag": "Orga"},
        {"q": "Loi de 2011 (réformant 1990) : Nouveaux termes pour HDT et HO ?", "options": ["ASPDT et ASPBRE", "SPDT et SPDRE", "PV et PO"], "answer": "SPDT et SPDRE", "type": "qcm", "explanation": "Soins Psychiatriques à la Demande d'un Tiers (urgence ou péril imminent) / Soins Psychiatriques sur Décision du Représentant de l'État.", "tag": "Loi"},
        {"q": "CMP (Centre Médico-Psychologique) : rôle ?", "type": "ouverte", "answer": "Pivot du secteur. Soins ambulatoires (consultations, suivi) gratuits. Premier lieu d'accueil.", "explanation": "Permet d'éviter l'hospitalisation.", "tag": "Orga"},
        
        # SÉMIOLOGIE (SYMPTÔMES)
        {"q": "Différence Hallucination Psychosensorielle vs Psychique ?", "type": "ouverte", "answer": "Psychosensorielle = Perçue par les sens (entendre une voix par l'oreille, voir qqch). Psychique = Voix intérieure, pensée imposée, sans sensorialité.", "explanation": "Psychique = Syndrome d'automatisme mental.", "tag": "Sémio"},
        {"q": "Clinophilie : définition ?", "options": ["Aimer l'hôpital", "Rester couché au lit toute la journée sans dormir", "Aimer le chaud"], "answer": "Rester couché au lit toute la journée sans dormir", "type": "qcm", "explanation": "Signe de repli ou de dépression (apragmatisme).", "tag": "Sémio"},
        {"q": "Incurie : définition ?", "type": "ouverte", "answer": "Négligence totale de l'hygiène corporelle et vestimentaire.", "explanation": "Fréquent dans la schizophrénie ou la dépression grave (Diogène).", "tag": "Sémio"},
        {"q": "Logorrhée ?", "options": ["Mutisme", "Flux de parole rapide et incessant", "Bégaiement"], "answer": "Flux de parole rapide et incessant", "type": "qcm", "explanation": "Typique de l'état maniaque.", "tag": "Sémio"},
        {"q": "Différence Angoisse vs Anxiété ?", "type": "ouverte", "answer": "Anxiété = Malaise psychique, attente appréhensive. Angoisse = Anxiété paroxystique avec manifestations somatiques fortes (étouffement, palpitations).", "explanation": "L'angoisse serre la gorge (etym : angere).", "tag": "Sémio"},
        
        # PATHOLOGIES ADULTE
        {"q": "Schizophrénie : Syndrome Dissociatif (Spaltung) ?", "type": "ouverte", "answer": "Perte de l'unité psychique. Discordance entre idées, affects et comportements (ex: rire immotivé).", "explanation": "Noyau dur de la schizophrénie.", "tag": "Schizo"},
        {"q": "Schizophrénie : Symptômes Positifs vs Négatifs ?", "type": "ouverte", "answer": "Positifs = Productifs (Délires, Hallucinations). Négatifs = Déficitaires (Repli, Apragmatisme, Émoussement affectif).", "explanation": "Traitement différent (Neuroleptiques vs Stimulation).", "tag": "Schizo"},
        {"q": "Dépression : Triade symptomatique ?", "type": "ouverte", "answer": "1. Tristesse de l'humeur. 2. Ralentissement psychomoteur. 3. Signes somatiques (Insomnie, Anorexie).", "explanation": "+ Risque suicidaire majeur.", "tag": "Humeur"},
        {"q": "Trouble Bipolaire (PMD) : Épisode Maniaque ?", "type": "ouverte", "answer": "Exaltation de l'humeur, Tachypsychie (idées fusent), Logorrhée, Insomnie sans fatigue, Désinhibition, Achats compulsifs.", "explanation": "Urgence thérapeutique (Thymorégulateurs).", "tag": "Humeur"},
        {"q": "Délire Paranoïaque : mécanisme principal ?", "options": ["Hallucinatoire", "Interprétatif", "Imaginatif"], "answer": "Interprétatif", "type": "qcm", "explanation": "Interprétation fausse d'un fait réel ('Il a toussé, c'est un signal pour me tuer').", "tag": "Délire"},
        {"q": "TOC (Trouble Obsessionnel Compulsif) : définition ?", "type": "ouverte", "answer": "Obsessions (idées intrusives angoissantes) + Compulsions (rituels pour calmer l'angoisse).", "explanation": "Le patient a conscience du trouble mais ne peut s'en empêcher.", "tag": "Névrose"},
        {"q": "Phobie : Mécanisme de défense ?", "options": ["Refoulement", "Déplacement", "Déni"], "answer": "Déplacement", "type": "qcm", "explanation": "L'angoisse interne est déplacée sur un objet extérieur (l'objet phobogène).", "tag": "Névrose"},
        {"q": "Hystérie (Trouble de conversion) : symptôme principal ?", "type": "ouverte", "answer": "Conversion somatique : conflit psychique transformé en symptôme corporel sans lésion organique (paralysie, cécité, crise).", "explanation": "Belle indifférence à l'égard du symptôme.", "tag": "Névrose"},
        {"q": "Anorexie Mentale : Triade ?", "type": "ouverte", "answer": "1. Refus alimentaire (lutte contre la faim). 2. Amaigrissement. 3. Aménorrhée (arrêt des règles).", "explanation": "+ Dysmorphophobie (se voit grosse).", "tag": "TCA"},
        {"q": "Boulimie : caractéristique ?", "type": "ouverte", "answer": "Crises d'ingestion massive et compulsive, suivies de comportements compensatoires (vomissements, sport excessif) et culpabilité.", "explanation": "Le poids est souvent normal (contrairement à l'anorexie).", "tag": "TCA"},
        {"q": "Trouble Bipolaire Type 1 vs Type 2 ?", "options": ["1 = Manie / 2 = Hypomanie", "1 = Dépression / 2 = Manie"], "answer": "1 = Manie / 2 = Hypomanie", "type": "qcm", "explanation": "Type 1 : au moins un épisode maniaque complet. Type 2 : dépression majeure + hypomanie (moins intense).", "tag": "Humeur"},
        
        # PÉDOPSYCHIATRIE
        {"q": "Autisme (TSA) : Dyade DSM-5 ?", "type": "ouverte", "answer": "1. Déficit communication/interactions sociales. 2. Caractère restreint et répétitif des comportements/intérêts.", "explanation": "Avant c'était une Triade (TED).", "tag": "Pédopsy"},
        {"q": "Hospitalisme (Spitz) ?", "type": "ouverte", "answer": "État d'altération physique et psychique profond dû à une carence affective totale en institution.", "explanation": "Dépression anaclitique -> Hospitalisme (irréversible).", "tag": "Pédopsy"},
        {"q": "Dysharmonie Évolutive (CFTMEA) ?", "type": "ouverte", "answer": "Pathologie limite. Développement hétérogène (secteurs matures et immatures), angoisses archaïques, instabilité.", "explanation": "Spécificité française.", "tag": "Pédopsy"},
        {"q": "Trouble de l'Attachement (Carence) ?", "type": "ouverte", "answer": "Conséquence de ruptures ou négligences précoces. Retrait social ou sociabilité indiscriminée.", "explanation": "Touche la sécurité de base.", "tag": "Pédopsy"},
        
        # THÉRAPEUTIQUES
        {"q": "Neuroleptiques (Antipsychotiques) : effet principal ?", "options": ["Calmer l'angoisse", "Réduire délires et hallucinations", "Faire dormir"], "answer": "Réduire délires et hallucinations", "type": "qcm", "explanation": "Bloquent la Dopamine. Effets secondaires : Syndrome extra-pyramidal (raideur, tremblement).", "tag": "Pharma"},
        {"q": "Thymorégulateurs : pour quelle maladie ?", "options": ["Dépression", "Trouble Bipolaire", "Schizophrénie"], "answer": "Trouble Bipolaire", "type": "qcm", "explanation": "Ex: Lithium. Pour stabiliser l'humeur.", "tag": "Pharma"},
        {"q": "Psychothérapie Institutionnelle ?", "type": "ouverte", "answer": "Soigner l'institution pour soigner les malades. Utiliser le quotidien, les réunions, le club thérapeutique comme outils de soin.", "explanation": "Oury, Tosquelles.", "tag": "Soin"},
        {"q": "Catatonie : symptômes moteurs ?", "type": "ouverte", "answer": "Immobilité, Stupeur, Négativisme, Flexibilité cireuse (garde la pose), Catalepsie.", "explanation": "Urgence (risque vital).", "tag": "Sémio"},
        # SÉMIOLOGIE FINE
        {"q": "Apragmatisme ?", "type": "ouverte", "answer": "Incapacité à entreprendre une action. On sait ce qu'il faut faire mais on ne peut pas 'passer à l'acte'.", "explanation": "Symptôme déficitaire (Schizo ou Dépression).", "tag": "Sémio"},
        {"q": "Aboulie ?", "type": "ouverte", "answer": "Diminution ou disparition de la volonté.", "explanation": "Souvent associé à l'apragmatisme.", "tag": "Sémio"},
        {"q": "Athymormie ?", "type": "ouverte", "answer": "Perte de l'élan vital et de l'affectivité.", "explanation": "Indifférence affective + Inaction.", "tag": "Sémio"},
        {"q": "Echolalie ?", "type": "ouverte", "answer": "Répétition automatique des paroles de l'interlocuteur.", "explanation": "Fréquent dans la catatonie ou l'autisme.", "tag": "Sémio"},
        {"q": "Barrage (Schizophrénie) ?", "type": "ouverte", "answer": "Arrêt brusque du discours sans raison, puis reprise sur un autre thème ou le même.", "explanation": "Signe la 'discontinuité' de la pensée.", "tag": "Sémio"},
        {"q": "Fading mental ?", "type": "ouverte", "answer": "Ralentissement progressif du discours jusqu'à l'extinction.", "explanation": "Équivalent mineur du barrage.", "tag": "Sémio"},
        {"q": "Néologisme ?", "type": "ouverte", "answer": "Invention de mots nouveaux incompréhensibles par l'entourage.", "explanation": "Typique du délire paranoïde ou schizophrénique.", "tag": "Sémio"},
        
        # PÉDOPSY & AUTRES
        {"q": "Dépression du nourrisson : signes ?", "type": "ouverte", "answer": "Regard vague/évitant, atonie, retrait, troubles du sommeil/alimentation, balancements.", "explanation": "Peut ressembler à l'autisme.", "tag": "Pédopsy"},
        {"q": "TDAH : Triade ?", "type": "ouverte", "answer": "Inattention, Impulsivité, Hyperactivité motrice.", "explanation": "Trouble neuro-développemental.", "tag": "Pédopsy"},
        {"q": "Trouble Oppositionnel avec Provocation (TOP) ?", "type": "ouverte", "answer": "Humeur colérique, comportement querelleur/provocateur, esprit vindicatif.", "explanation": "Souvent associé au TDAH.", "tag": "Pédopsy"},
        {"q": "Déficience Intellectuelle (Retard Mental) : critère ?", "options": ["QI < 70 + Déficit adaptatif", "QI < 100", "Échec scolaire"], "answer": "QI < 70 + Déficit adaptatif", "type": "qcm", "explanation": "Léger (50-70), Moyen (35-50), Grave (20-35), Profond (<20).", "tag": "Pédopsy"},
        {"q": "Psychose Puerpérale ?", "type": "ouverte", "answer": "Épisode psychotique aigu (délire, confusion) survenant brutalement après l'accouchement.", "explanation": "Urgence psychiatrique (risque infanticide/suicide).", "tag": "Périnatalité"},
        {"q": "Baby Blues vs Dépression Post-Partum ?", "type": "ouverte", "answer": "Baby Blues = Transitoire (J3-J10), hormonal, fréquent (80%). DPP = Durable, pathologique, nécessite soins.", "explanation": "Ne pas confondre.", "tag": "Périnatalité"},
        {"q": "Syndrome de Glissement (Gériatrie) ?", "type": "ouverte", "answer": "Détérioration rapide de l'état général après un événement déclenchant (chute, deuil), refus de soin/alimentation, désir de mort.", "explanation": "Pronostic vital engagé.", "tag": "Gériatrie"},
        {"q": "Maladie d'Alzheimer : types de troubles ?", "type": "ouverte", "answer": "Mnésiques (mémoire), Phasiques (langage), Praxiques (gestes), Gnosiques (reconnaissance).", "explanation": "Les 4 A (Amnésie, Aphasie, Apraxie, Agnosie).", "tag": "Neuropsy"},
        {"q": "État Limite (Borderline) : caractéristiques ?", "type": "ouverte", "answer": "Instabilité émotionnelle, relationnelle et de l'image de soi. Angoisse d'abandon. Impulsivité (scarifications).", "explanation": "Entre névrose et psychose.", "tag": "Patho"},
        {"q": "Déni de grossesse ?", "type": "ouverte", "answer": "La femme est enceinte mais n'en a pas conscience. Le corps ne montre pas de signes jusqu'à un stade avancé.", "explanation": "Mécanisme de défense inconscient.", "tag": "Périnatalité"},
        {"q": "Addiction : Circuit cérébral impliqué ?", "options": ["Circuit de la récompense", "Circuit de la peur"], "answer": "Circuit de la récompense", "type": "qcm", "explanation": "Noyau Accumbens / Dopamine.", "tag": "Addicto"},
    ],

    "MODULE 6: Psychomotricité Théorique": [
        # DÉFINITIONS & HISTOIRE
        {"q": "Définition Psychomotricité (Décret 88) ?", "type": "ouverte", "answer": "Agit sur les fonctions psychomotrices (tonus, schéma corporel...) perturbées par des troubles psychiques, psycho-affectifs ou neuro-développementaux.", "explanation": "Approche globale corps-psyché.", "tag": "Déf"},
        {"q": "Julian de Ajuriaguerra (1947) ?", "type": "ouverte", "answer": "Père de la psychomotricité. Crée la première chaire et le premier service à Sainte-Anne (Hôpital Henri Rousselle).", "explanation": "Lie neurologie et psychanalyse.", "tag": "Histoire"},
        {"q": "Giselle Soubiran ?", "type": "ouverte", "answer": "Crée l'ISRP. Développe la relaxation psychomotrice. Structure l'enseignement.", "explanation": "Pionnière de la pratique.", "tag": "Histoire"},
        {"q": "Date Création Diplôme d'État (DE) ?", "options": ["1947", "1974", "1988"], "answer": "1974", "type": "qcm", "explanation": "Reconnaissance officielle de la profession.", "tag": "Législation"},
        {"q": "Décret de Compétence (Actes) : Année ?", "options": ["1974", "1988", "2002"], "answer": "1988", "type": "qcm", "explanation": "Liste les actes autorisés (Bilan, Rééducation, Thérapie).", "tag": "Législation"},
        {"q": "Prescription médicale : Obligatoire ?", "options": ["Oui", "Non"], "answer": "Oui", "type": "qcm", "explanation": "'Sur prescription médicale'. Le bilan est le premier acte.", "tag": "Législation"},

        # CONCEPTS FONDAMENTAUX
        {"q": "Dialogue Tonique (Wallon) ?", "type": "ouverte", "answer": "Échange d'informations affectives et émotionnelles par les variations de tension musculaire entre la mère et l'enfant.", "explanation": "Fonction de communication du tonus. Prélude au langage.", "tag": "Tonus"},
        {"q": "Paratonie (Dupré) ?", "type": "ouverte", "answer": "Impossibilité de se relâcher volontairement. Freinage tonique lors de la mobilisation passive.", "explanation": "Signe clinique majeur (Débilité motrice).", "tag": "Tonus"},
        {"q": "Syncinésie ?", "type": "ouverte", "answer": "Mouvement involontaire et parasite d'un groupe musculaire lors de l'exécution d'un mouvement volontaire ailleurs.", "explanation": "D'imitation (l'autre main fait pareil) ou de diffusion.", "tag": "Tonus"},
        {"q": "Schéma Corporel (Head/Schilder) ?", "type": "ouverte", "answer": "Représentation tridimensionnelle de notre corps, physiologique, commune à tous, évolutive avec la croissance et l'apprentissage.", "explanation": "Permet de s'orienter et d'agir.", "tag": "Représentation"},
        {"q": "Image du Corps (Dolto) ?", "type": "ouverte", "answer": "Représentation inconsciente, propre à chaque sujet, liée à son histoire affective et relationnelle.", "explanation": "Mémoire inconsciente du vécu corporel.", "tag": "Représentation"},
        {"q": "Latéralité homogène ?", "type": "ouverte", "answer": "Préférence œil, main, pied du même côté (Tout Droitier ou Tout Gaucher).", "explanation": "Latéralité croisée = hétérogène (ex: Main droite, Oeil gauche).", "tag": "Latéralité"},
        {"q": "Espace Topologique (Piaget) ?", "type": "ouverte", "answer": "Premier espace de l'enfant. Relations de voisinage, séparation, ordre, entourage (Dedans/Dehors).", "explanation": "Avant l'espace projectif et euclidien.", "tag": "Espace"},
        {"q": "Corps Réel / Corps Imaginaire / Corps Symbolique (Lacan) ?", "type": "ouverte", "answer": "Réel = Organisme biologique. Imaginaire = Image du corps (Miroir). Symbolique = Corps nommé par le langage.", "explanation": "Nœud Borroméen.", "tag": "Concept"},
        {"q": "Empreinte (Lorenz) ?", "type": "ouverte", "answer": "Attachement instinctif et irréversible d'un animal au premier objet mobile qu'il voit à la naissance.", "explanation": "Expérience des oies.", "tag": "Ethologie"},
        {"q": "Néo-Darwinisme (Bullinger) ?", "type": "ouverte", "answer": "L'équipement sensorimoteur est archaïque mais doit s'adapter à un milieu technique moderne.", "explanation": "L'enfant est un 'organisme' qui devient 'corps' par l'interaction.", "tag": "Concept"},
        {"q": "Flux sensoriel (Bullinger) ?", "type": "ouverte", "answer": "Stimulation continue que l'enfant reçoit. Il doit apprendre à les filtrer pour ne pas être envahi.", "explanation": "Rôle du portage/holding comme pare-excitation.", "tag": "Concept"},
        {"q": "Fonction de Contenance ?", "type": "ouverte", "answer": "Capacité à rassembler les sensations éparses pour donner un sentiment d'unité (Peau psychique).", "explanation": "Bick, Anzieu.", "tag": "Concept"},
        {"q": "Schéma Corporel : Localisation cérébrale ?", "options": ["Lobe Pariétal", "Lobe Occipital", "Cervelet"], "answer": "Lobe Pariétal", "type": "qcm", "explanation": "Intégration somesthésique.", "tag": "Neuro"},
        {"q": "Somatognosie ?", "type": "ouverte", "answer": "Connaissance et reconnaissance des parties du corps et de leur relation entre elles.", "explanation": "Synonyme ou composante du schéma corporel.", "tag": "Déf"},
        
        # DÉVELOPPEMENT PSYCHOMOTEUR
        {"q": "Loi Céphalo-Caudale ?", "type": "ouverte", "answer": "Le contrôle moteur et la maturation se font de la tête vers les pieds.", "explanation": "Tenu de tête -> Assis -> Debout.", "tag": "Dvlpmt"},
        {"q": "Loi Proximo-Distale ?", "type": "ouverte", "answer": "Le contrôle se fait du centre du corps (axe) vers les extrémités.", "explanation": "Épaules -> Mains -> Doigts.", "tag": "Dvlpmt"},
        {"q": "Réflexe de Moro ?", "type": "ouverte", "answer": "Réflexe archaïque de défense (bruit/chute). Ouverture des bras (embrassement) puis fermeture + Cri.", "explanation": "Disparaît vers 3-4 mois.", "tag": "Dvlpmt"},
        {"q": "Grasping (Agrippement) ?", "type": "ouverte", "answer": "Fermeture réflexe de la main à la stimulation palmaire.", "explanation": "Devient préhension volontaire vers 4-5 mois.", "tag": "Dvlpmt"},
        {"q": "Stade du Corps Vécu (0-3 ans) ?", "type": "ouverte", "answer": "L'enfant vit son corps à travers l'action, l'exploration et le ressenti émotionnel.", "explanation": "Avant le corps perçu et le corps représenté.", "tag": "Dvlpmt"},
        {"q": "Stade du Corps Subi (0-3 mois) ?", "type": "ouverte", "answer": "Dépendance totale à l'adulte. Motricité réflexe. Besoins physiologiques primaires.", "explanation": "Ajuriaguerra.", "tag": "Dvlpmt"},
        {"q": "Stade du Corps Perçu (3-7 ans) ?", "type": "ouverte", "answer": "Affinement de la perception (visuelle, auditive). Latéralisation. Orientation spatio-temporelle.", "explanation": "Pré-opératoire.", "tag": "Dvlpmt"},
        {"q": "Stade du Corps Représenté (7-12 ans) ?", "type": "ouverte", "answer": "Image mentale du corps en mouvement. Peut anticiper l'action sans la faire.", "explanation": "Opératoire concret.", "tag": "Dvlpmt"},
        {"q": "Réflexe Tonique Asymétrique du Cou (RTAC) ?", "type": "ouverte", "answer": "Rotation tête d'un côté -> Extension bras/jambe côté visage, Flexion côté opposé.", "explanation": "Position de l'escrimeur.", "tag": "Dvlpmt"},
        {"q": "Marche automatique ?", "type": "ouverte", "answer": "Réflexe archaïque. Pas alternés si on tient le bébé debout penché en avant.", "explanation": "Disparaît vers 2-3 mois. Réapparaît en marche volontaire vers 1 an.", "tag": "Dvlpmt"},
        {"q": "Pince pouce-index (Fine) : âge ?", "options": ["4 mois", "9-10 mois", "2 ans"], "answer": "9-10 mois", "type": "qcm", "explanation": "Pince supérieure. Permet de saisir des miettes.", "tag": "Dvlpmt"},
        {"q": "Position assise sans appui : âge ?", "options": ["4 mois", "6-8 mois", "12 mois"], "answer": "6-8 mois", "type": "qcm", "explanation": "Libère les mains pour l'exploration.", "tag": "Dvlpmt"},
        {"q": "Marche acquise (moyenne) ?", "options": ["9 mois", "12-15 mois", "24 mois"], "answer": "12-15 mois", "type": "qcm", "explanation": "Considéré retard si > 18 mois.", "tag": "Dvlpmt"},
        
        # PRATIQUE ET MÉDIATION
        {"q": "Médiation Thérapeutique : définition ?", "type": "ouverte", "answer": "Utilisation d'un objet, d'une matière ou d'une activité pour faire tiers dans la relation et favoriser l'expression.", "explanation": "L'objet est 'malléable' (Roussillon).", "tag": "Pratique"},
        {"q": "Cadre thérapeutique ?", "type": "ouverte", "answer": "Ensemble des règles fixes (Temps, Lieu, Tarifs, Règles de vie) qui sécurisent la thérapie.", "explanation": "Permet au processus de se déployer.", "tag": "Pratique"},
        {"q": "Indications de la psychomotricité ?", "type": "ouverte", "answer": "TDC (Dyspraxie), TDAH, TSA, Troubles du tonus, Dysgraphie, Inhibition, Instabilité...", "explanation": "Sur prescription.", "tag": "Pratique"},
        {"q": "Bilan Psychomoteur : Étapes ?", "type": "ouverte", "answer": "Entretien (Anamnèse), Passation des tests/épreuves, Cotation/Analyse, Rédaction (Compte-rendu), Restitution.", "explanation": "Aboutit au projet thérapeutique.", "tag": "Pratique"},

        # TROUBLES PSYCHOMOTEURS
        {"q": "TDC (Trouble du Développement de la Coordination) ?", "type": "ouverte", "answer": "Nouveau nom de la Dyspraxie. Maladresse, difficulté planification gestuelle, lenteur.", "explanation": "DSM-5.", "tag": "Patho"},
        {"q": "Dysgraphie ?", "type": "ouverte", "answer": "Trouble de l'écriture (qualité, vitesse, lisibilité) sans déficit intellectuel ni neuro.", "explanation": "Motif de consultation fréquent.", "tag": "Patho"},
        {"q": "Instabilité Psychomotrice ?", "type": "ouverte", "answer": "Besoin incessant de bouger (Hyperkinésie) + Déficit attentionnel.", "explanation": "Symptôme, pas forcément TDAH.", "tag": "Patho"},
        {"q": "Inhibition Psychomotrice ?", "type": "ouverte", "answer": "Rareté du mouvement, lenteur, passivité, tension, fatigue.", "explanation": "L'enfant 'se fait oublier'.", "tag": "Patho"},
        {"q": "Trouble de la Latéralité ?", "type": "ouverte", "answer": "Latéralité mal affirmée, contrariée ou discordante (œil/main).", "explanation": "Peut gêner l'apprentissage (lecture/écriture).", "tag": "Patho"},
        {"q": "Trouble Spatio-Temporel ?", "type": "ouverte", "answer": "Difficulté à s'orienter (droite/gauche), à organiser l'espace (feuille) ou le temps (rythme, durée).", "explanation": "Dyschronie.", "tag": "Patho"},
        
        # PRATIQUE & EXAMEN
        {"q": "Bilan : Examen du Tonus ?", "type": "ouverte", "answer": "Tonus de fond (passivité, ballant), Tonus postural (équilibre), Tonus d'action.", "explanation": "Base de l'examen.", "tag": "Bilan"},
        {"q": "Test M-ABC ?", "type": "ouverte", "answer": "Batterie d'évaluation du mouvement chez l'enfant (TDC).", "explanation": "Dextérité, Viser/Attraper, Équilibre.", "tag": "Test"},
        {"q": "BHK ?", "type": "ouverte", "answer": "Échelle d'évaluation rapide de l'écriture chez l'enfant.", "explanation": "Détecte la dysgraphie.", "tag": "Test"},
        {"q": "NP-MOT ?", "type": "ouverte", "answer": "Batterie d'évaluation des fonctions psychomotrices (Vaivre-Douret).", "explanation": "Maturation neuro-psychomotrice.", "tag": "Test"},
        {"q": "Relaxation : But ?", "type": "ouverte", "answer": "Abaissement du tonus, conscience corporelle, apaisement émotionnel.", "explanation": "Méthodes : Soubiran, Schultz, Jacobson, Wintrebert.", "tag": "Thérapie"},
        {"q": "Graphomotricité ?", "type": "ouverte", "answer": "Rééducation du geste d'écriture (tenue crayon, posture, fluidité).", "explanation": "Ne pas confondre avec calligraphie.", "tag": "Thérapie"},
        {"q": "Eau (Balnéothérapie) : Intérêt ?", "type": "ouverte", "answer": "Enveloppe, portage, sensations, régression, schéma corporel.", "explanation": "Médiation corporelle privilégiée.", "tag": "Médiation"},
        {"q": "Équithérapie : Intérêt ?", "type": "ouverte", "answer": "Dialogue tonique avec l'animal, portage, axe corporel, communication non-verbale.", "explanation": "Le cheval comme miroir.", "tag": "Médiation"},
        {"q": "Rythme et Danse : Intérêt ?", "type": "ouverte", "answer": "Coordination, expressivité, occupation de l'espace, socialisation.", "explanation": "Structuration temporelle.", "tag": "Médiation"},
        {"q": "Projet Thérapeutique Individualisé (PTI) ?", "type": "ouverte", "answer": "Objectifs de soin définis après le bilan, adaptés au patient, réévalués régulièrement.", "explanation": "Contrat de soin.", "tag": "Pratique"},
    ]
}

# [ ... ICI, TU DOIS AVOIR TA GROSSE BASE DE DONNÉES db_questions INTACTE ... ]

# =========================================================
# ⚙️ MOTEUR INTELLIGENT (ALÉATOIRE & SUIVI)
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
# NOUVEAU : On stocke les questions tirées au sort pour qu'elles ne changent pas pendant le quiz
if 'quiz_batch' not in st.session_state:
    st.session_state.quiz_batch = []

# --- CONSTANTE : NOMBRE DE QUESTIONS PAR TIRAGE ---
QUESTIONS_PAR_QUIZ = 20

# --- NAVIGATION ---
menu = st.sidebar.radio("📌 Navigation", ["Tableau de Bord", "Passer un Quiz"])

# --- FONCTIONS UTILES ---
def get_global_stats():
    if not st.session_state.history:
        return None
    df = pd.DataFrame(st.session_state.history)
    avg_per_module = df.groupby("module")["score_percent"].mean().reset_index()
    return avg_per_module

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
    """Tire au sort 15 questions nouvelles depuis la base de données"""
    all_questions = db_questions[module]
    # On prend 15 questions au hasard (ou moins si le module en a moins de 15)
    nb_to_take = min(len(all_questions), QUESTIONS_PAR_QUIZ)
    st.session_state.quiz_batch = random.sample(all_questions, nb_to_take)
    
    # On réinitialise les scores pour ce nouveau round
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
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tests réalisés", len(st.session_state.history))
        with col2:
            st.metric("Moyenne Générale", f"{stats['score_percent'].mean():.1f}%")
        
        st.write("---")
        
        col_graph1, col_graph2 = st.columns(2)
        with col_graph1:
            st.subheader("📈 Moyenne par matière")
            fig_bar = px.bar(stats, x='module', y='score_percent', range_y=[0, 100], 
                         labels={'score_percent': 'Note Moyenne (%)'},
                         color='score_percent', color_continuous_scale='Bluered')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graph2:
            st.subheader("🚀 Évolution de tes notes")
            df_hist = pd.DataFrame(st.session_state.history)
            df_hist['Essai'] = range(1, len(df_hist) + 1)
            fig_line = px.line(df_hist, x='Essai', y='score_percent', color='module', markers=True,
                               range_y=[0, 105],
                               labels={'Essai': 'Ordre des Quiz', 'score_percent': 'Note (%)'},
                               title="Progression au fil des essais")
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
    
    module_choisi = st.sidebar.selectbox("Choisir le module :", list(db_questions.keys()))
    
    # BOUTON POUR LANCER UN NOUVEAU QUIZ
    if st.sidebar.button("NOUVEAU QUIZ (20 Q)", type="primary"):
        generer_nouveau_quiz(module_choisi)
        st.rerun()

    # Si c'est la première fois qu'on arrive ou si on change de module via le menu sans cliquer sur le bouton
    if 'active_module' not in st.session_state or st.session_state.active_module != module_choisi:
        generer_nouveau_quiz(module_choisi)
    
    # Affichage du Quiz
    st.title(f"📝 {module_choisi}")
    st.caption(f"Série aléatoire de {len(st.session_state.quiz_batch)} questions tirées de la base de données.")
    
    # On utilise le batch stocké en mémoire (pour qu'il ne change pas à chaque clic)
    questions = st.session_state.quiz_batch
    
    for i, q in enumerate(questions):
        st.markdown(f"<div class='question-card'><h5>Question {i+1} <span style='background:#eee;padding:2px 5px;border-radius:5px;font-size:0.7em'>{q['tag']}</span></h5>", unsafe_allow_html=True)
        st.write(f"**{q['q']}**")
        # On utilise le q['q'] comme partie de la clé pour qu'elle soit unique même si l'ordre change
        q_hash = hash(q['q']) 
        q_id = f"{module_choisi}_{q_hash}"
        
        if q["type"] == "qcm":
            user_choice = st.radio("Réponse :", q["options"], key=f"radio_{q_id}", index=None)
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
            "date": datetime.now()
        })
        st.balloons()
        
        st.markdown(f"""
        <div style="background-color:#d4edda;padding:20px;border-radius:10px;text-align:center;">
            <h2>Score : {score}/{total_q}</h2>
            <h3>Note : {percent:.0f}/20</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.current_mistakes:
            st.write("### 🔍 Sur cette série, revois ces points :")
            from collections import Counter
            for tag, count in Counter(st.session_state.current_mistakes).items():
                st.markdown(f"- **{tag}** ({count} fautes)")
        
        st.info("Résultat enregistré ! Clique sur 'Générer un nouveau quiz' à gauche pour relancer une série différente.")