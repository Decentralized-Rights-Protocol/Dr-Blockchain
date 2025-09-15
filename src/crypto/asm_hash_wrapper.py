# === Assembly Hash Wrapper for Python ===
# Links assembly code with Python using ctypes

import ctypes
import ctypes.util
import os
import platform

class AssemblyHasher:
    def __init__(self):
        self.lib = None
        self.load_library()
    
    def load_library(self):
        """Load the compiled assembly library"""
        try:
            # Try to load the compiled library
            if platform.system() == "Darwin":  # macOS
                lib_path = "./libhash.dylib"
            elif platform.system() == "Linux":
                lib_path = "./libhash.so"
            elif platform.system() == "Windows":
                lib_path = "./hash.dll"
            else:
                raise OSError("Unsupported platform")
            
            if os.path.exists(lib_path):
                self.lib = ctypes.CDLL(lib_path)
                self.setup_function_signatures()
            else:
                print(f"Warning: Assembly library not found at {lib_path}")
                print("Using Python fallback implementation")
                self.lib = None
                
        except Exception as e:
            print(f"Error loading assembly library: {e}")
            print("Using Python fallback implementation")
            self.lib = None
    
    def setup_function_signatures(self):
        """Setup function signatures for the assembly functions"""
        if self.lib:
            # sha256_hash(input_ptr, input_len, output_ptr)
            self.lib.sha256_hash.argtypes = [
                ctypes.c_char_p,  # input pointer
                ctypes.c_size_t,  # input length
                ctypes.c_char_p   # output pointer
            ]
            self.lib.sha256_hash.restype = None
            
            # sha256_init()
            self.lib.sha256_init.argtypes = []
            self.lib.sha256_init.restype = None
    
    def hash_data(self, data):
        """Hash data using assembly or Python fallback"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if self.lib:
            # Use assembly implementation
            return self._hash_asm(data)
        else:
            # Use Python fallback
            return self._hash_python(data)
    
    def _hash_asm(self, data):
        """Hash using assembly code"""
        input_ptr = ctypes.c_char_p(data)
        input_len = len(data)
        output_buffer = ctypes.create_string_buffer(32)  # 32 bytes for SHA-256
        
        self.lib.sha256_hash(input_ptr, input_len, output_buffer)
        
        return output_buffer.raw
    
    def _hash_python(self, data):
        """Python fallback implementation"""
        import hashlib
        return hashlib.sha256(data).digest()

# === Integration with existing blockchain code ===
def integrate_with_blockchain():
    """Example of how to integrate assembly hashing with blockchain"""
    hasher = AssemblyHasher()
    
    # Test the hasher
    test_data = b"Hello, Blockchain!"
    hash_result = hasher.hash_data(test_data)
    print(f"Hash result: {hash_result.hex()}")
    
    return hasher

# === Usage in blockchain.py ===
def create_enhanced_blockchain():
    """Create blockchain with assembly-accelerated hashing"""
    hasher = AssemblyHasher()
    
    class EnhancedBlock:
        def __init__(self, index, previous_hash, timestamp, data, nonce=0):
            self.index = index
            self.previous_hash = previous_hash
            self.timestamp = timestamp
            self.data = data
            self.nonce = nonce
            self.hash = self.calculate_hash(hasher)
        
        def calculate_hash(self, hasher):
            import json
            block_string = json.dumps({
                "index": self.index,
                "previous_hash": self.previous_hash,
                "timestamp": self.timestamp,
                "data": self.data,
                "nonce": self.nonce
            }, sort_keys=True).encode()
            
            return hasher.hash_data(block_string).hex()
    
    return EnhancedBlock

if __name__ == "__main__":
    # Test the assembly integration
    hasher = integrate_with_blockchain()
    
    # Test with blockchain data
    EnhancedBlock = create_enhanced_blockchain()
    block = EnhancedBlock(1, "0", 1234567890, {"test": "data"})
    print(f"Block hash: {block.hash}")
