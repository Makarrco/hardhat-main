import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent
RPC_URL = "http://127.0.0.1:8545"

STATES = [
    "AwaitingPayment",
    "AwaitingDelivery",
    "Complete",
    "Disputed",
    "Refunded",
    "Cancelled",
]
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))
def load_json(filename):
    with open(BASE_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)
addresses = load_json("contracts.json")
def load_abi(filename):
    data = load_json(filename)
    return data["abi"] if isinstance(data, dict) else data

escrow_abi = load_abi("Escrow.json")
arbitrator_abi = load_abi("Arbitrator.json")
escrow_contract = w3.eth.contract(address=Web3.to_checksum_address(addresses["Escrow"]),abi=escrow_abi,)
arbitrator_contract = w3.eth.contract(address=Web3.to_checksum_address(addresses["Arbitrator"]), abi=arbitrator_abi,)

# Tkinter Window
root = tk.Tk()
root.title("Escrow Service | Hardhat Blockchain")
root.geometry("820x720")
root.minsize(720, 620)

style = ttk.Style(root)
style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
style.configure("Action.TButton", padding=7)

main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)

ttk.Label(
    main,
    text="Escrow Service",
    style="Title.TLabel",
).pack(anchor="w")

ttk.Label(
    main,
    text="Secure payments between buyer and seller",
).pack(anchor="w", pady=(0, 10))
# 
status_var = tk.StringVar(value="Checking blockchain connection...")
account_var = tk.StringVar(value="No account selected")
status_frame = ttk.LabelFrame(main, text="Connection", padding=10)
status_frame.pack(fill="x", pady=(0, 12))
ttk.Label(status_frame, textvariable=status_var).pack(anchor="w")
ttk.Label(status_frame, textvariable=account_var).pack(anchor="w", pady=(4, 0))
key_frame = ttk.LabelFrame(main, text="Transaction account", padding=10)
key_frame.pack(fill="x", pady=(0, 12))
ttk.Label(key_frame, text="Private key:").grid(
    row=0, column=0, sticky="w", padx=(0, 10)
)
pk_entry = ttk.Entry(key_frame, show="*", width=65)
pk_entry.grid(row=0, column=1, sticky="ew")
key_frame.columnconfigure(1, weight=1)

ttk.Label(
    key_frame,
    text="The key is used in memory only. Never share it.",
).grid(row=1, column=1, sticky="w", pady=(5, 0))

def get_account():
    pk = pk_entry.get().strip()
    if not pk:
        messagebox.showerror("Error", "Enter your private key.")
        return None
    try:
        account = w3.eth.account.from_key(pk)
        account_var.set(f"Account: {account.address}")
        return account
    except Exception:
        messagebox.showerror("Error", "Invalid private key.")
        return None


def check_connection():
    connected = w3.is_connected()
    status_var.set(
        f"Connected to {RPC_URL}"
        if connected
        else f"Not connected to {RPC_URL}"
    )
    return connected
def get_amount_wei():
    try:
        value = w3.to_wei(amount_var.get().strip(), "ether")
        if value <= 0:
            raise ValueError("Amount must be greater than zero.")
        return value
    except Exception:
        messagebox.showerror(
            "Invalid amount",
            "Enter a valid positive Ether amount, for example 0.5.",
        )
        return None

def send_transaction(account, function, value=0):
    if not check_connection():
        raise RuntimeError("Start the local Hardhat node first.")
    tx = function.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "gas": 500000,
        "value": value,
    })
    signed_tx = w3.eth.account.sign_transaction(
        tx,
        private_key=pk_entry.get().strip(),
    )

    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    messagebox.showinfo(
        "Transaction submitted",
        f"Transaction hash:\n{tx_hash.hex()}\n\nWaiting for confirmation...",
    )
    receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash,
        timeout=120,
    )
    if receipt["status"] != 1:
        raise RuntimeError(
            f"Transaction reverted.\nHash: {tx_hash.hex()}"
        )
    fetch_info()
    messagebox.showinfo(
        "Success",
        f"Transaction confirmed.\n"
        f"Block: {receipt['blockNumber']}\n"
        f"Hash: {tx_hash.hex()}",
    )

def execute_transaction(function, value=0):
    account = get_account()
    if account is None:
        return
    try:
        send_transaction(account, function, value)
    except Exception as exc:
        messagebox.showerror("Transaction failed", str(exc))
def fetch_info():
    if not check_connection():
        return
    try:
        buyer, seller, arbitrator, amount, state = (
            escrow_contract.functions.getDetails().call()
        )
        state_name = STATES[state] if 0 <= state < len(STATES) else str(state)
        info = (
            f"Buyer:       {buyer}\n"
            f"Seller:      {seller}\n"
            f"Arbitrator:  {arbitrator}\n"
            f"Escrow:      {escrow_contract.address}\n"
            f"Amount:      {w3.from_wei(amount, 'ether')} ETH\n"
            f"State:       {state_name}\n"
            f"Balance:     "
            f"{w3.from_wei(w3.eth.get_balance(escrow_contract.address), 'ether')} ETH"
        )
        info_var.set(info)
    except Exception as exc:
        messagebox.showerror("Read error", str(exc))

