import json
import os
import hashlib
import base64
import hmac
import secrets

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSWORDS_FILE = os.path.join(_PROJECT_ROOT, "passwords.json")


class PasswordCrypto:
    """简单的密码加密/解密工具（基于主密码派生密钥 + XOR）"""

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """从主密码派生加密密钥"""
        return hashlib.pbkdf2_hmac(
            "sha256", master_password.encode("utf-8"), salt, 100000
        )

    @staticmethod
    def encrypt(plaintext: str, master_password: str) -> dict:
        """加密明文密码，返回 {"salt": ..., "data": ..., "tag": ...}"""
        salt = secrets.token_bytes(16)
        key = PasswordCrypto.derive_key(master_password, salt)
        # XOR 加密
        data_bytes = plaintext.encode("utf-8")
        # 扩展 key 到匹配长度
        extended_key = (key * ((len(data_bytes) // len(key)) + 1))[: len(data_bytes)]
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, extended_key))
        # HMAC 完整性标签
        tag = hmac.new(key, encrypted, hashlib.sha256).hexdigest()
        return {
            "salt": base64.b64encode(salt).decode("ascii"),
            "data": base64.b64encode(encrypted).decode("ascii"),
            "tag": tag,
        }

    @staticmethod
    def decrypt(encrypted_obj: dict, master_password: str) -> str | None:
        """解密密码，失败返回 None（主密码错误或数据损坏）"""
        try:
            salt = base64.b64decode(encrypted_obj["salt"])
            data = base64.b64decode(encrypted_obj["data"])
            tag = encrypted_obj["tag"]
            key = PasswordCrypto.derive_key(master_password, salt)
            # 验证 HMAC
            expected_tag = hmac.new(key, data, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(tag, expected_tag):
                return None  # 主密码错误或数据被篡改
            # XOR 解密
            extended_key = (key * ((len(data) // len(key)) + 1))[: len(data)]
            decrypted = bytes(a ^ b for a, b in zip(data, extended_key))
            return decrypted.decode("utf-8")
        except (KeyError, ValueError, UnicodeDecodeError):
            return None

    @staticmethod
    def hash_master_password(master_password: str, salt: bytes = None) -> dict:
        """对主密码进行哈希，用于验证主密码是否正确"""
        if salt is None:
            salt = secrets.token_bytes(16)
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256", master_password.encode("utf-8"), salt, 100000
        )
        return {
            "salt": base64.b64encode(salt).decode("ascii"),
            "hash": base64.b64encode(pw_hash).decode("ascii"),
        }

    @staticmethod
    def verify_master_password(master_password: str, stored: dict) -> bool:
        """验证主密码是否与存储的哈希匹配"""
        try:
            salt = base64.b64decode(stored["salt"])
            expected_hash = base64.b64decode(stored["hash"])
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256", master_password.encode("utf-8"), salt, 100000
            )
            return hmac.compare_digest(actual_hash, expected_hash)
        except (KeyError, ValueError):
            return False


class PasswordManager:
    """密码管理器：保存、加载、删除网站密码，带主密码保护"""

    @staticmethod
    def load_data() -> dict:
        """
        加载密码数据文件。
        格式:
        {
            "master_password_hash": {"salt": "...", "hash": "..."},
            "entries": [
                {
                    "url": "https://example.com",
                    "username": "user@example.com",
                    "password_encrypted": {"salt": "...", "data": "...", "tag": "..."},
                    "created_at": "2026-..."
                }, ...
            ]
        }
        """
        if not os.path.exists(PASSWORDS_FILE):
            return {"master_password_hash": None, "entries": []}
        try:
            with open(PASSWORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"master_password_hash": None, "entries": []}

    @staticmethod
    def save_data(data: dict):
        """保存密码数据到文件"""
        try:
            with open(PASSWORDS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print("Password save error:", e)

    @staticmethod
    def is_master_password_set() -> bool:
        """检查是否已设置主密码"""
        data = PasswordManager.load_data()
        return data.get("master_password_hash") is not None

    @staticmethod
    def set_master_password(master_password: str):
        """设置主密码（首次使用）"""
        data = PasswordManager.load_data()
        data["master_password_hash"] = PasswordCrypto.hash_master_password(
            master_password
        )
        PasswordManager.save_data(data)

    @staticmethod
    def verify_master_password(master_password: str) -> bool:
        """验证主密码"""
        data = PasswordManager.load_data()
        stored = data.get("master_password_hash")
        if stored is None:
            return False
        return PasswordCrypto.verify_master_password(master_password, stored)

    @staticmethod
    def save_password(url: str, username: str, password: str, master_password: str):
        """保存一个网站的密码（使用主密码加密）"""
        import datetime

        data = PasswordManager.load_data()
        entries = data.get("entries", [])
        # 检查是否已有该网站+用户名的记录，有则更新
        encrypted = PasswordCrypto.encrypt(password, master_password)
        for entry in entries:
            if entry["url"] == url and entry["username"] == username:
                entry["password_encrypted"] = encrypted
                entry["updated_at"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                PasswordManager.save_data(data)
                return
        # 新增
        entries.append(
            {
                "url": url,
                "username": username,
                "password_encrypted": encrypted,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        data["entries"] = entries
        PasswordManager.save_data(data)

    @staticmethod
    def get_passwords_for_url(url: str, master_password: str) -> list:
        """获取某个 URL 的所有保存密码（解密后返回）"""
        from urllib.parse import urlparse

        data = PasswordManager.load_data()
        entries = data.get("entries", [])
        # 用域名匹配
        try:
            target_domain = urlparse(url).netloc.lower()
        except Exception:
            target_domain = url.lower()
        results = []
        for entry in entries:
            try:
                entry_domain = urlparse(entry["url"]).netloc.lower()
            except Exception:
                entry_domain = entry["url"].lower()
            if entry_domain == target_domain:
                decrypted = PasswordCrypto.decrypt(
                    entry["password_encrypted"], master_password
                )
                if decrypted is not None:
                    results.append(
                        {
                            "url": entry["url"],
                            "username": entry["username"],
                            "password": decrypted,
                        }
                    )
        return results

    @staticmethod
    def get_all_entries() -> list:
        """获取所有条目（不含解密密码，只有元数据）"""
        data = PasswordManager.load_data()
        entries = data.get("entries", [])
        return [
            {
                "url": e.get("url", ""),
                "username": e.get("username", ""),
                "created_at": e.get("created_at", ""),
            }
            for e in entries
        ]

    @staticmethod
    def delete_password(url: str, username: str):
        """删除一个保存的密码"""
        data = PasswordManager.load_data()
        entries = data.get("entries", [])
        data["entries"] = [
            e for e in entries if not (e["url"] == url and e["username"] == username)
        ]
        PasswordManager.save_data(data)

    @staticmethod
    def delete_all():
        """删除所有保存的密码（保留主密码哈希）"""
        data = PasswordManager.load_data()
        data["entries"] = []
        PasswordManager.save_data(data)
