FROM python:3.10.6

WORKDIR /app

# Installer certbot pour Let's Encrypt
RUN apt-get update && apt-get install -y \
    certbot \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --no-cache-dir --upgrade pip

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port 7000 (comme actuellement)
EXPOSE 7000

# Script de démarrage HTTPS
COPY start-https.sh /start-https.sh
RUN chmod +x /start-https.sh

CMD ["/start-https.sh"]