from web3 import Web3
import eth_account

w3 = Web3()
#account = eth_account.Account.create()

account=Web3.to_checksum_address('0x12349840E00aD66A7E2038777d58601b9dF11D8d')
key='0x10aff6e7abe9a5b51bd776987d296b0b95db8ee82b3ec9e71ced86a89bea1045'


print(f"Address: {address}")
print(f"Private Key: {w3.to_hex(key)}")
