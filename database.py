import sqlite3
import bcrypt
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "fixtop_agent.db"):
        """Initialise le gestionnaire de base de données"""
        self.db_path = db_path
        self.ensure_connection()
    
    def ensure_connection(self):
        """Vérifie que la base de données existe et est accessible"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Base de données non trouvée : {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Retourne une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        return conn
    
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe avec bcrypt (plus sécurisé que SHA-256)"""
        # Générer un salt et hasher le mot de passe
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérifie un mot de passe contre son hash bcrypt"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            # Fallback pour les anciens mots de passe SHA-256 (si nécessaire)
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Valide la force d'un mot de passe
        Retourne: (est_valide, liste_des_erreurs)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not any(c.isupper() for c in password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not any(c.islower() for c in password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if not any(c.isdigit() for c in password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        # Vérifier les mots de passe communs
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123", 
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        if password.lower() in common_passwords:
            errors.append("Ce mot de passe est trop commun")
        
        return len(errors) == 0, errors
    
    # ==================== GESTION DES RÔLES ====================
    
    def get_all_roles(self) -> List[Dict]:
        """Récupère tous les rôles actifs"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, is_active, created_at, updated_at 
                FROM role 
                WHERE is_active = 1 
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_role_by_id(self, role_id: int) -> Optional[Dict]:
        """Récupère un rôle par son ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, is_active, created_at, updated_at 
                FROM role 
                WHERE id = ? AND is_active = 1
            """, (role_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== GESTION DES UTILISATEURS ====================
    
    def get_all_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs avec leurs rôles"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.id, u.nin, u.name, u.email, u.role_id, u.is_active,
                    u.created_by, u.updated_by, u.created_at, u.updated_at,
                    r.name as role_name
                FROM user u
                LEFT JOIN role r ON u.role_id = r.id
                ORDER BY u.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur par son ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.id, u.nin, u.name, u.email, u.role_id, u.is_active,
                    u.created_by, u.updated_by, u.created_at, u.updated_at,
                    r.name as role_name
                FROM user u
                LEFT JOIN role r ON u.role_id = r.id
                WHERE u.id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Récupère un utilisateur par son email"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.id, u.nin, u.name, u.email, u.password, u.role_id, u.is_active,
                    u.created_by, u.updated_by, u.created_at, u.updated_at,
                    r.name as role_name
                FROM user u
                LEFT JOIN role r ON u.role_id = r.id
                WHERE u.email = ?
            """, (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_user(self, name: str, email: str, password: str, role_id: int, 
                   nin: str = None, created_by: int = None) -> Tuple[bool, str, Optional[int]]:
        """
        Crée un nouvel utilisateur
        Retourne: (succès, message, user_id)
        """
        try:
            # Vérifier si l'email existe déjà
            if self.get_user_by_email(email):
                return False, "Un utilisateur avec cet email existe déjà", None
            
            # Vérifier que le rôle existe
            if not self.get_role_by_id(role_id):
                return False, "Le rôle spécifié n'existe pas", None
            
            # Hash du mot de passe
            hashed_password = self.hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user (nin, name, email, password, role_id, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nin, name, email, hashed_password, role_id, created_by))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return True, f"Utilisateur '{name}' créé avec succès", user_id
                
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                return False, "Un utilisateur avec cet email existe déjà", None
            return False, f"Erreur d'intégrité : {str(e)}", None
        except Exception as e:
            return False, f"Erreur lors de la création : {str(e)}", None
    
    def update_user(self, user_id: int, name: str = None, email: str = None, 
                   role_id: int = None, nin: str = None, is_active: int = None,
                   updated_by: int = None) -> Tuple[bool, str]:
        """
        Met à jour un utilisateur
        Retourne: (succès, message)
        """
        try:
            # Construire la requête dynamiquement
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if role_id is not None:
                updates.append("role_id = ?")
                params.append(role_id)
            if nin is not None:
                updates.append("nin = ?")
                params.append(nin)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            if updated_by is not None:
                updates.append("updated_by = ?")
                params.append(updated_by)
            
            # Toujours mettre à jour updated_at
            updates.append("updated_at = datetime('now')")
            params.append(user_id)
            
            if not updates:
                return False, "Aucune modification spécifiée"
            
            query = f"UPDATE user SET {', '.join(updates)} WHERE id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return False, "Utilisateur non trouvé"
                
                conn.commit()
                return True, "Utilisateur mis à jour avec succès"
                
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                return False, "Un utilisateur avec cet email existe déjà"
            return False, f"Erreur d'intégrité : {str(e)}"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour : {str(e)}"
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """
        Supprime un utilisateur (soft delete - marque comme inactif)
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE user 
                    SET is_active = 0, updated_at = datetime('now')
                    WHERE id = ?
                """, (user_id,))
                
                if cursor.rowcount == 0:
                    return False, "Utilisateur non trouvé"
                
                conn.commit()
                return True, "Utilisateur désactivé avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la suppression : {str(e)}"
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authentifie un utilisateur
        Retourne les informations utilisateur si succès, None sinon
        """
        user = self.get_user_by_email(email)
        if user and user['is_active'] == 1:
            if self.verify_password(password, user['password']):
                # Retirer le mot de passe des données retournées
                user_data = dict(user)
                del user_data['password']
                return user_data
        return None
    
    # ==================== GESTION DES TICKETS/PROBLÈMES ====================
    
    def get_all_problems(self) -> List[Dict]:
        """Récupère tous les tickets/problèmes"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, 
                       u1.name as created_by_name,
                       u2.name as updated_by_name
                FROM problems p
                LEFT JOIN user u1 ON p.created_by = u1.id
                LEFT JOIN user u2 ON p.updated_by = u2.id
                WHERE p.is_active = 1
                ORDER BY p.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_problem_by_id(self, problem_id: int) -> Optional[Dict]:
        """Récupère un ticket/problème par son ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, 
                       u1.name as created_by_name,
                       u2.name as updated_by_name
                FROM problems p
                LEFT JOIN user u1 ON p.created_by = u1.id
                LEFT JOIN user u2 ON p.updated_by = u2.id
                WHERE p.id = ? AND p.is_active = 1
            """, (problem_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_problem(self, customer_name: str, customer_phone: str, 
                      problem_desc: str, created_by: int) -> Tuple[bool, str]:
        """
        Crée un nouveau ticket/problème
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO problems (customer_name, customer_phone, problem_desc, created_by)
                    VALUES (?, ?, ?, ?)
                """, (customer_name, customer_phone, problem_desc, created_by))
                
                conn.commit()
                return True, f"Ticket créé avec succès (ID: {cursor.lastrowid})"
                
        except Exception as e:
            return False, f"Erreur lors de la création : {str(e)}"
    
    def update_problem(self, problem_id: int, customer_name: str = None, 
                      customer_phone: str = None, problem_desc: str = None, 
                      updated_by: int = None) -> Tuple[bool, str]:
        """
        Met à jour un ticket/problème
        Retourne: (succès, message)
        """
        try:
            updates = []
            params = []
            
            if customer_name is not None:
                updates.append("customer_name = ?")
                params.append(customer_name)
            if customer_phone is not None:
                updates.append("customer_phone = ?")
                params.append(customer_phone)
            if problem_desc is not None:
                updates.append("problem_desc = ?")
                params.append(problem_desc)
            if updated_by is not None:
                updates.append("updated_by = ?")
                params.append(updated_by)
            
            # Toujours mettre à jour updated_at
            updates.append("updated_at = datetime('now')")
            params.append(problem_id)
            
            if not updates:
                return False, "Aucune modification spécifiée"
            
            query = f"UPDATE problems SET {', '.join(updates)} WHERE id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return False, "Ticket non trouvé"
                
                conn.commit()
                return True, "Ticket mis à jour avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la mise à jour : {str(e)}"
    
    def delete_problem(self, problem_id: int) -> Tuple[bool, str]:
        """
        Supprime un ticket/problème (soft delete - marque comme inactif)
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE problems 
                    SET is_active = 0, updated_at = datetime('now')
                    WHERE id = ?
                """, (problem_id,))
                
                if cursor.rowcount == 0:
                    return False, "Ticket non trouvé"
                
                conn.commit()
                return True, "Ticket supprimé avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la suppression : {str(e)}"
    
    def get_problem_stats(self) -> Dict:
        """Récupère les statistiques des tickets/problèmes"""
        with self.get_connection() as conn:
            # Nombre total de tickets
            cursor = conn.execute("SELECT COUNT(*) as total FROM problems WHERE is_active = 1")
            total = cursor.fetchone()['total']
            
            # Tickets par mois (derniers 6 mois)
            cursor = conn.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM problems 
                WHERE is_active = 1 AND created_at >= date('now', '-6 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
            """)
            by_month = [dict(row) for row in cursor.fetchall()]
            
            # Tickets créés aujourd'hui
            cursor = conn.execute("""
                SELECT COUNT(*) as today
                FROM problems 
                WHERE is_active = 1 AND date(created_at) = date('now')
            """)
            today = cursor.fetchone()['today']
            
            return {
                'total': total,
                'today': today,
                'by_month': by_month
            }

    # ==================== STATISTIQUES ====================
    
    def get_user_stats(self) -> Dict:
        """Récupère les statistiques des utilisateurs"""
        with self.get_connection() as conn:
            # Nombre total d'utilisateurs
            cursor = conn.execute("SELECT COUNT(*) as total FROM user")
            total = cursor.fetchone()['total']
            
            # Utilisateurs actifs
            cursor = conn.execute("SELECT COUNT(*) as active FROM user WHERE is_active = 1")
            active = cursor.fetchone()['active']
            
            # Utilisateurs par rôle
            cursor = conn.execute("""
                SELECT r.name, COUNT(u.id) as count
                FROM role r
                LEFT JOIN user u ON r.id = u.role_id AND u.is_active = 1
                GROUP BY r.id, r.name
                ORDER BY count DESC
            """)
            by_role = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total': total,
                'active': active,
                'inactive': total - active,
                'by_role': by_role
            }

# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()