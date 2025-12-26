import base64

from Crypto.Cipher import AES
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from loguru import logger

from config.base_config import AES_IV, AES_KEY


class AESCipher:

    def __init__(
            self,
            key: str = base64.decodebytes(AES_KEY.encode('utf8')).decode(),
            iv: str = base64.decodebytes(AES_IV.encode('utf8')).decode(),
    ):
        """
        :param key: 加密解密密钥
        :param iv:  偏移量
        """
        self.key = key
        self.iv = iv
        backend = default_backend()
        self.cipher = Cipher(algorithms.AES(key.encode('utf8')), modes.GCM(iv.encode('utf8')), backend=backend)
        self.aes_cipher = AES.new(key.encode('utf8'), AES.MODE_GCM, iv.encode('utf8'))

    def aes_encoding(
            self,
            text
    ):
        try:
            ciphertext, auth_tag = self.aes_cipher.encrypt_and_digest(text.encode('utf8'))
            result = ciphertext + auth_tag
            return base64.b64encode(result).decode('utf-8')
        except Exception as err:
            logger.error("###加密异常, Message={}", err)
            return text

    def aes_decoding(
            self,
            ciphertext
    ):
        try:
            res_bytes = base64.b64decode(ciphertext.encode('utf-8'))
            ciphertext = res_bytes[:-16]
            auth_tag = res_bytes[-16:]
            return self.aes_cipher.decrypt_and_verify(ciphertext, auth_tag).decode('utf-8')
        except Exception as err:
            logger.error("###解密异常, Message={}", err)
            return ciphertext
