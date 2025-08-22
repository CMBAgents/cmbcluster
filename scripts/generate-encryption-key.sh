#!/bin/bash

# Generate encryption key for CMBCluster environment files
# This script helps generate a secure encryption key for production deployments

echo "🔐 Generating encryption key for CMBCluster environment files..."

# Try to use Python first (recommended)
if command -v python3 &> /dev/null; then
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Generated encryption key using Python cryptography library:"
        echo "FILE_ENCRYPTION_KEY=$KEY"
        echo ""
        echo "📝 To use this key:"
        echo "1. Add this to your .env file:"
        echo "   FILE_ENCRYPTION_KEY=$KEY"
        echo ""
        echo "2. Or set it as an environment variable before deployment:"
        echo "   export FILE_ENCRYPTION_KEY=\"$KEY\""
        echo ""
        echo "⚠️  IMPORTANT: Store this key securely! If you lose it, you won't be able"
        echo "   to decrypt existing environment files and users will need to re-upload them."
        exit 0
    fi
fi

# Fallback to OpenSSL
if command -v openssl &> /dev/null; then
    KEY=$(openssl rand -base64 32)
    echo ""
    echo "✅ Generated encryption key using OpenSSL:"
    echo "FILE_ENCRYPTION_KEY=$KEY"
    echo ""
    echo "📝 To use this key:"
    echo "1. Add this to your .env file:"
    echo "   FILE_ENCRYPTION_KEY=$KEY"
    echo ""
    echo "2. Or set it as an environment variable before deployment:"
    echo "   export FILE_ENCRYPTION_KEY=\"$KEY\""
    echo ""
    echo "⚠️  IMPORTANT: Store this key securely! If you lose it, you won't be able"
    echo "   to decrypt existing environment files and users will need to re-upload them."
    echo ""
    echo "ℹ️  Note: This key was generated with OpenSSL. For optimal compatibility,"
    echo "   consider using Python cryptography library instead."
    exit 0
fi

# No suitable tools found
echo "❌ Error: Neither Python3 with cryptography library nor OpenSSL found."
echo ""
echo "Please install one of the following:"
echo "1. Python 3 with cryptography library:"
echo "   pip install cryptography"
echo ""
echo "2. OpenSSL (usually pre-installed on most systems)"
echo ""
echo "Then run this script again."
exit 1
