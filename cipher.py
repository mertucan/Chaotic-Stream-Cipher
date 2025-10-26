import hashlib

def generate_initial_conditions(seed: str):
    """
    Generates initial parameters (x0, r) for the logistic map from a seed string.
    """
    hash_object = hashlib.sha256(seed.encode())
    hex_dig = hash_object.hexdigest()
    
    x0_seed = int(hex_dig[:8], 16)
    r_seed = int(hex_dig[8:16], 16)

    x0 = (x0_seed / 0xFFFFFFFF) * 0.99 + 0.005 
    
    r = 3.9 + (r_seed / 0xFFFFFFFF) * 0.0999

    if x0 in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x0 += 0.000000001
        
    return x0, r

def generate_keystream(x0: float, r: float, length: int):
    """
    Generates a keystream of a given length using the logistic map.
    """
    keystream = []
    x = x0
    
    for _ in range(100):
        x = r * x * (1 - x)

    for _ in range(length):
        x = r * x * (1 - x)
        key_byte = int((x * (10**15))) % 256
        keystream.append(key_byte)
        
    return bytes(keystream)

def process_text(text_bytes: bytes, seed: str):
    """
    Encrypts or decrypts a byte string using the chaotic stream cipher.
    """
    x0, r = generate_initial_conditions(seed)
    keystream = generate_keystream(x0, r, len(text_bytes))
    
    processed_bytes = bytes([b ^ k for b, k in zip(text_bytes, keystream)])
    
    return processed_bytes, x0, r, keystream
