import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Psychomot' Master - Suivi & Performance", page_icon="🧠", layout="wide")

# --- CSS PRO ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4e73df; text-align: center; }
    .feedback-box { padding: 15px; border-radius: 10px; margin-top: 10px; background-color: #e8f4f8; border-left: 5px solid #2e86de; color: #1e3799; }
    .weakness-tag { background-color: #ffcccc; color: #cc0000; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; margin: 2px; display: inline-block; }
    h1, h2, h3 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DONNÉES MASSIVE (INTEGRALE) ---
db_questions = {
    "MODULE 1: Santé Pub, Pharma, Hygiène": [
        # PHARMACOLOGIE
        {"q": "Dans le système ADME, à quoi correspond la lettre 'D' ?", "options": ["Digestion", "Dilution", "Distribution", "Dynamisation"], "answer": "Distribution", "type": "qcm", "explanation": "ADME = Absorption, Distribution, Métabolisme, Élimination.", "tag": "Pharmacologie"},
        {"q": "Quelle est la définition de la biodisponibilité ?", "options": ["Vitesse d'élimination", "Fraction de la dose atteignant la circulation générale sous forme inchangée", "Toxicité", "Volume de distribution"], "answer": "Fraction de la dose atteignant la circulation générale sous forme inchangée", "type": "qcm", "explanation": "100% en IV, moins en per os (premier passage hépatique).", "tag": "Pharmacologie"},
        {"q": "Qu'est-ce que l'effet de premier passage hépatique ?", "type": "ouverte", "answer": "Perte de principe actif lors du passage par le foie avant d'atteindre la circulation générale.", "explanation": "Le foie dégrade une partie du médicament absorbé.", "tag": "Pharmacologie"},
        {"q": "Différence Princeps / Générique ?", "type": "ouverte", "answer": "Princeps = Original breveté. Générique = Copie (même PA, même dosage) après chute du brevet.", "explanation": "Bioéquivalence obligatoire.", "tag": "Pharmacologie"},
        {"q": "Qu'est-ce qu'un excipient ?", "options": ["Principe actif", "Substance inactive (forme/goût)", "Poison"], "answer": "Substance inactive (forme/goût)", "type": "qcm", "explanation": "Sert à la fabrication et conservation (ex: amidon, sucre).", "tag": "Pharmacologie"},
        {"q": "Demi-vie d'élimination (T1/2) ?", "type": "ouverte", "answer": "Temps nécessaire pour que la concentration plasmatique diminue de 50%.", "explanation": "Il faut 5 à 7 demi-vies pour éliminer le produit.", "tag": "Pharmacologie"},
        {"q": "Clairance rénale ?", "options": ["Volume de plasma épuré par unité de temps", "Volume d'urine"], "answer": "Volume de plasma épuré par unité de temps", "type": "qcm", "explanation": "Mesure la fonction rénale.", "tag": "Pharmacologie"},
        
        # SANTÉ PUBLIQUE & HISTOIRE
        {"q": "Loi Kouchner (2002) : Apport principal ?", "options": ["Sécu", "Droits des malades & Qualité du système", "Avortement"], "answer": "Droits des malades & Qualité du système", "type": "qcm", "explanation": "Fin du paternalisme, accès au dossier médical.", "tag": "Législation"},
        {"q": "Loi de 1838 ?", "options": ["Secteur", "Asiles départementaux"], "answer": "Asiles départementaux", "type": "qcm", "explanation": "Loi Esquirol : obligation d'un asile par département.", "tag": "Histoire"},
        {"q": "Lois Jules Ferry (1881-1882) ?", "options": ["École laïque, gratuite, obligatoire", "Vote des femmes"], "answer": "École laïque, gratuite, obligatoire", "type": "qcm", "explanation": "Fondement école républicaine.", "tag": "Histoire"},
        {"q": "Définition de la santé (OMS 1946) ?", "type": "ouverte", "answer": "État de complet bien-être physique, mental et social (pas seulement absence de maladie).", "explanation": "Approche bio-psycho-sociale.", "tag": "Concept"},
        {"q": "Rôle de la PMI ?", "options": ["Protection Maternelle et Infantile", "Police Médicale"], "answer": "Protection Maternelle et Infantile", "type": "qcm", "explanation": "Suivi 0-6 ans.", "tag": "Santé Pub"},
        
        # HYGIÈNE
        {"q": "Durée friction SHA ?", "options": ["10 sec", "30 sec", "2 min"], "answer": "30 sec", "type": "qcm", "explanation": "Jusqu'à séchage complet.", "tag": "Hygiène"},
        {"q": "Signification DASRI ?", "options": ["Déchets d'Activités de Soins à Risques Infectieux", "Déchets Assimilés", "Déchets Aseptisés"], "answer": "Déchets d'Activités de Soins à Risques Infectieux", "type": "qcm", "explanation": "Bacs jaunes (piquants/coupants/sang).", "tag": "Hygiène"},
        {"q": "Définition Infection Nosocomiale (IAS) ?", "type": "ouverte", "answer": "Infection contractée lors d'un soin, absente à l'admission. Délai > 48h.", "explanation": "Si < 48h = communautaire.", "tag": "Hygiène"},
        {"q": "Asepsie vs Antisepsie ?", "type": "ouverte", "answer": "Asepsie = Préventif (empêcher microbes d'entrer). Antisepsie = Curatif (tuer microbes sur tissus vivants).", "explanation": "On aseptise un local, on fait une antisepsie d'une plaie.", "tag": "Hygiène"},
        {"q": "Les 5 moments hygiène des mains ?", "type": "ouverte", "answer": "Avant patient, Avant geste aseptique, Après liquide bio, Après patient, Après environnement.", "explanation": "OMS.", "tag": "Hygiène"},
    ],

    "MODULE 2: Anatomie & Neuroanatomie": [
        # OSTEOLOGIE
        {"q": "Courbures du rachis (Sagittal) ?", "type": "ouverte", "answer": "Lordose cervicale, Cyphose thoracique, Lordose lombaire, Cyphose sacrée.", "explanation": "Lordose = creux, Cyphose = bosse.", "tag": "Rachis"},
        {"q": "Nombre de vertèbres cervicales ?", "options": ["5", "7", "12"], "answer": "7", "type": "qcm", "explanation": "C1 à C7.", "tag": "Rachis"},
        {"q": "Noms de C1 et C2 ?", "options": ["Atlas et Axis", "Axis et Atlas"], "answer": "Atlas et Axis", "type": "qcm", "explanation": "Atlas porte la tête.", "tag": "Rachis"},
        {"q": "Os du carpe (Rangée 1) ?", "type": "ouverte", "answer": "Scaphoïde, Lunatum, Triquetrum, Pisiforme.", "explanation": "Rangée proximale, de dehors en dedans.", "tag": "Membre Sup"},
        {"q": "Muscles coiffe des rotateurs ?", "type": "ouverte", "answer": "Supra-épineux, Infra-épineux, Petit rond, Subscapulaire.", "explanation": "Stabilisateurs de l'épaule.", "tag": "Membre Sup"},
        {"q": "Nerf 'petit juif' au coude ?", "options": ["Radial", "Ulnaire", "Médian"], "answer": "Ulnaire", "type": "qcm", "explanation": "Passe dans la gouttière épitrochléenne.", "tag": "Membre Sup"},
        {"q": "Os coxal composé de ?", "options": ["Ilion, Ischion, Pubis", "Sacrum, Coccyx", "Fémur"], "answer": "Ilion, Ischion, Pubis", "type": "qcm", "explanation": "Fusion au niveau de l'acétabulum.", "tag": "Membre Inf"},
        {"q": "Garden III (Col fémur) ?", "options": ["Non déplacée", "Déplacée en varus (charnière conservée)", "Tête libre"], "answer": "Déplacée en varus (charnière conservée)", "type": "qcm", "explanation": "Risque de nécrose tête fémorale.", "tag": "Trauma"},
        {"q": "Triade terrible du coude ?", "type": "ouverte", "answer": "Luxation coude + Fracture tête radiale + Fracture processus coronoïde.", "explanation": "Très instable.", "tag": "Trauma"},
        
        # NEURO
        {"q": "Nombre os du crâne ?", "options": ["8", "14", "22"], "answer": "8", "type": "qcm", "explanation": "Frontal, Occipital, Sphénoïde, Ethmoïde, 2 Pariétaux, 2 Temporaux.", "tag": "Crâne"},
        {"q": "Lobe de la vision ?", "options": ["Frontal", "Pariétal", "Occipital"], "answer": "Occipital", "type": "qcm", "explanation": "Cortex visuel primaire V1.", "tag": "Neuro"},
        {"q": "Localisation LCS ?", "options": ["Sous-dural", "Sous-arachnoïdien"], "answer": "Sous-arachnoïdien", "type": "qcm", "explanation": "Entre arachnoïde et pie-mère.", "tag": "Neuro"},
        {"q": "Composition SNC ?", "options": ["Encéphale + Moelle", "Cerveau + Nerfs"], "answer": "Encéphale + Moelle", "type": "qcm", "explanation": "Système Nerveux Central.", "tag": "Neuro"},
        {"q": "Rôle Cervelet ?", "type": "ouverte", "answer": "Équilibre, Coordination, Tonus.", "explanation": "Chef d'orchestre motricité.", "tag": "Neuro"},
    ],

    "MODULE 3: Physiologie": [
        # CELLULE & NERF
        {"q": "Homéostasie ?", "type": "ouverte", "answer": "Maintien de la stabilité du milieu intérieur malgré les variations externes.", "explanation": "Température, pH, glycémie...", "tag": "Général"},
        {"q": "Ion dépolarisation cellulaire ?", "options": ["Na+", "K+", "Cl-"], "answer": "Na+", "type": "qcm", "explanation": "Entrée massive de Sodium.", "tag": "Neurophy"},
        {"q": "Synapse ?", "type": "ouverte", "answer": "Zone de contact fonctionnelle entre deux neurones permettant transmission influx.", "explanation": "Chimique ou électrique.", "tag": "Neurophy"},
        
        # MUSCLE & CARDIO
        {"q": "Protéines contractiles muscle ?", "options": ["Actine/Myosine", "Collagène/Élastine"], "answer": "Actine/Myosine", "type": "qcm", "explanation": "Glissement des filaments.", "tag": "Muscle"},
        {"q": "Systole / Diastole ?", "type": "ouverte", "answer": "Systole = Contraction (éjection). Diastole = Relâchement (remplissage).", "explanation": "Cycle cardiaque.", "tag": "Cardio"},
        {"q": "Pacemaker naturel ?", "options": ["Nœud Sinusal", "Nœud AV", "His"], "answer": "Nœud Sinusal", "type": "qcm", "explanation": "Oreillette Droite.", "tag": "Cardio"},
        {"q": "Veine Pulmonaire : Sang riche en ?", "options": ["Oxygène", "CO2"], "answer": "Oxygène", "type": "qcm", "explanation": "Exception : veine ramène sang oxygéné au cœur gauche.", "tag": "Cardio"},
        
        # VISCERAL
        {"q": "Hématose ?", "type": "ouverte", "answer": "Échanges gazeux O2/CO2 alvéolo-capillaires.", "explanation": "Poumon.", "tag": "Respi"},
        {"q": "Muscle inspirateur principal ?", "answer": "Diaphragme", "type": "qcm", "options": ["Intercostaux", "Diaphragme", "Abdos"], "explanation": "Nerf phrénique.", "tag": "Respi"},
        {"q": "Unité fonctionnelle rein ?", "options": ["Néphron", "Glomérule", "Hile"], "answer": "Néphron", "type": "qcm", "explanation": "Filtration du sang.", "tag": "Rénal"},
        {"q": "Hormone rénale pour globules rouges ?", "options": ["EPO", "Rénine"], "answer": "EPO", "type": "qcm", "explanation": "Érythropoïétine.", "tag": "Rénal"},
        {"q": "Rôle de la bile ?", "options": ["Émulsionner graisses", "Digérer sucre"], "answer": "Émulsionner graisses", "type": "qcm", "explanation": "Produite par foie.", "tag": "Digestif"},
    ],

    "MODULE 4: Psychologie": [
        # FREUD
        {"q": "Stade Oral (Freud) ?", "type": "ouverte", "answer": "0-1 an. Zone buccale. Incorporation. Relation anaclitique.", "explanation": "Plaisir de succion.", "tag": "Freud"},
        {"q": "Stade Anal ?", "type": "ouverte", "answer": "1-3 ans. Sphincters. Maîtrise/Emprise. Don/Retenue.", "explanation": "Apprentissage propreté.", "tag": "Freud"},
        {"q": "Complexe d'Oedipe (Âge) ?", "options": ["Oral", "Anal", "Phallique (3-6 ans)"], "answer": "Phallique (3-6 ans)", "type": "qcm", "explanation": "Désir parent opposé, rivalité même sexe.", "tag": "Freud"},
        {"q": "Instances 2ème topique ?", "options": ["Ça/Moi/Surmoi", "Ics/Pcs/Cs"], "answer": "Ça/Moi/Surmoi", "type": "qcm", "explanation": "Ça=Pulsion, Moi=Réalité, Surmoi=Interdit.", "tag": "Freud"},
        
        # AUTEURS
        {"q": "Stade du miroir (Auteur) ?", "type": "ouverte", "answer": "Wallon (et Lacan).", "explanation": "Unification du corps, construction du Je.", "tag": "Wallon"},
        {"q": "Objet Transitionnel ?", "type": "ouverte", "answer": "Première possession non-moi (doudou). Aire transitionnelle.", "explanation": "Défense contre angoisse séparation.", "tag": "Winnicott"},
        {"q": "Préoccupation Maternelle Primaire ?", "type": "ouverte", "answer": "État sensibilité mère fin grossesse pour s'adapter au bébé.", "explanation": "Maladie normale (Winnicott).", "tag": "Winnicott"},
        {"q": "Positions Klein ?", "options": ["Schizo-paranoïde / Dépressive", "Orale / Anale"], "answer": "Schizo-paranoïde / Dépressive", "type": "qcm", "explanation": "Clivage puis ambivalence.", "tag": "Klein"},
        {"q": "Fonction Alpha (Bion) ?", "type": "ouverte", "answer": "Transformation éléments Bêta (bruts) en Alpha (pensables) par la mère.", "explanation": "Capacité de rêverie.", "tag": "Bion"},
        {"q": "Attachement (Bowlby) ?", "type": "ouverte", "answer": "Besoin primaire de lien affectif pour la sécurité et la survie.", "explanation": "Base de sécurité.", "tag": "Bowlby"},
        {"q": "Stades Piaget ?", "type": "ouverte", "answer": "Sensorimoteur -> Préopératoire -> Opératoire Concret -> Formel.", "explanation": "Intelligence.", "tag": "Piaget"},
    ],

    "MODULE 5: Psychiatrie": [
        # HISTOIRE & ORGA
        {"q": "Pinel (1793) ?", "options": ["Libération aliénés", "Hypnose"], "answer": "Libération aliénés", "type": "qcm", "explanation": "Naissance psychiatrie moderne.", "tag": "Histoire"},
        {"q": "Loi 1838 ?", "answer": "Asiles départementaux", "type": "qcm", "options": ["Secteur", "Asiles"], "explanation": "Enfermement.", "tag": "Histoire"},
        {"q": "Sectorisation ?", "type": "ouverte", "answer": "Organisation géo : même équipe soigne population d'une zone (Hôpital + CMP).", "explanation": "Continuité des soins.", "tag": "Orga"},
        
        # PATHO
        {"q": "Névrose vs Psychose ?", "type": "ouverte", "answer": "Névrose = Réalité conservée, Conflit. Psychose = Perte réalité, Délire, Anosognosie.", "explanation": "Refoulement vs Forclusion.", "tag": "Nosographie"},
        {"q": "Délire ?", "type": "ouverte", "answer": "Conviction inébranlable en une idée fausse, hors réalité.", "explanation": "Mécanismes variés.", "tag": "Sémio"},
        {"q": "Triade Autisme ?", "type": "ouverte", "answer": "Déficit Com/Social + Comportements restreints/répétitifs.", "explanation": "Dyade dans le DSM-5.", "tag": "TSA"},
        {"q": "Anhédonie ?", "options": ["Perte plaisir", "Perte mémoire"], "answer": "Perte plaisir", "type": "qcm", "explanation": "Signe dépression.", "tag": "Sémio"},
        {"q": "Symptômes négatifs Schizo ?", "type": "ouverte", "answer": "Apragmatisme, Aboulie, Retrait social, Émoussement.", "explanation": "Opposés aux positifs (délires).", "tag": "Schizo"},
        {"q": "Dysharmonie évolutive ?", "type": "ouverte", "answer": "Pathologie limite enfant, développement hétérogène.", "explanation": "Concept CFTMEA.", "tag": "Pédopsy"},
    ],

    "MODULE 6: Psychomotricité Théorique": [
        # CONCEPTS
        {"q": "Définition Psychomot ?", "type": "ouverte", "answer": "Lien corps-psyché. Agir sur le corps pour agir sur le psychisme.", "explanation": "Approche globale.", "tag": "Déf"},
        {"q": "Dialogue Tonique ?", "type": "ouverte", "answer": "Communication émotionnelle mère-enfant via variations tonus.", "explanation": "Wallon/Ajuriaguerra.", "tag": "Concept"},
        {"q": "Schéma vs Image Corps ?", "type": "ouverte", "answer": "Schéma = Physio/Universel. Image = Inconscient/Affectif.", "explanation": "Dolto.", "tag": "Concept"},
        {"q": "Loi Proximo-distale ?", "options": ["Tête aux pieds", "Centre aux extrémités"], "answer": "Centre aux extrémités", "type": "qcm", "explanation": "Contrôle épaule avant main.", "tag": "Dvlpmt"},
        {"q": "Loi Céphalo-caudale ?", "options": ["Tête aux pieds", "Centre aux extrémités"], "answer": "Tête aux pieds", "type": "qcm", "explanation": "Tenu tête avant debout.", "tag": "Dvlpmt"},
        {"q": "Sensori-motricité ?", "type": "ouverte", "answer": "Lien indissociable sensation/mouvement. Boucle.", "explanation": "Bullinger.", "tag": "Concept"},
        
        # CADRE & PRATIQUE
        {"q": "Créateur Chaire Psychomot 1947 ?", "answer": "Ajuriaguerra", "type": "qcm", "options": ["Freud", "Ajuriaguerra"], "explanation": "Avec Soubiran.", "tag": "Histoire"},
        {"q": "Date DE ?", "options": ["1974", "1988"], "answer": "1974", "type": "qcm", "explanation": "Décret compétences 1988.", "tag": "Cadre"},
        {"q": "Paratonie ?", "options": ["Freinage tonique involontaire", "Paralysie"], "answer": "Freinage tonique involontaire", "type": "qcm", "explanation": "Impossibilité de relâchement passif.", "tag": "Sémio"},
        {"q": "Médiation thérapeutique ?", "type": "ouverte", "answer": "Utilisation d'un tiers (objet/activité) pour faciliter relation et expression.", "explanation": "Contourner les défenses.", "tag": "Pratique"},
    ]
}

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

# =========================================================
# PAGE 1 : TABLEAU DE BORD
# =========================================================
if menu == "Tableau de Bord":
    st.title("📊 Tableau de Bord de Révision")
    stats = get_global_stats()
    
    if stats is None:
        st.info("👋 Aucune donnée. Va dans 'Passer un Quiz' pour commencer.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Quiz terminés", len(st.session_state.history))
        with col2:
            st.metric("Moyenne Générale", f"{stats['score_percent'].mean():.1f}%")
        
        st.write("---")
        st.subheader("📈 Progression par Module")
        fig = px.bar(stats, x='module', y='score_percent', range_y=[0, 100], 
                     color='score_percent', color_continuous_scale='Bluered')
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("⚠️ Top 5 des thèmes à revoir")
        weaknesses = get_weaknesses()
        if weaknesses:
            cols = st.columns(5)
            for i, (tag, count) in enumerate(weaknesses):
                with cols[i % 5]:
                    st.markdown(f"<div class='metric-card' style='border-left: 5px solid #ff4d4d;'><b>{tag}</b><br>{count} erreurs</div>", unsafe_allow_html=True)
        else:
            st.success("Aucune lacune récurrente !")

# =========================================================
# PAGE 2 : QUIZ
# =========================================================
elif menu == "Passer un Quiz":
    module_choisi = st.sidebar.selectbox("Choisir le module :", list(db_questions.keys()))
    
    # Reset si changement de module
    if 'active_module' not in st.session_state or st.session_state.active_module != module_choisi:
        st.session_state.active_module = module_choisi
        st.session_state.current_score = 0
        st.session_state.current_mistakes = []
        st.session_state.validated_questions = set()
        st.session_state.show_explanation = {}
    
    st.title(f"📝 {module_choisi}")
    questions = db_questions[module_choisi]
    
    for i, q in enumerate(questions):
        st.markdown(f"<div class='question-card'><h5>Question {i+1} <span style='background:#eee;padding:2px 5px;border-radius:5px;font-size:0.7em'>{q['tag']}</span></h5>", unsafe_allow_html=True)
        st.write(f"**{q['q']}**")
        q_id = f"{module_choisi}_{i}"
        
        if q["type"] == "qcm":
            user_choice = st.radio("Réponse :", q["options"], key=f"radio_{q_id}", index=None)
            if st.button(f"Valider Q{i+1}", key=f"btn_{q_id}"):
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
            if st.button(f"Vérifier Q{i+1}", key=f"btn_{q_id}"):
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

    if st.button("🏁 TERMINER CE MODULE", type="primary"):
        total_q = len(questions)
        score = st.session_state.current_score
        percent = (score / total_q) * 100
        st.session_state.history.append({
            "module": module_choisi, "score": score, "total": total_q,
            "score_percent": percent, "mistakes": st.session_state.current_mistakes
        })
        st.balloons()
        st.success(f"Score : {score}/{total_q} ({percent:.0f}%)")
        if st.session_state.current_mistakes:
            st.write("### 🔍 À revoir :")
            from collections import Counter
            for tag, count in Counter(st.session_state.current_mistakes).items():
                st.markdown(f"- **{tag}** ({count} fautes)")
        st.info("Résultats enregistrés dans le Tableau de Bord.")