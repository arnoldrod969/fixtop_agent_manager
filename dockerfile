FROM python:3.10.6

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libblas-dev \
    liblapack-dev \
    libpng-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --no-cache-dir --upgrade pip

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port
EXPOSE 7000

# Lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7000", "--server.address=0.0.0.0"]