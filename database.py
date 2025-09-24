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
                return False, "A user with this email already exists", None
            
            # Vérifier que le rôle existe
            if not self.get_role_by_id(role_id):
                return False, "The specified role does not exist", None
            
            # Hash du mot de passe
            hashed_password = self.hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO user (nin, name, email, password, role_id, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ? , ?)
                """, (nin, name, email, hashed_password, role_id, created_by , created_by))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return True, f"User '{name}' successfully created", user_id
                
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                return False, "A user with this email already exists", None
            return False, f"Integrity error: {str(e)}", None
        except Exception as e:
            return False, f"Error creating user: {str(e)}", None
    
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
                return False, "No changes specified"
            
            query = f"UPDATE user SET {', '.join(updates)} WHERE id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return False, "User not found"
                
                conn.commit()
                return True, "User updated successfully"
                
        except sqlite3.IntegrityError as e:
            if "email" in str(e).lower():
                return False, "A user with this email already exists"
            return False, f"Integrity error: {str(e)}"
        except Exception as e:
            return False, f"Error updating user: {str(e)}"
    
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
                return True, "User disabled successfully"
                
        except Exception as e:
            return False, f"Error disabling user: {str(e)}"
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticates a user
        Returns user data if successful, None otherwise
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
                return True, f"Problem created successfully (ID: {cursor.lastrowid})"
                
        except Exception as e:
            return False, f"Error creating problem: {str(e)}"
    
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
                return False, "No changes specified"
            
            query = f"UPDATE problems SET {', '.join(updates)} WHERE id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return False, "Problem not found"
                
                conn.commit()
                return True, "Problem updated successfully"
                
        except Exception as e:
            return False, f"Error updating problem: {str(e)}"
    
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
                    return False, "Problem not found"
                
                conn.commit()
                return True, "Problem deleted successfully"
                
        except Exception as e:
            return False, f"Error deleting problem: {str(e)}"
    
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


    def get_teams(self) -> List[Dict]:
        """Récupère toutes les équipes avec les informations du manager"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.id,
                       t.code,
                       t.name,
                       t.description,
                       t.manager_id,
                       t.is_active,
                       t.created_at,
                       t.updated_at,
                       u1.name as created_by_name,
                       u2.name as updated_by_name,
                       u3.name as manager_name,
                       u3.email as manager_email
                FROM team t
                LEFT JOIN user u1 ON t.created_by = u1.id
                LEFT JOIN user u2 ON t.updated_by = u2.id
                LEFT JOIN user u3 ON t.manager_id = u3.id
                WHERE t.is_active = 1
                ORDER BY t.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_team_by_id(self, team_id: int) -> Optional[Dict]:
        """Récupère une équipe par son ID avec les informations du manager"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.*, 
                       u1.name as created_by_name,
                       u2.name as updated_by_name,
                       u3.name as manager_name,
                       u3.email as manager_email
                FROM team t
                LEFT JOIN user u1 ON t.created_by = u1.id
                LEFT JOIN user u2 ON t.updated_by = u2.id
                LEFT JOIN user u3 ON t.manager_id = u3.id
                WHERE t.id = ? AND t.is_active = 1
            """, (team_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def generate_team_code(self) -> str:
        """
        Generate a unique team code in format TEAM001, TEAM002, etc.
        Returns: Generated team code
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT code FROM team 
                    WHERE code LIKE 'TEAM%' 
                    ORDER BY CAST(SUBSTR(code, 5) AS INTEGER) DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                
                if row and row[0]:
                    # Extract number from existing code (e.g., TEAM001 -> 1)
                    last_number = int(row[0][4:])  # Remove 'TEAM' prefix
                    new_number = last_number + 1
                else:
                    # First team
                    new_number = 1
                
                # Format with leading zeros (TEAM001, TEAM002, etc.)
                return f"TEAM{new_number:03d}"
                
        except Exception as e:
            # Fallback to timestamp-based code if there's an error
            import time
            return f"TEAM{int(time.time()) % 10000:04d}"

    def create_team(self, name: str, manager_id: int, description: str = None, created_by: int = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new team with automatic code generation and manager assignment
        Args:
            name: Team name (must be unique)
            manager_id: ID of the manager (must be unique - one manager per team)
            description: Optional team description
            created_by: ID of the user creating the team
        Returns: (success, message, team_id)
        """
        try:
            with self.get_connection() as conn:
                # Check if name already exists
                cursor = conn.execute("""
                    SELECT id FROM team WHERE name = ? AND is_active = 1
                """, (name,))
                if cursor.fetchone():
                    return False, "A team with this name already exists", None

                # Check if manager is already assigned to another team
                cursor = conn.execute("""
                    SELECT id, name FROM team WHERE manager_id = ? AND is_active = 1
                """, (manager_id,))
                existing_team = cursor.fetchone()
                if existing_team:
                    return False, f"This manager is already assigned to team '{existing_team[1]}'", None

                # Verify that the manager exists and is active
                cursor = conn.execute("""
                    SELECT id, name FROM user WHERE id = ? AND is_active = 1
                """, (manager_id,))
                manager = cursor.fetchone()
                if not manager:
                    return False, "Invalid manager ID or manager is not active", None

                # Generate unique team code
                team_code = self.generate_team_code()
                
                # Ensure code is unique (double-check)
                cursor = conn.execute("""
                    SELECT id FROM team WHERE code = ?
                """, (team_code,))
                if cursor.fetchone():
                    # If somehow the code exists, generate a timestamp-based one
                    import time
                    team_code = f"TEAM{int(time.time()) % 10000:04d}"

                # Create the team with auto-generated code and manager
                cursor = conn.execute("""
                    INSERT INTO team (name, code, description, manager_id, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, team_code, description, manager_id, created_by, created_by))
                
                team_id = cursor.lastrowid
                conn.commit()
                
                return True, f"Team '{name}' successfully created with code {team_code} and manager '{manager[1]}'", team_id
                
        except Exception as e:
            return False, f"Error creating team: {str(e)}", None

    def update_team(self, team_id: int, name: str = None, description: str = None, 
                   manager_id: int = None, updated_by: int = None) -> Tuple[bool, str]:
        """
        Met à jour une équipe
        Retourne: (succès, message)
        """
        try:
            # Construire la requête dynamiquement
            updates = []
            params = []
            
            if name is not None:
                # Vérifier si le nom existe déjà (sauf pour cette équipe)
                with self.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT id FROM team WHERE name = ? AND id != ? AND is_active = 1
                    """, (name, team_id))
                    if cursor.fetchone():
                        return False, "Une équipe avec ce nom existe déjà"
                
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if manager_id is not None:
                # Vérifier que le manager existe et est actif
                with self.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT u.id, u.name, u.email FROM user u
                        JOIN role r ON u.role_id = r.id
                        WHERE u.id = ? AND u.is_active = 1 AND r.name = 'manager'
                    """, (manager_id,))
                    manager = cursor.fetchone()
                    
                    if not manager:
                        return False, "Manager non trouvé ou inactif"
                    
                    # Vérifier que ce manager ne gère pas déjà une autre équipe
                    cursor = conn.execute("""
                        SELECT id, name FROM team 
                        WHERE manager_id = ? AND id != ? AND is_active = 1
                    """, (manager_id, team_id))
                    existing_team = cursor.fetchone()
                    
                    if existing_team:
                        return False, f"Ce manager gère déjà l'équipe '{existing_team[1]}'"
                
                updates.append("manager_id = ?")
                params.append(manager_id)
            
            if updated_by is not None:
                updates.append("updated_by = ?")
                params.append(updated_by)
            
            # Toujours mettre à jour updated_at
            updates.append("updated_at = datetime('now')")
            params.append(team_id)
            
            if not updates:
                return False, "Aucune modification spécifiée"
            
            query = f"UPDATE team SET {', '.join(updates)} WHERE id = ? AND is_active = 1"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                
                if cursor.rowcount == 0:
                    return False, "Équipe non trouvée"
                
                conn.commit()
                return True, "Équipe mise à jour avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la mise à jour de l'équipe: {str(e)}"

    def delete_team(self, team_id: int, updated_by: int = None) -> Tuple[bool, str]:
        """
        Supprime une équipe (hard delete - suppression définitive)
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                # Vérifier si l'équipe existe
                cursor = conn.execute("""
                    SELECT name FROM team WHERE id = ? AND is_active = 1
                """, (team_id,))
                team = cursor.fetchone()
                
                if not team:
                    return False, "Équipe non trouvée"
                
                # Supprimer définitivement tous les membres de l'équipe
                cursor = conn.execute("""
                    DELETE FROM team_member 
                    WHERE team_id = ?
                """, (team_id,))
                
                # Supprimer définitivement l'équipe
                cursor = conn.execute("""
                    DELETE FROM team 
                    WHERE id = ?
                """, (team_id,))
                
                conn.commit()
                return True, f"Équipe '{team['name']}' supprimée définitivement avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la suppression de l'équipe: {str(e)}"

    def get_team_stats(self) -> Dict:
        """Récupère les statistiques des équipes"""
        with self.get_connection() as conn:
            # Nombre total d'équipes
            cursor = conn.execute("SELECT COUNT(*) as total FROM team WHERE is_active = 1")
            total = cursor.fetchone()['total']
            
            # Équipes créées aujourd'hui
            cursor = conn.execute("""
                SELECT COUNT(*) as today
                FROM team 
                WHERE is_active = 1 AND date(created_at) = date('now')
            """)
            today = cursor.fetchone()['today']
            
            # Équipes par mois (derniers 6 mois)
            cursor = conn.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM team 
                WHERE is_active = 1 AND created_at >= date('now', '-6 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
            """)
            by_month = [dict(row) for row in cursor.fetchall()]
            
            # Taille moyenne des équipes
            cursor = conn.execute("""
                SELECT AVG(member_count) as avg_size
                FROM (
                    SELECT COUNT(tm.id) as member_count
                    FROM team t
                    LEFT JOIN team_member tm ON t.id = tm.team_id AND tm.is_active = 1
                    WHERE t.is_active = 1
                    GROUP BY t.id
                )
            """)
            avg_size_result = cursor.fetchone()
            avg_size = round(avg_size_result['avg_size'] or 0, 1)
            
            return {
                'total': total,
                'today': today,
                'by_month': by_month,
                'avg_size': avg_size
            }

    # Méthodes pour la gestion des membres d'équipes
    def get_team_members(self, team_id: int) -> List[Dict]:
        """Récupère tous les membres d'une équipe"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT tm.*, 
                       tm.member_id as user_id,
                       u.name as user_name,
                       u.email as user_email,
                       r.name as user_role,
                       u1.name as created_by_name,
                       u2.name as updated_by_name
                FROM team_member tm
                JOIN user u ON tm.member_id = u.id
                LEFT JOIN role r ON u.role_id = r.id
                LEFT JOIN user u1 ON tm.created_by = u1.id
                LEFT JOIN user u2 ON tm.updated_by = u2.id
                WHERE tm.team_id = ? AND tm.is_active = 1
                ORDER BY tm.created_at DESC
            """, (team_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_team_member(self, team_id: int, user_id: int, created_by: int = None) -> Tuple[bool, str]:
        """
        Ajoute un membre à une équipe
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                # Vérifier si l'équipe existe
                cursor = conn.execute("""
                    SELECT name FROM team WHERE id = ? AND is_active = 1
                """, (team_id,))
                team = cursor.fetchone()
                if not team:
                    return False, "Équipe non trouvée"
                
                # Vérifier si l'utilisateur existe
                cursor = conn.execute("""
                    SELECT name FROM user WHERE id = ? AND is_active = 1
                """, (user_id,))
                user = cursor.fetchone()
                if not user:
                    return False, "Utilisateur non trouvé"
                
                # Vérifier si l'utilisateur n'est pas déjà membre
                cursor = conn.execute("""
                    SELECT id FROM team_member 
                    WHERE team_id = ? AND member_id = ? AND is_active = 1
                """, (team_id, user_id))
                if cursor.fetchone():
                    return False, f"L'utilisateur {user['name']} est déjà membre de l'équipe {team['name']}"
                
                # Ajouter le membre
                cursor = conn.execute("""
                    INSERT INTO team_member (team_id, member_id, created_by, updated_by)
                    VALUES (?, ?, ?, ?)
                """, (team_id, user_id, created_by, created_by))
                
                conn.commit()
                return True, f"Utilisateur {user['name']} ajouté à l'équipe {team['name']} avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de l'ajout du membre: {str(e)}"

    def remove_team_member(self, team_id: int, user_id: int, updated_by: int = None) -> Tuple[bool, str]:
        """
        Retire un membre d'une équipe (hard delete)
        Retourne: (succès, message)
        """
        try:
            with self.get_connection() as conn:
                # Vérifier si le membre existe
                cursor = conn.execute("""
                    SELECT tm.id, t.name as team_name, u.name as user_name
                    FROM team_member tm
                    JOIN team t ON tm.team_id = t.id
                    JOIN user u ON tm.member_id = u.id
                    WHERE tm.team_id = ? AND tm.member_id = ? AND tm.is_active = 1
                """, (team_id, user_id))
                member = cursor.fetchone()
                
                if not member:
                    return False, "Membre non trouvé dans cette équipe"
                
                # Supprimer définitivement le membre (hard delete)
                cursor = conn.execute("""
                    DELETE FROM team_member 
                    WHERE team_id = ? AND member_id = ?
                """, (team_id, user_id))
                
                conn.commit()
                return True, f"Utilisateur {member['user_name']} retiré de l'équipe {member['team_name']} avec succès"
                
        except Exception as e:
            return False, f"Erreur lors de la suppression du membre: {str(e)}"

    def get_user_teams(self, user_id: int) -> List[Dict]:
        """Récupère toutes les équipes dont un utilisateur est membre"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.*, tm.created_at as joined_at
                FROM team t
                JOIN team_member tm ON t.id = tm.team_id
                WHERE tm.member_id = ? AND t.is_active = 1 AND tm.is_active = 1
                ORDER BY tm.created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_available_users_for_team(self, team_id: int) -> List[Dict]:
        """Récupère les agents qui ne sont membres d'aucune équipe active"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT u.id, u.name, u.email, r.name as role
                FROM user u
                LEFT JOIN role r ON u.role_id = r.id
                WHERE u.is_active = 1 
                AND r.name = 'agent'
                AND u.id NOT IN (
                    SELECT tm.member_id 
                    FROM team_member tm 
                    JOIN team t ON tm.team_id = t.id
                    WHERE tm.is_active = 1 AND t.is_active = 1
                )
                ORDER BY u.name
            """, ())
            return [dict(row) for row in cursor.fetchall()]

    # Méthodes de validation pour les contraintes d'unicité
    def is_manager_available(self, manager_id: int, exclude_team_id: int = None) -> bool:
        """
        Vérifie si un manager est disponible (pas déjà assigné à une autre équipe)
        Args:
            manager_id: ID du manager à vérifier
            exclude_team_id: ID de l'équipe à exclure de la vérification (pour les mises à jour)
        Returns:
            True si le manager est disponible, False sinon
        """
        with self.get_connection() as conn:
            query = """
                SELECT COUNT(*) as count
                FROM team 
                WHERE manager_id = ? AND is_active = 1
            """
            params = [manager_id]
            
            if exclude_team_id:
                query += " AND id != ?"
                params.append(exclude_team_id)
            
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            return result['count'] == 0

    def is_agent_available(self, user_id: int, exclude_team_id: int = None) -> bool:
        """
        Vérifie si un agent est disponible (pas déjà membre d'une autre équipe)
        Args:
            user_id: ID de l'utilisateur à vérifier
            exclude_team_id: ID de l'équipe à exclure de la vérification (pour les mises à jour)
        Returns:
            True si l'agent est disponible, False sinon
        """
        with self.get_connection() as conn:
            query = """
                SELECT COUNT(*) as count
                FROM team_member tm
                JOIN team t ON tm.team_id = t.id
                WHERE tm.member_id = ? AND tm.is_active = 1 AND t.is_active = 1
            """
            params = [user_id]
            
            if exclude_team_id:
                query += " AND tm.team_id != ?"
                params.append(exclude_team_id)
            
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            return result['count'] == 0

    def get_manager_current_team(self, manager_id: int) -> Dict:
        """
        Récupère l'équipe actuellement gérée par un manager
        Returns:
            Dictionnaire avec les informations de l'équipe ou None si aucune équipe
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, code, description
                FROM team 
                WHERE manager_id = ? AND is_active = 1
            """, (manager_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_agent_current_team(self, user_id: int) -> Dict:
        """
        Récupère l'équipe dont un agent est actuellement membre
        Returns:
            Dictionnaire avec les informations de l'équipe ou None si aucune équipe
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.id, t.name, t.code, t.description
                FROM team t
                JOIN team_member tm ON t.id = tm.team_id
                WHERE tm.member_id = ? AND tm.is_active = 1 AND t.is_active = 1
            """, (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def validate_team_constraints(self, manager_id: int, member_ids: List[int] = None, exclude_team_id: int = None) -> Tuple[bool, str]:
        """
        Valide toutes les contraintes d'équipe avant création/modification
        Args:
            manager_id: ID du manager
            member_ids: Liste des IDs des membres (optionnel)
            exclude_team_id: ID de l'équipe à exclure (pour les mises à jour)
        Returns:
            (succès, message d'erreur si échec)
        """
        # Vérifier la disponibilité du manager
        if not self.is_manager_available(manager_id, exclude_team_id):
            current_team = self.get_manager_current_team(manager_id)
            return False, f"Ce manager gère déjà l'équipe '{current_team['name']}' (Code: {current_team['code']})"
            
            # Vérifier la disponibilité des membres si fournis
            if member_ids:
                for member_id in member_ids:
                    if not self.is_agent_available(member_id, exclude_team_id):
                        current_team = self.get_agent_current_team(member_id)
                        user_info = self.get_user_by_id(member_id)
                        return False, f"L'agent '{user_info['name']}' appartient déjà à l'équipe '{current_team['name']}' (Code: {current_team['code']})"
            
            return True, "Toutes les contraintes sont respectées"


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()