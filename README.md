SmartFarm — Mini service IoT + ETL qualité

--Description:

Ce projet simule un service d’ingestion IoT pour une exploitation agricole "SmartFarm".
Il inclut :
Ingestion réseau TCP : réception de mesures capteurs (température, humidité, irrigation, indicateurs air).
Validation défensive : vérification des types, plages de valeurs, cohérence des données.
Observabilité : logs détaillés et corrélés par request_id.
Pipeline ETL batch : nettoyage, normalisation, traitement des outliers et création de features.
Le projet permet de passer d’un flux de mesures brutes à un data mart exploitable.

-- Structure du projet:

smartfarm/
├─ src/
│  ├─ client.py           # Client TCP pour envoi de mesures
│  ├─ server.py           # Serveur TCP d’ingestion
│  ├─ models.py           # Modèles / contrats de messages
│  ├─ validators.py       # Validation métier
│  ├─ protocol.py         # Encodage / framing NDJSON
│  └─ etl_pipeline.py     # Pipeline ETL batch
├─ data/
│  └─ rawdata.json        # Données brutes capteurs
├─ outputs/               # Dossier de sortie ETL (CSV)
├─ logs/                  # Logs serveur et client
└─ main_demo.py           # Démo / vérifications rapides


-- Exécution:

1️- Lancer le serveur
python -m src.server --host 127.0.0.1 --port 9000
Écoute sur le port 9000.
Logs dans logs/server.log et console.

2️- Lancer le client
python -m src.client --host 127.0.0.1 --port 9000 --data data/rawdata.json --interval 5
Envoie les mesures toutes les 5 secondes.
Affiche les résultats d’ingestion et erreurs de validation.
Logs dans logs/client.log.

3️- Lancer le pipeline ETL
python -m src.etl_pipeline --input data/rawdata.json --output outputs
Nettoie les données :
Transformation ON/OFF pour irrigation (OUI → ON, NON → OFF).
Clipping des valeurs de température et humidité.
Détection et suppression d’outliers simples (z-score).
Création de features :
temp_humidity_index = temperature + 0.1*humidity
air_quality_index = pm25 + pm10 + ozone + no2
Exporte :
outputs/cleaned.csv
outputs/cleaned_with_features.csv

4️- Tester avec la démo rapide
python main_demo.py
Vérifie : encode/decode protocole, lectures valides/invalide, incohérence pompe/irrigation, structure protocolaire.
Sortie attendue :

=== Vérifications rapides SmartFarm ===
✅ Check 1 : encode/decode protocole OK
✅ Check 2 : lecture valide OK
✅ Check 3 : lecture invalide détectée OK
✅ Check 4 : sensor_id vide détecté OK
✅ Check 5 : incohérence pompe/irrigation détectée OK
✅ Check 6 : structure protocolaire OK
=== Toutes les vérifications passées ! ===
📊 Observabilité et logs

Logs serveur → logs/server.log

Logs client → logs/client.log

Contiennent : request_id, type de message, décisions accept/reject, temps de traitement, erreurs.

-- Règles de validation et nettoyage:

Champs obligatoires : sensor_id, timestamp, type, value.
Types : float/int pour value, datetime ISO pour timestamp.
Plages réalistes :
temperature : [-50, 60]
humidity : [0, 100]
irrigation_mm : ≥ 0
Catégories normalisées : irrigation → ON/OFF.
Cohérence pompe/irrigation : si pump_status=OFF, irrigation_mm doit être 0.
Outliers : détectés avec z-score > 3 sigma sur temperature et humidity.

--Fichiers générés:

outputs/cleaned.csv → données nettoyées
outputs/cleaned_with_features.csv → données nettoyées + features
logs/server.log et logs/client.log → logs d’exécution
Rapport qualité → à générer via ETL ou script complémentaire