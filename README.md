INSTALLATION DE LA BASE DE DONNÉES POSTGRESQL POUR LE PROJET

Le code du projet est déjà configuré pour utiliser PostgreSQL.
Chaque membre doit seulement créer la base de données sur sa machine.

------------------------------------------------------------

1) INSTALLER POSTGRESQL

Télécharger et installer PostgreSQL.
Pendant l'installation :
- garder le port 5432
- retenir le mot de passe du compte postgres

------------------------------------------------------------

2) OUVRIR SQL SHELL

Ouvrir "SQL Shell (psql)".

Quand il demande :

Server [localhost]:
→ appuyer sur ENTER

Database [postgres]:
→ appuyer sur ENTER

Port [5432]:
→ appuyer sur ENTER

Username [postgres]:
→ écrire : postgres

Password:
→ entrer le mot de passe choisi pendant l'installation

Si tout fonctionne vous verrez :

postgres=#

------------------------------------------------------------

3) CRÉER L'UTILISATEUR DU PROJET

Dans SQL Shell taper :

CREATE USER pm_user WITH PASSWORD 'pm_password';

Puis ENTER.

------------------------------------------------------------

4) CRÉER LA BASE DE DONNÉES

Toujours dans SQL Shell taper :

CREATE DATABASE project_management_db OWNER pm_user;

Puis ENTER.

------------------------------------------------------------

5) DONNER LES DROITS

Toujours dans SQL Shell :

GRANT ALL PRIVILEGES ON DATABASE project_management_db TO pm_user;

Puis ENTER.

------------------------------------------------------------

6) VÉRIFIER QUE LA BASE EXISTE

Taper :

\l

Dans la liste vous devez voir :

project_management_db

------------------------------------------------------------

7) QUITTER SQL SHELL

Taper :

\q

------------------------------------------------------------

8) INSTALLER LES DÉPENDANCES PYTHON

Dans le dossier du projet (là où il y a manage.py) :

pip install -r requirements.txt

Si le fichier n'existe pas :

pip install django psycopg2-binary django-crispy-forms crispy-bootstrap4 pillow

------------------------------------------------------------

9) CRÉER LES TABLES DJANGO

Toujours dans le dossier du projet :

python manage.py makemigrations
python manage.py migrate

------------------------------------------------------------

10) CRÉER UN COMPTE ADMIN

python manage.py createsuperuser

------------------------------------------------------------

11) LANCER LE PROJET

python manage.py runserver

Puis ouvrir :

http://127.0.0.1:8000

Admin :

http://127.0.0.1:8000/admin

------------------------------------------------------------

Si le site fonctionne et que vous pouvez créer des utilisateurs ou projets,
alors PostgreSQL est correctement configuré.
