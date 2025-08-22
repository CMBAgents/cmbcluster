import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger()

class FileEncryption:
    """Secure file encryption utility using Fernet (AES 128 in CBC mode)"""
    
    def __init__(self, encryption_key: str = None):
        """Initialize with encryption key from environment or provided key"""
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Get from environment or generate
            self.key = self._get_or_generate_key()
        
        # Derive a proper Fernet key from the provided key
        self.fernet = self._create_fernet_key()
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from environment or generate a new one"""
        key = os.environ.get('FILE_ENCRYPTION_KEY')
        if not key:
            # Generate a new key - this should only happen in development
            key = Fernet.generate_key().decode()
            logger.warning(
                "No FILE_ENCRYPTION_KEY found in environment. Generated temporary key. "
                "For production, set FILE_ENCRYPTION_KEY environment variable. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        else:
            logger.info("Using encryption key from environment variable")
            
        return key.encode()
    
    def _create_fernet_key(self) -> Fernet:
        """Create Fernet instance with proper key derivation"""
        # Use PBKDF2 to derive a proper 32-byte key from the provided key
        salt = b'cmbcluster_file_salt'  # In production, use a random salt per installation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.key))
        return Fernet(key)
    
    def encrypt_content(self, content: str) -> bytes:
        """Encrypt string content and return encrypted bytes"""
        try:
            content_bytes = content.encode('utf-8')
            encrypted = self.fernet.encrypt(content_bytes)
            logger.debug("Content encrypted successfully", content_size=len(content))
            return encrypted
        except Exception as e:
            logger.error("Failed to encrypt content", error=str(e))
            raise
    
    def decrypt_content(self, encrypted_content: bytes) -> str:
        """Decrypt bytes and return string content"""
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_content)
            content = decrypted_bytes.decode('utf-8')
            logger.debug("Content decrypted successfully", content_size=len(content))
            return content
        except Exception as e:
            logger.error("Failed to decrypt content", error=str(e))
            raise
    
    def encrypt_file_data(self, file_data: bytes) -> bytes:
        """Encrypt file data bytes"""
        try:
            encrypted = self.fernet.encrypt(file_data)
            logger.debug("File data encrypted successfully", data_size=len(file_data))
            return encrypted
        except Exception as e:
            logger.error("Failed to encrypt file data", error=str(e))
            raise
    
    def decrypt_file_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt file data bytes"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data)
            logger.debug("File data decrypted successfully", data_size=len(decrypted))
            return decrypted
        except Exception as e:
            logger.error("Failed to decrypt file data", error=str(e))
            raise

# Global encryption instance
_encryption_instance = None

def get_file_encryption() -> FileEncryption:
    """Get global file encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = FileEncryption()
    return _encryption_instance
