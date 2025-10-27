import hashlib
from typing import Tuple

def generate_initial_conditions(seed: str) -> Tuple[float, float]:
    """
    Generates initial parameters (x0, r) for the logistic map from a seed string.

    The seed is hashed using SHA-256 to produce a deterministic set of parameters.
    - x0 (initial value) is mapped to the interval (0, 1), avoiding fixed points.
    - r (control parameter) is mapped to the chaotic region [3.9, 3.9999].

    Args:
        seed: The input string used to generate the parameters.

    Returns:
        A tuple containing the initial value x0 and the control parameter r.
    """
    hash_object = hashlib.sha256(seed.encode())
    hex_dig = hash_object.hexdigest()
    
    # Use the first 8 hex characters (32 bits) for x0
    x0_seed = int(hex_dig[:8], 16)
    # Use the next 8 hex characters (32 bits) for r
    r_seed = int(hex_dig[8:16], 16)

    # Normalize x0 to be in (0, 1) and scale to [0.005, 0.995] to stay away from the boundaries
    x0 = (x0_seed / 0xFFFFFFFF) * 0.99 + 0.005 
    
    # Normalize r and scale to the chaotic range [3.9, 3.9999]
    r = 3.9 + (r_seed / 0xFFFFFFFF) * 0.0999

    # Avoid unstable fixed points of the logistic map
    if x0 in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x0 += 0.000000001
        
    return x0, r

def generate_keystream(x0: float, r: float, length: int) -> bytes:
    """
    Generates a keystream of a given length using the logistic map.

    The function first iterates the map 100 times to discard initial transient
    values, allowing the system to settle into its chaotic attractor. It then
    generates the keystream bytes.

    Args:
        x0: The initial value for the logistic map.
        r: The control parameter for the logistic map.
        length: The desired length of the keystream in bytes.

    Returns:
        A byte string representing the generated keystream.
    """
    keystream = []
    x = x0
    
    # Discard the initial 100 values to avoid transient effects.
    # This helps ensure the generator is in a chaotic state.
    for _ in range(100):
        x = r * x * (1 - x)

    # Generate the keystream bytes
    for _ in range(length):
        x = r * x * (1 - x)
        # Convert the chaotic float value to a byte.
        # Multiplying by a large number and taking modulo 256 aims to
        # use the less significant digits of x, which are more random.
        key_byte = int((x * (10**15))) % 256
        keystream.append(key_byte)
        
    return bytes(keystream)

def xor_with_keystream(data_bytes: bytes, keystream: bytes) -> bytes:
    """
    Encrypts or decrypts a byte string using a simple XOR operation with a keystream.
    
    Args:
        data_bytes: The input data (plaintext or ciphertext) as bytes.
        keystream: The keystream to XOR with the data.
        
    Returns:
        The result of the XOR operation as a byte string.
    """
    return bytes([b ^ k for b, k in zip(data_bytes, keystream)])
