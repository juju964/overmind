# Overmind (MVP)

Prototype **crawler + indexation + recherche sémantique + orchestration distribuée** en Python.

## TL;DR (version rapide)

Si tu veux juste voir que ça marche en 30 secondes (sans internet) :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
overmind-demo "meilleur langage pour faire un jeu 2D rapide"
```


## Il se trouve où ?

Depuis la racine du repo, tu peux afficher les chemins exacts avec :

```bash
python -m overmind.where
```

Après installation (`pip install -e .`), tu peux aussi faire :

```bash
overmind-where
```

Ça affiche en JSON :
- `project_root`
- `package_dir`
- `demo_module`
- `main_module`

## Comment télécharger le code

### Option 1 — depuis GitHub

- Clique sur **Code** > **Download ZIP**
- Ou en terminal :

```bash
git clone <url-du-repo>
cd overmind
```

### Option 2 — créer un ZIP local automatiquement

Depuis la racine du projet :

```bash
python -m overmind.export --output overmind-project.zip
```

Après installation, tu peux aussi utiliser :

```bash
overmind-export --output overmind-project.zip
```

Le fichier ZIP est créé à la racine du projet.

## Installation complète

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
```

## Je ne peux pas le voir : interface web locale + mini navigateur

Lance l'interface :

```bash
python -m overmind.web --port 8765
```

Puis ouvre : <http://127.0.0.1:8765/browser>

Tu as une vraie barre d'URL :
- tape `https://example.com` (ou juste `example.com`)
- clique **Aller**
- la page est chargée et rendue dans l'app

Si tu as installé le package, tu peux aussi faire :

```bash
overmind-web --port 8765
```

## Comment le faire fonctionner

### 1) Mode démo offline (recommandé pour commencer)

Aucun crawl web, dataset intégré.

```bash
overmind-demo "meilleur langage pour faire un jeu 2D rapide"
```

Tu dois voir un top de résultats avec scores.

### 2) Mode crawl web réel

```bash
overmind --seed https://example.com --max-pages 10 "jeu 2D rapide"
```

Sortie attendue :
1. nombre de documents indexés,
2. top PageRank,
3. résultats de recherche sémantique.

> Note : le crawl dépend du réseau, du site cible, et du contenu HTML dispo.

## Ce que contient ce dépôt

- `overmind/crawler.py` : crawler asynchrone multi-workers avec file d’attente, déduplication d’URLs, extraction de liens, nettoyage HTML, détection de langue.
- `overmind/indexer.py` : index inversé + scoring TF‑IDF + recherche lexicale.
- `overmind/semantic.py` : mini embeddings de cooccurrence (Word2Vec-like simplifié) + reranking sémantique.
- `overmind/distributed.py` : master/worker via sockets TCP, heartbeat, distribution de tâches.
- `overmind/simulation.py` : mini moteur de simulation de graphe (PageRank).
- `overmind/main.py` : exécutable CLI crawl + index + query.
- `overmind/demo.py` : exécutable CLI offline pour tester immédiatement.

## Architecture MVP

1. **Crawler distribué (local)** : pool `asyncio`, queue partagée, URLs visitées.
2. **Indexation avancée** : nettoyage HTML, tokenisation, normalisation, TF‑IDF, index inversé.
3. **Mini IA maison** : embeddings de cooccurrence + cosinus sparse.
4. **Recherche intelligente** : fusion score lexical + score sémantique.
5. **Système distribué** : MasterNode / WorkerNode via sockets + heartbeat.
6. **Simulation** : calcul PageRank sur graphe de liens.

## Limites actuelles

- Pas encore de persistance DB (stockage en mémoire)
- Pas encore d’interface web dashboard
- Crawler volontairement minimal (robots.txt / retries / politeness avancés à ajouter)
