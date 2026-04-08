appuyer sur l’icône en forme de crayon à droite et d’ouvrir correctement le fichier.
INSTALLATION DU PROJET (POSTGRESQL + DJANGO)

Le projet est configuré pour utiliser PostgreSQL.

------------------------------------------------------------------------

1)  INSTALLER POSTGRESQL

Télécharger et installer PostgreSQL.

Pendant l’installation : - garder le port 5432 - retenir le mot de passe
du compte postgres

------------------------------------------------------------------------

2)  OUVRIR SQL SHELL

Ouvrir “SQL Shell (psql)”.

Répondre comme suit :

Server [localhost]: → ENTER
Database [postgres]: → ENTER
Port [5432]: → ENTER
Username [postgres]: → postgres
Password: → votre mot de passe

Si tout fonctionne :
postgres=#

------------------------------------------------------------------------

3)  CRÉER L’UTILISATEUR

CREATE USER pm_user WITH PASSWORD ‘pm_password’;

------------------------------------------------------------------------

4)  CRÉER LA BASE DE DONNÉES

CREATE DATABASE project_management_db OWNER pm_user;

------------------------------------------------------------------------

5)  DONNER LES DROITS

GRANT ALL PRIVILEGES ON DATABASE project_management_db TO pm_user;

------------------------------------------------------------------------

6)  VÉRIFIER

Vous devez voir :
project_management_db

------------------------------------------------------------------------

7)  QUITTER

------------------------------------------------------------------------

8)  INSTALLER LES DÉPENDANCES

ouvrir un terminal

pip install django psycopg2-binary django-crispy-forms crispy-bootstrap4
pillow

------------------------------------------------------------------------

9)  MIGRATIONS

python manage.py makemigrations

python manage.py migrate

------------------------------------------------------------------------

10) CHARGER LES DONNÉES DE TEST

python manage.py loaddata initial_data.json

------------------------------------------------------------------------

11) CONFIGURER LES MOTS DE PASSE (IMPORTANT)

Après avoir chargé les données, exécuter :

python manage.py shell

Puis :

from django.contrib.auth.models import User

u = User.objects.get(username="eloise")
u.set_password("1234")
u.save()

u = User.objects.get(username="gregory")
u.set_password("1234")
u.save()
exit()

------------------------------------------------------------------------

12) LANCER LE PROJET

python manage.py runserver

http://127.0.0.1:8000

Admin : http://127.0.0.1:8000/admin

------------------------------------------------------------------------

COMPTES DE DÉMONSTRATION

Administrateur :
username : eloise
password : 1234

Utilisateur standard :
username : gregory
password : 1234

------------------------------------------------------------------------

RÔLES

Eloise : administrateur (gestion complète des projets)
Gregory : utilisateur standard (accès limité)
