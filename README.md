
[![Gemini-Generated-Image-xuk5x3xuk5x3xuk5.png](https://i.postimg.cc/9M1M9TM8/Gemini-Generated-Image-xuk5x3xuk5x3xuk5.png)](https://postimg.cc/LYY2KJjL)


Assistant juridique intelligent  est un agent IA spécialisé dans la recherche, l’analyse et la synthèse de contenus juridiques. Il combine : 
* Une compréhension fine des requêtes utilisateur (clarification intelligente),
* Une recherche ciblée via outils externes (Tavily, réflexion interne),
* Une synthèse structurée et fiable adaptée aux besoins juridiques.
     

# 🧠 Technologies clés :
 LangGraph, LangChain, Ollama, modèles LLM open-source (Mistral-Nemo, Phi-3), architecture modulaire. 

🔒 100% local & open source — respect de la confidentialité, aucune dépendance cloud, aucun coût d’API. 

# 🎯 Fonctionnalités 

✅ Clarification intelligente : reformule ou demande des précisions si la requête est ambiguë.
✅ Génération de brief structuré : extrait la question juridique centrale, le pays, les sources officielles.
✅ Recherche automatisée : appelle des outils (web juridique, réflexion interne) pour collecter des données fiables.
✅ Synthèse experte : compresse les résultats en un rapport clair, précis et citant les sources.
✅ Workflow entièrement traçable : chaque étape est loggée, inspectable, reproductible.
✅ Architecture modulaire : chaque composant (scope, recherche, compression) peut être remplacé indépendamment.
✅ Multi-pays : paramétrable pour la France, Belgique, Suisse, Canada, etc. 

# 🧩 Architecture Technique
[![graphe-1.png](https://i.postimg.cc/sg5pb6xt/graphe-1.png)](https://postimg.cc/K1vkM5nN)



## ⚙️ Installation & Configuration
```bash
git clone -b mariem-branch https://github.com/zouaghisarra/back_multi-agent.git 
```
```bash
cd back_multi-agent
```
💡 Tu peux ouvrir le projet dans VS Code :
```bash
code . 
```
Vérifier la version de Python
```bash
python --version
# ou parfois :
python3 --version
```
Créer et activer l’environnement virtuel
```bash
python -m venv venv
```
➤ Sur Windows :
```bash
venv\Scripts\activate
```
 Installer les dépendances
```bash
python -m pip install -r requirement.txt
```
> ⚠️ Si pip n’est pas reconnu, utilise python -m pip install -r requirements.txt

Installer et configurer Neo4j

  * Télécharge et installe Neo4j Desktop 
  * Lance Neo4j Desktop et crée une nouvelle base de données.
  * Active les plugins nécessaires (ex: APOC, Graph Data Science) via les paramètres :
     
[![image.png](https://i.postimg.cc/3J266rXs/image.png)](https://postimg.cc/vcH3xsSh)

Installer et configurer Ollama 

Télécharge et installe Ollama 

Télécharge les modèles LLM nécessaires :
     
```bash
ollama pull mistral:latest
ollama pull mistral-nemo:latest
ollama pull phi3:medium
```
🚀 Lancer le projet 

Une fois toutes les dépendances installées et les services (Neo4j, Ollama) démarrés : 
```bash
uvicorn source.api.main:app --host 127.0.0.1 --port 8000 --reload
```
L’API sera accessible à l’adresse : http://localhost:8000
La documentation Swagger (OpenAPI) sera disponible à : http://localhost:8000/docs

[![image.png](https://i.postimg.cc/YS5BjSM4/image.png)](https://postimg.cc/hJ155cJg)

[![image.png](https://i.postimg.cc/RCGpD0yc/image.png)](https://postimg.cc/DmJcW72Z)