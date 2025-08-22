"""
File migration utilities for handling encryption key changes
"""
import structlog
from database import get_db_connection
from file_encryption import FileEncryption

logger = structlog.get_logger()

def check_file_decryption_health():
    """Check if existing files can be decrypted with current key"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all encrypted files
        cursor.execute("SELECT id, file_name, encrypted_content FROM user_files")
        files = cursor.fetchall()
        
        encryption = FileEncryption()
        failed_files = []
        
        for file_id, file_name, encrypted_content in files:
            try:
                # Try to decrypt
                encryption.decrypt_content(encrypted_content)
                logger.debug("File decryption OK", file_id=file_id, file_name=file_name)
            except Exception as e:
                logger.error("File decryption FAILED", 
                           file_id=file_id, 
                           file_name=file_name, 
                           error=str(e))
                failed_files.append((file_id, file_name))
        
        if failed_files:
            logger.warning("Found files that cannot be decrypted", 
                         failed_count=len(failed_files),
                         total_count=len(files))
            return False, failed_files
        else:
            logger.info("All files can be decrypted successfully", 
                       total_count=len(files))
            return True, []
            
    except Exception as e:
        logger.error("Failed to check file decryption health", error=str(e))
        return False, []
    finally:
        if 'conn' in locals():
            conn.close()

def mark_corrupted_files_for_reupload():
    """Mark files that cannot be decrypted as requiring re-upload"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all encrypted files
        cursor.execute("SELECT id, file_name, encrypted_content FROM user_files")
        files = cursor.fetchall()
        
        encryption = FileEncryption()
        corrupted_files = []
        
        for file_id, file_name, encrypted_content in files:
            try:
                # Try to decrypt
                encryption.decrypt_content(encrypted_content)
            except Exception:
                # Mark as corrupted by adding a flag to metadata
                cursor.execute("""
                    UPDATE user_files 
                    SET metadata = json_set(COALESCE(metadata, '{}'), '$.corrupted', 'true')
                    WHERE id = ?
                """, (file_id,))
                corrupted_files.append((file_id, file_name))
                logger.warning("Marked file as corrupted", 
                             file_id=file_id, 
                             file_name=file_name)
        
        conn.commit()
        
        if corrupted_files:
            logger.warning("Marked corrupted files for re-upload", 
                         corrupted_count=len(corrupted_files))
        
        return corrupted_files
        
    except Exception as e:
        logger.error("Failed to mark corrupted files", error=str(e))
        return []
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Run health check
    healthy, failed_files = check_file_decryption_health()
    
    if not healthy:
        print(f"Warning: {len(failed_files)} files cannot be decrypted with current key")
        print("Failed files:")
        for file_id, file_name in failed_files:
            print(f"  - {file_name} (ID: {file_id})")
        
        # Option to mark them as corrupted
        response = input("Mark these files as corrupted for re-upload? (y/N): ")
        if response.lower() == 'y':
            corrupted = mark_corrupted_files_for_reupload()
            print(f"Marked {len(corrupted)} files as corrupted")
    else:
        print("All files can be decrypted successfully")
