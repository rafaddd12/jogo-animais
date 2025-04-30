import hashlib

senha = "brasil2018"
hash_senha = hashlib.sha256(senha.encode()).hexdigest()
print(f"Hash da senha '{senha}': {hash_senha}") 