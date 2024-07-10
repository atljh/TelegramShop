ssudo apt update
sudo apt install python3 python3-pip redis git screen postgresql nginx certbot python3-certbot-nginx
pip3 install aiogram psycopg2-binary asyncpg aioredis django

sudo nano /etc/nginx/sites-available/example.com
    server { 
            root /var/www/default/html;
            index index.html index.htm index.nginx-debian.html;

            server_name exmaple.com www.exmaple.com;

            location / {
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_pass http://localhost:7000;
            }
            location /admin/ {
                    proxy_pass http://localhost:8000;
            }
            location /static/admin/ {
                    proxy_pass http://localhost:8000;
            }
    
    } - Paste
ctrl + o, ctrl + x 

sudo ln -s /etc/nginx/sites-available/example.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

sudo certbot --nginx -d example.com
Choose redirect

sudo -u postgres psql -c 'create database db'
sudo -u postgres psql -c "create user usr with encrypted password 'passwd'"
sudo -u postgres psql -c 'grant all privileges on database db to usr'


screen -S admin

cd celmond_bot_admin
export $(grep -v '^#' .env | xargs)
cd admin
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver localhost:8000
ctrl + a + d


screen -S web_bot

cd celmond_bot_admin
export $(grep -v '^#' .env | xargs)
python3 main.py

