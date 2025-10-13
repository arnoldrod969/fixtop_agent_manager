import logging
import os

# Configuration du logger de débogage
def setup_debug_logger():
    """Configure un logger pour les messages de débogage silencieux"""
    logger = logging.getLogger('fixtop_debug')
    logger.setLevel(logging.DEBUG)
    
    # Éviter les doublons de handlers
    if not logger.handlers:
        # Handler pour fichier de log
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'debug.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Format des messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

# Instance globale du logger
debug_logger = setup_debug_logger()

def log_column_check(column_name, is_present, context=""):
    """Log silencieux pour vérifier la présence des colonnes"""
    if is_present:
        debug_logger.debug(f"Colonne '{column_name}' présente dans les données. {context}")
    else:
        debug_logger.warning(f"Colonne '{column_name}' manquante dans les données. {context}")

def log_data_info(df, context=""):
    """Log des informations sur le DataFrame"""
    debug_logger.info(f"DataFrame info - Lignes: {len(df)}, Colonnes: {list(df.columns)}. {context}")