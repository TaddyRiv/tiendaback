python -m venv venv  
venv\Scripts\activate
pip install -r requirements.txt


actualizar requerimiento si se añade alguna libreria
pip freeze > requirements.txt    

crear el .env y conectar con postgres
DB_NAME=tiendaropa
DB_USER=postgres
DB_PASSWORD=contraseña
DB_HOST=127.0.0.1
DB_PORT=5432

SECRET_KEY=django-insecure-tu-clave-secreta-aqui
DEBUG=True

para verificar si existe la libreria simplejwt
pip list | findstr simplejwt


python manage.py makemigrations
python manage.py migrate

correr seeders en este orden

python manage.py seed_roles
python manage.py seed_ventas


python manage.py runserver