from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip84, Bip84Coins
from eth_account import Account

# 生成24个单词的助记词
mnemo = Mnemonic("english")
words = mnemo.generate(strength=256)  # 生成24个单词的助记词
print(f"助记词: {words}")

# 生成种子
seed = Bip39SeedGenerator(words).Generate()
print(f"种子: {seed.hex()}")

print("-" * 60)

# 生成比特币 BIP84 地址
bip84_ctx = Bip84.FromSeed(seed, Bip84Coins.BITCOIN)
bip84_acc = bip84_ctx.Purpose().Coin().Account(0).Change(False).AddressIndex(0)
btc_private_key = bip84_acc.PrivateKey().Raw().ToHex()
btc_public_key = bip84_acc.PublicKey().RawCompressed().ToHex()
btc_address = bip84_acc.PublicKey().ToAddress()
print(f"比特币 BIP84 私钥: {btc_private_key}")
print(f"比特币 BIP84 公钥: {btc_public_key}")
print(f"比特币 BIP84 地址: {btc_address}")

print("-" * 60)

# 生成以太坊地址
bip44_eth_ctx = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
bip44_eth_acc = bip44_eth_ctx.Purpose().Coin().Account(0).Change(False).AddressIndex(0)
eth_private_key = bip44_eth_acc.PrivateKey().Raw().ToHex()
eth_public_key = bip44_eth_acc.PublicKey().RawCompressed().ToHex()
eth_account = Account.from_key(eth_private_key)
eth_address = eth_account.address
print(f"以太坊私钥: {eth_private_key}")
print(f"以太坊公钥: {eth_public_key}")
print(f"以太坊地址: {eth_address}")

print("-" * 60)

# 生成 Zcash 地址
bip44_zcash_ctx = Bip44.FromSeed(seed, Bip44Coins.ZCASH)
bip44_zcash_acc = bip44_zcash_ctx.Purpose().Coin().Account(0).Change(False).AddressIndex(0)
zcash_private_key = bip44_zcash_acc.PrivateKey().Raw().ToHex()
zcash_public_key = bip44_zcash_acc.PublicKey().RawCompressed().ToHex()
zcash_address = bip44_zcash_acc.PublicKey().ToAddress()
print(f"Zcash 私钥: {zcash_private_key}")
print(f"Zcash 公钥: {zcash_public_key}")
print(f"Zcash 地址: {zcash_address}")

print("-" * 60)

# 生成达世币 (Dash) 地址
bip44_dash_ctx = Bip44.FromSeed(seed, Bip44Coins.DASH)
bip44_dash_acc = bip44_dash_ctx.Purpose().Coin().Account(0).Change(False).AddressIndex(0)
dash_private_key = bip44_dash_acc.PrivateKey().Raw().ToHex()
dash_public_key = bip44_dash_acc.PublicKey().RawCompressed().ToHex()
dash_address = bip44_dash_acc.PublicKey().ToAddress()
print(f"达世币私钥: {dash_private_key}")
print(f"达世币公钥: {dash_public_key}")
print(f"达世币地址: {dash_address}")

print("-" * 60)

# 生成比特币黄金 (Bitcoin Gold) 地址
bip44_btg_ctx = Bip44.FromSeed(seed, Bip44Coins.BITCOIN_GOLD)
bip44_btg_acc = bip44_btg_ctx.Purpose().Coin().Account(0).Change(False).AddressIndex(0)
btg_private_key = bip44_btg_acc.PrivateKey().Raw().ToHex()
btg_public_key = bip44_btg_acc.PublicKey().RawCompressed().ToHex()
btg_address = bip44_btg_acc.PublicKey().ToAddress()
print(f"比特币黄金私钥: {btg_private_key}")
print(f"比特币黄金公钥: {btg_public_key}")
print(f"比特币黄金地址: {btg_address}")

print("-" * 60)
