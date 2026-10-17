import json
import tkinter as tk
from tkinter import ttk, messagebox
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
with open("contracts.json", "r") as f:
    addresses = json.load(f)
with open("Escrow.json", "r") as f:
    escrow_abi = json.load(f)["abi"]
escrow_contract = w3.eth.contract(address=addresses["Escrow"], abi=escrow_abi)

root = tk.Tk()
root.title("Escrow Service - Hardhat GUI")
root.geometry("480x520")
status_label = tk.Label(root, text=f"Connected: {w3.is_connected()}", fg="green" if w3.is_connected() else "red")
status_label.pack(pady=5)
tk.Label(root, text="Private key:").pack()
pk_entry = tk.Entry(root, show="*", width=50)
pk_entry.pack(pady=5)

tk.Label(root, text="Ether Amount:").pack()
amount_entry = tk.Entry(root, width=20)
amount_entry.insert(0, "1.0")
amount_entry.pack(pady=5)

def get_account():
    pk = pk_entry.get().strip()
    if not pk:
        messagebox.showerror("Error", "Please enter a private key!")
        return None, None
    try:
        account = w3.eth.account.from_key(pk)
        return account, pk
    except Exception as e:
        messagebox.showerror("Error", f"Invalid Private Key: {e}")
        return None, None
def send_deposit():
    account, pk = get_account()
    if not account: return
    try: 
        val_eth = float(amount_entry.get())
        tx = escrow_contract.functions.deposit().build_transaction({
            'from': account.address,
            'value': w3.to_wei(val_eth, 'ether'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        messagebox.showinfo("Success", f"Deposit Sent!\nTx Hash: {tx_hash.hex()}")
    except Exception as e:
        messagebox.showerror("Transaction Failed", str(e))
def confirm_delivery():
    account, pk = get_account()
    if not account: return

    try: 
        tx = escrow_contract.functions.confirmDelivery().build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        messagebox.showinfo("Success", f"Delivery Confirmed!\nTx Hash: {tx_hash.hex()}")
    except Exception as e:
        messagebox.showerror("Transaction Failed", str(e))
def fetch_info():
    try:
        buyer, seller, arbitrator, amount, state = escrow_contract.functions.getDetails().call()
        states = ["AwaitingPayment", "AwaitingDelivery", "Complete", "Disputed", "Refunded"]
        info = f"Buyer: {buyer}\nSeller: {seller}\nArbitrator: {arbitrator}\nAmount: {w3.from_wei(amount, 'ether')} ETH\nState: {states[state]}"
        info_label.config(text=info)
    except Exception as e:
        messagebox.showerror("Error", str(e))
tk.Button(root, text="1. Send Deposit (Buyer)", command=send_deposit, bg="#4CAF50", fg="white").pack(pady=5)
tk.Button(root, text="2. Confirm Delivery (Buyer)", command=confirm_delivery, bg="#2196F3", fg="white").pack(pady=5)
tk.Button(root, text="Refresh Contract Status", command=fetch_info).pack(pady=10)

info_label = tk.Label(root, text="", justify="left", font=("Consolas", 9))
info_label.pack(pady=10)
root.mainloop()