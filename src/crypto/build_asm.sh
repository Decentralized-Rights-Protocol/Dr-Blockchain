#!/bin/bash

# Build script for assembly code integration
# This script compiles the assembly code into a shared library

echo "Building assembly hash library..."

# Check if NASM is installed
if ! command -v nasm &> /dev/null; then
    echo "Error: NASM (Netwide Assembler) is not installed"
    echo "Install NASM:"
    echo "  macOS: brew install nasm"
    echo "  Ubuntu: sudo apt-get install nasm"
    echo "  CentOS: sudo yum install nasm"
    exit 1
fi

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)

echo "Platform: $PLATFORM"
echo "Architecture: $ARCH"

# Compile assembly code
if [ "$PLATFORM" = "Darwin" ]; then
    # macOS
    echo "Compiling for macOS..."
    nasm -f macho64 hash_asm.asm -o hash_asm.o
    ld -shared -o libhash.dylib hash_asm.o
    echo "Created libhash.dylib"
    
elif [ "$PLATFORM" = "Linux" ]; then
    # Linux
    echo "Compiling for Linux..."
    nasm -f elf64 hash_asm.asm -o hash_asm.o
    ld -shared -o libhash.so hash_asm.o
    echo "Created libhash.so"
    
else
    echo "Unsupported platform: $PLATFORM"
    exit 1
fi

# Clean up object file
rm -f hash_asm.o

echo "Build complete!"
echo "You can now use the assembly library with Python:"
echo "  python3 asm_hash_wrapper.py"