def deposit():
    value = get_amount_wei()
    if value is None:
        return
    execute_transaction(
        escrow_contract.functions.deposit(),
        value=value,
    )
def confirm_delivery():
    if messagebox.askyesno(
        "Confirm delivery",
        "Confirm that the goods or service were received?\n"
        "The escrow will pay the seller.",
    ):
        execute_transaction(
            escrow_contract.functions.confirmDelivery()
        )

def raise_dispute():
    if messagebox.askyesno("Raise dispute","Raise a dispute about this transaction?",):
        execute_transaction(
            escrow_contract.functions.raiseDispute()
        )


def cancel_deal():
    if messagebox.askyesno("Cancel deal", "Cancel the deal before payment?",):
        execute_transaction(
            escrow_contract.functions.cancel()
        )
def resolve_dispute():
    refund_buyer = refund_var.get()
    decision = (
        "Refund the buyer"
        if refund_buyer
        else "Release funds to the seller"
    )
    if not messagebox.askyesno(
        "Resolve dispute",
        f"Arbitrator decision: {decision}?\n\n"
        "This action transfers the escrow funds.",
    ):
        return
    execute_transaction(
        arbitrator_contract.functions.resolve(
            escrow_contract.address,
            refund_buyer,
        )
    )
# Tabs
notebook = ttk.Notebook(main)
notebook.pack(fill="both", expand=True)

deal_tab = ttk.Frame(notebook, padding=14)
status_tab = ttk.Frame(notebook, padding=14)
arbitration_tab = ttk.Frame(notebook, padding=14)

notebook.add(deal_tab, text="Deal")
notebook.add(status_tab, text="Contract status")
notebook.add(arbitration_tab, text="Arbitration")

ttk.Label(
    deal_tab,
    text="Buyer operations",
    style="Section.TLabel",
).pack(anchor="w", pady=(0, 10))

amount_var = tk.StringVar(value="1.0")
amount_frame = ttk.Frame(deal_tab)
amount_frame.pack(fill="x", pady=(0, 12))
ttk.Label(amount_frame, text="Deposit amount (ETH):").pack(side="left")

ttk.Entry(
    amount_frame,
    textvariable=amount_var,
    width=20,
).pack(side="left", padx=10)
ttk.Button(
    deal_tab,
    text="1. Deposit Ether",
    style="Action.TButton",
    command=deposit,
).pack(fill="x", pady=5)
ttk.Button(
    deal_tab,
    text="2. Confirm delivery and pay seller",
    style="Action.TButton",
    command=confirm_delivery,
).pack(fill="x", pady=5)
ttk.Button(
    deal_tab,
    text="3. Raise a dispute",
    style="Action.TButton",
    command=raise_dispute,
).pack(fill="x", pady=5)
ttk.Button(
    deal_tab,
    text="4. Cancel unpaid deal",
    style="Action.TButton",
    command=cancel_deal,
).pack(fill="x", pady=5)

ttk.Label(
    status_tab,
    text="Escrow details",
    style="Section.TLabel",
).pack(anchor="w", pady=(0, 10))
info_var = tk.StringVar(value="Click Refresh to load contract details.")
ttk.Label(
    status_tab,
    textvariable=info_var,
    justify="left",
    font=("Consolas", 10),
    wraplength=720,
).pack(anchor="w", fill="x", pady=(0, 15))
ttk.Button(
    status_tab,
    text="Refresh contract status",
    command=fetch_info,
).pack(anchor="w")

ttk.Label(
    arbitration_tab,
    text="Arbitrator operations",
    style="Section.TLabel",
).pack(anchor="w", pady=(0, 10))
ttk.Label(
    arbitration_tab,
    text=(
        "Only the owner of the Arbitrator contract can resolve a dispute. "
        "The Escrow contract must be in the Disputed state."
    ),
    wraplength=720,
).pack(anchor="w", pady=(0, 12))
refund_var = tk.BooleanVar(value=True)
ttk.Radiobutton(
    arbitration_tab,
    text="Refund the buyer",
    variable=refund_var,
    value=True,
).pack(anchor="w", pady=5)
ttk.Radiobutton(
    arbitration_tab,
    text="Release funds to the seller",
    variable=refund_var,
    value=False,
).pack(anchor="w", pady=5)
ttk.Button(
    arbitration_tab,
    text="Resolve dispute",
    style="Action.TButton",
    command=resolve_dispute,
).pack(fill="x", pady=(15, 5))

check_connection()
if w3.is_connected():
    fetch_info()
root.mainloop()
