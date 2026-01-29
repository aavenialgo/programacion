"""
Sistema de autenticación simple basado en contraseña para el servidor WebSocket.
"""
import secrets
import hashlib
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Gestor de autenticación con tokens de sesión.
    
    Implementa un sistema simple de autenticación por contraseña con tokens.
    """
    
    def __init__(self, password: str, session_timeout_hours: int = 24):
        """
        Inicializa el gestor de autenticación.
        
        Args:
            password: Contraseña para autenticación
            session_timeout_hours: Horas antes de que expire un token
        """
        self.password_hash = self._hash_password(password)
        self.session_timeout = session_timeout_hours * 3600  # Convertir a segundos
        
        # Diccionario de tokens activos: {token: timestamp}
        self.active_tokens: Dict[str, float] = {}
        
        logger.info("AuthManager inicializado")
    
    def _hash_password(self, password: str) -> str:
        """
        Genera un hash SHA-256 de la contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash hexadecimal de la contraseña
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, password: str) -> Optional[str]:
        """
        Autentica un usuario con contraseña y genera un token.
        
        Args:
            password: Contraseña proporcionada
            
        Returns:
            str: Token de sesión si la autenticación es exitosa, None si falla
        """
        password_hash = self._hash_password(password)
        
        if password_hash == self.password_hash:
            # Generar token único
            token = secrets.token_urlsafe(32)
            self.active_tokens[token] = time.time()
            
            logger.info(f"Usuario autenticado. Token generado: {token[:8]}...")
            return token
        else:
            logger.warning("Intento de autenticación fallido")
            return None
    
    def validate_token(self, token: str) -> bool:
        """
        Valida si un token es válido y no ha expirado.
        
        Args:
            token: Token de sesión a validar
            
        Returns:
            bool: True si el token es válido y no ha expirado
        """
        if token not in self.active_tokens:
            return False
        
        # Verificar expiración
        token_time = self.active_tokens[token]
        if time.time() - token_time > self.session_timeout:
            # Token expirado, eliminarlo
            del self.active_tokens[token]
            logger.info(f"Token expirado y eliminado: {token[:8]}...")
            return False
        
        return True
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoca un token de sesión.
        
        Args:
            token: Token a revocar
            
        Returns:
            bool: True si el token fue revocado, False si no existía
        """
        if token in self.active_tokens:
            del self.active_tokens[token]
            logger.info(f"Token revocado: {token[:8]}...")
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """Elimina todos los tokens expirados."""
        current_time = time.time()
        expired_tokens = [
            token for token, timestamp in self.active_tokens.items()
            if current_time - timestamp > self.session_timeout
        ]
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        if expired_tokens:
            logger.info(f"Eliminados {len(expired_tokens)} tokens expirados")
    
    def get_active_sessions_count(self) -> int:
        """
        Retorna el número de sesiones activas.
        
        Returns:
            int: Número de tokens activos
        """
        # Limpiar tokens expirados primero
        self.cleanup_expired_tokens()
        return len(self.active_tokens)
    
    def get_session_info(self, token: str) -> Optional[dict]:
        """
        Obtiene información sobre una sesión.
        
        Args:
            token: Token de sesión
            
        Returns:
            dict: Información de la sesión o None si no existe
        """
        if token not in self.active_tokens:
            return None
        
        token_time = self.active_tokens[token]
        age_seconds = time.time() - token_time
        remaining_seconds = max(0, self.session_timeout - age_seconds)
        
        return {
            "token": token[:8] + "...",  # Mostrar solo inicio del token
            "created": token_time,
            "age_seconds": age_seconds,
            "remaining_seconds": remaining_seconds,
            "is_valid": remaining_seconds > 0
        }
    
    def list_active_sessions(self) -> list:
        """
        Lista todas las sesiones activas.
        
        Returns:
            list: Lista de información de sesiones activas
        """
        self.cleanup_expired_tokens()
        return [
            self.get_session_info(token)
            for token in self.active_tokens.keys()
        ]


if __name__ == "__main__":
    # Ejemplo de uso
    import time
    
    # Crear gestor de autenticación
    auth = AuthManager(password="test123", session_timeout_hours=24)
    
    # Probar autenticación exitosa
    print("=== Prueba de autenticación exitosa ===")
    token = auth.authenticate("test123")
    if token:
        print(f"✓ Token generado: {token[:16]}...")
        print(f"✓ Token válido: {auth.validate_token(token)}")
    else:
        print("✗ Autenticación fallida")
    
    # Probar autenticación fallida
    print("\n=== Prueba de autenticación fallida ===")
    bad_token = auth.authenticate("wrongpass")
    if bad_token is None:
        print("✓ Autenticación rechazada correctamente")
    else:
        print("✗ Se generó token con contraseña incorrecta")
    
    # Probar validación de token inválido
    print("\n=== Prueba de token inválido ===")
    fake_token = "faktoken123"
    is_valid = auth.validate_token(fake_token)
    print(f"Token falso válido: {is_valid} (debe ser False)")
    
    # Información de sesiones
    print("\n=== Información de sesiones ===")
    print(f"Sesiones activas: {auth.get_active_sessions_count()}")
    
    if token:
        session_info = auth.get_session_info(token)
        print(f"Info de sesión: {session_info}")
    
    # Probar revocación
    print("\n=== Prueba de revocación ===")
    if token:
        print(f"Token válido antes de revocar: {auth.validate_token(token)}")
        auth.revoke_token(token)
        print(f"Token válido después de revocar: {auth.validate_token(token)}")
    
    print("\n=== Pruebas completadas ===")
