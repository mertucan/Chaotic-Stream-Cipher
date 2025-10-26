from flask import Flask, render_template, request, jsonify
import base64
import binascii
import os
import random
import string
from cipher import process_text, generate_initial_conditions

app = Flask(__name__)

def byte_to_printable(byte_val: int) -> str:
    """Converts a byte value to a printable character or a placeholder."""
    if 32 <= byte_val <= 126:
        return chr(byte_val)
    return '.'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-seed')
def generate_seed():
    seed = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    return jsonify({'seed': seed})

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    text = data.get('text')
    seed = data.get('seed')
    operation = data.get('operation')

    if not text or not seed:
        return jsonify({'error': 'Please provide both text and a seed.'}), 400

    steps = []
    try:
        x0, r = generate_initial_conditions(seed)
        steps.append(f'1. Initial Conditions Derived: Seed "{seed}" produced <em>x<sub>0</sub></em> = {x0:.15f} and <em>&lambda;</em> = {r:.15f}.')

        table_headers = {}
        char_details = []

        if operation == 'encrypt':
            text_bytes = text.encode('utf-8')
            steps.append(f'2. Text to Bytes: Plaintext converted to {len(text_bytes)} UTF-8 bytes (e.g., {text_bytes[:8].hex(" ")}...).')
            
            result_bytes, _, _, keystream = process_text(text_bytes, seed)
            
            steps.append(f'3. Keystream Generated: A {len(keystream)}-byte keystream was produced from the initial parameters (e.g., {keystream[:8].hex(" ")}...).')
            
            if text_bytes:
                example_result = text_bytes[0] ^ keystream[0]
                steps.append(f'4. XOR Operation: Each text byte is XORed with a keystream byte. (e.g., first byte: {text_bytes[0]:#04x} &oplus; {keystream[0]:#04x} = {example_result:#04x}).')

            result = base64.b64encode(result_bytes).decode('utf-8')
            steps.append(f'5. Base64 Encoding: The binary encrypted data is encoded into a Base64 string for safe transport.')

            table_headers = {
                'char': 'Original Char', 'original_byte': 'Original Byte',
                'keystream_byte': 'Keystream Byte', 'result_byte': 'Encrypted Byte'
            }
            byte_cursor = 0
            for char in text:
                char_bytes = char.encode('utf-8')
                for i, byte in enumerate(char_bytes):
                    display_char = char if i == 0 else '..'
                    original_byte_val = byte
                    keystream_byte_val = keystream[byte_cursor]
                    result_byte_val = result_bytes[byte_cursor]
                    
                    char_details.append({
                        'char': display_char,
                        'original_byte': {'hex': f'{original_byte_val:#04x}', 'char': byte_to_printable(original_byte_val)},
                        'keystream_byte': {'hex': f'{keystream_byte_val:#04x}', 'char': byte_to_printable(keystream_byte_val)},
                        'result_byte': {'hex': f'{result_byte_val:#04x}', 'char': byte_to_printable(result_byte_val)}
                    })
                    byte_cursor += 1

        elif operation == 'decrypt':
            try:
                text_bytes = base64.b64decode(text)
                steps.append(f'2. Base64 Decoding: Ciphertext decoded from Base64 into {len(text_bytes)} bytes (e.g., {text_bytes[:8].hex(" ")}...).')
            except (binascii.Error, ValueError):
                return jsonify({'error': 'Invalid Base64 input. Please provide a valid encrypted text.'}), 400
            
            result_bytes, _, _, keystream = process_text(text_bytes, seed)
            steps.append(f'3. Keystream Generated: The exact same {len(keystream)}-byte keystream was reproduced from the seed (e.g., {keystream[:8].hex(" ")}...).')

            if text_bytes:
                example_result = text_bytes[0] ^ keystream[0]
                steps.append(f'4. XOR Operation: Each ciphertext byte is XORed with the keystream byte to reverse the encryption. (e.g., first byte: {text_bytes[0]:#04x} &oplus; {keystream[0]:#04x} = {example_result:#04x}).')

            try:
                result = result_bytes.decode('utf-8')
                steps.append(f'5. Bytes to Text: The resulting bytes are decoded back to a UTF-8 string, revealing the original plaintext.')
                
                table_headers = {
                    'char': 'Decrypted Char', 'original_byte': 'Encrypted Byte',
                    'keystream_byte': 'Keystream Byte', 'result_byte': 'Decrypted Byte'
                }
                
                byte_cursor = 0
                for char in result:
                    char_decrypted_bytes = char.encode('utf-8')
                    for i, byte in enumerate(char_decrypted_bytes):
                        display_char = char if i == 0 else '..'
                        encrypted_byte_val = text_bytes[byte_cursor]
                        keystream_byte_val = keystream[byte_cursor]
                        decrypted_byte_val = byte

                        char_details.append({
                            'char': display_char,
                            'original_byte': {'hex': f'{encrypted_byte_val:#04x}', 'char': byte_to_printable(encrypted_byte_val)},
                            'keystream_byte': {'hex': f'{keystream_byte_val:#04x}', 'char': byte_to_printable(keystream_byte_val)},
                            'result_byte': {'hex': f'{decrypted_byte_val:#04x}', 'char': byte_to_printable(decrypted_byte_val)}
                        })
                        byte_cursor += 1

            except UnicodeDecodeError:
                return jsonify({'error': 'Failed to decode the decrypted text. The seed may be incorrect or the original text was not valid UTF-8.'}), 400
        else:
            return jsonify({'error': 'Invalid operation specified.'}), 400

        return jsonify({'result': result, 'steps': steps, 'char_details': char_details, 'table_headers': table_headers})

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
