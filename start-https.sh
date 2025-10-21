#!/bin/bash

echo "🌐 Démarrage de l'application en HTTPS sur le port 7000"

# Vérifier si le domaine est défini
if [ -z "$DOMAIN_NAME" ]; then
    echo "❌ ERREUR: DOMAIN_NAME non défini"
    echo "Utilisez: DOMAIN_NAME=votre-domaine.com EMAIL=votre@email.com docker-compose up"
    exit 1
fi

# Créer le répertoire webroot pour certbot
mkdir -p /var/www/html

# Obtenir le certificat Let's Encrypt si il n'existe pas
if [ ! -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]; then
    echo "📜 Génération du certificat SSL pour $DOMAIN_NAME"
    certbot certonly \
        --standalone \
        -d $DOMAIN_NAME \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        --preferred-challenges http
fi

# Configurer le renouvellement automatique
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

echo "🚀 Lancement de Streamlit en HTTPS sur le port 7000"

# Démarrer Streamlit avec HTTPS sur le port 7000
streamlit run app.py \
    --server.port=7000 \
    --server.address=0.0.0.0 \
    --server.sslCertFile=/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem \
    --server.sslKeyFile=/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem