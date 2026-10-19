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

def load_abi(filename):
    data = load_json(filename)
    return data["abi"] if isinstance(data, dict) else data

addresses = load_json("contracts.json")
escrow_abi = load_abi("Escrow.json")
factory_abi = load_abi("EscrowFactory.json")
arbitrator_abi = load_abi("Arbitrator.json")
factory_contract = w3.eth.contract(
    address=Web3.to_checksum_address(addresses["EscrowFactory"]),
    abi=factory_abi,
)
arbitrator_contract = w3.eth.contract(
    address=Web3.to_checksum_address(addresses["Arbitrator"]),
    abi=arbitrator_abi,
)
escrow_contract = None
selected_escrow_address = None

# Tkinter Window
root = tk.Tk()
root.title("Escrow Service | Hardhat Blockchain")
root.geometry("900x760")
root.minsize(760, 650)

style = ttk.Style(root)
style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
style.configure("Action.TButton", padding=7)
main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)

ttk.Label(main, text="Escrow Service", style="Title.TLabel").pack(anchor="w")
ttk.Label(main, text="Create and manage multiple escrow deals on the local blockchain",).pack(anchor="w", pady=(0, 10))

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
        f"Connected to {RPC_URL}" if connected
        else f"Not connected to {RPC_URL}"
    )
    return connected
def send_transaction(account, function, value=0, refresh=True):
    if not check_connection():
        raise RuntimeError("Start the local Hardhat node first.")
    tx = function.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "gas": 2_000_000,
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
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] != 1:
        raise RuntimeError(f"Transaction reverted.\nHash: {tx_hash.hex()}")
    if refresh:
        refresh_escrows()
        fetch_info()
    messagebox.showinfo(
        "Success",
        f"Transaction confirmed.\nBlock: {receipt['blockNumber']}\n"
        f"Hash: {tx_hash.hex()}",
    )
    return receipt

def execute_transaction(function, value=0, refresh=True):
    account = get_account()
    if account is None:
        return
    try:
        send_transaction(account, function, value, refresh)
    except Exception as exc:
        messagebox.showerror("Transaction failed", str(exc))

def get_amount_wei():
    try:
        value = w3.to_wei(amount_var.get().strip(), "ether")
        if value <= 0:
            raise ValueError("Amount must be greater than zero.")
        return value
    except Exception:
        messagebox.showerror("Invalid amount","Enter a valid positive Ether amount, for example 0.5.")
        return None


def get_selected_escrow():
    global escrow_contract, selected_escrow_address
    value = escrow_var.get().strip()
    if not value:
        return None
    try:
        selected_escrow_address = Web3.to_checksum_address(value)
        escrow_contract = w3.eth.contract(
            address=selected_escrow_address,
            abi=escrow_abi
        )
        return escrow_contract

    except Exception as exc:
        messagebox.showerror("Invalid deal", str(exc))
        return None

def refresh_escrows():
    if not check_connection():
        return
    try:
        old_selection = escrow_var.get().strip()
        escrows = factory_contract.functions.getAllEscrows().call()
        escrows = [
            Web3.to_checksum_address(address)
            for address in escrows
        ]
        escrow_combo["values"] = escrows
        if old_selection in escrows:
            escrow_var.set(old_selection)
        elif escrows:
            escrow_var.set(escrows[-1])
        else:
            escrow_var.set("")

        if escrow_var.get():
            get_selected_escrow()
            fetch_info()
        else:
            global escrow_contract, selected_escrow_address
            escrow_contract = None
            selected_escrow_address = None
        deal_list_var.set(
            "\n".join(
                f"{index}: {address}"
                for index, address in enumerate(escrows)
            ) if escrows else "No deals created yet."
        )
    except Exception as exc:
        messagebox.showerror("Read error", str(exc))


def create_deal():
    seller = seller_var.get().strip()
    try:
        seller = Web3.to_checksum_address(seller)
        if seller == "0x0000000000000000000000000000000000000000":
            raise ValueError("Seller address cannot be the zero address.")
    except Exception:
        messagebox.showerror("Invalid seller", "Enter a valid seller address.")
        return

    account = get_account()
    if account is None:
        return
    if seller.lower() == account.address.lower():
        messagebox.showerror("Invalid seller", "Buyer and seller must be different.")
        return
    try:
        function = factory_contract.functions.createEscrow(seller)
        receipt = send_transaction(account, function, refresh=False)
        created_address = None
        for log in receipt["logs"]:
            try:
                event = factory_contract.events.EscrowCreated().process_log(log)
                created_address = Web3.to_checksum_address(
                    event["args"]["escrowAddress"]
                )
                break
            except Exception:
                continue
        if created_address is None:
            escrows = factory_contract.functions.getAllEscrows().call()
            if not escrows:
                raise RuntimeError("Transaction succeeded, but no escrow was found.")
            created_address = Web3.to_checksum_address(escrows[-1])

        refresh_escrows()
        escrow_var.set(created_address)
        get_selected_escrow()
        fetch_info()
        messagebox.showinfo("Deal created", f"New escrow deal:\n{created_address}")
    except Exception as exc:
        messagebox.showerror("Create deal failed", str(exc))

def fetch_info():
    if not check_connection():
        return
    contract = get_selected_escrow()
    if contract is None:
        info_var.set("Select a deal or create a new one.")
        return
    try:
        buyer, seller, arbitrator, amount, state = contract.functions.getDetails().call()
        state_name = STATES[state] if 0 <= state < len(STATES) else str(state)
        info_var.set(
            f"Buyer:       {buyer}\n"
            f"Seller:      {seller}\n"
            f"Arbitrator:  {arbitrator}\n"
            f"Escrow:      {contract.address}\n"
            f"Amount:      {w3.from_wei(amount, 'ether')} ETH\n"
            f"State:       {state_name}\n"
            f"Balance:     "
            f"{w3.from_wei(w3.eth.get_balance(contract.address), 'ether')} ETH"
        )
    except Exception as exc:
        info_var.set("Could not load deal details.")
        messagebox.showerror("Read error", str(exc))

def deposit():
    contract = get_selected_escrow()
    if contract is None:
        return
    value = get_amount_wei()
    if value is None:
        return
    execute_transaction(contract.functions.deposit(), value=value)

def confirm_delivery():
    contract = get_selected_escrow()
    if contract is None:
        return
    if messagebox.askyesno(
        "Confirm delivery",
        "Confirm that the goods or service were received?\n"
        "The escrow will pay the seller.",
    ):
        execute_transaction(contract.functions.confirmDelivery())
def raise_dispute():
    contract = get_selected_escrow()
    if contract is None:
        return
    if messagebox.askyesno("Raise dispute", "Raise a dispute about this deal?"):
        execute_transaction(contract.functions.raiseDispute())

def cancel_deal():
    contract = get_selected_escrow()
    if contract is None:
        return
    if messagebox.askyesno("Cancel deal", "Cancel this deal before payment?"):
        execute_transaction(contract.functions.cancel())

def resolve_dispute():
    contract = get_selected_escrow()
    if contract is None:
        return
    refund_buyer = refund_var.get()
    decision = "Refund the buyer" if refund_buyer else "Release funds to the seller"
    if not messagebox.askyesno("Resolve dispute", f"Arbitrator decision: {decision}?\n\nThis action transfers the escrow funds."):
        return
    execute_transaction(
        arbitrator_contract.functions.resolve(contract.address, refund_buyer)
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

#Deal creation and selection
ttk.Label(deal_tab, text="Create a new deal", style="Section.TLabel").pack(anchor="w")
create_frame = ttk.Frame(deal_tab)
create_frame.pack(fill="x", pady=(8, 12))
ttk.Label(create_frame, text="Seller address:").grid(row=0, column=0, sticky="w")
seller_var = tk.StringVar()
ttk.Entry(create_frame, textvariable=seller_var).grid(
    row=0, column=1, sticky="ew", padx=8
)
ttk.Button(
    create_frame, text="Create new deal", command=create_deal, style="Action.TButton"
).grid(row=0, column=2, sticky="ew")
create_frame.columnconfigure(1, weight=1)

ttk.Label(deal_tab, text="Select existing deal", style="Section.TLabel").pack(anchor="w")
select_frame = ttk.Frame(deal_tab)
select_frame.pack(fill="x", pady=(8, 12))
escrow_var = tk.StringVar()
escrow_combo = ttk.Combobox(
    select_frame, textvariable=escrow_var, state="readonly", width=70
)
escrow_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))
escrow_combo.bind("<<ComboboxSelected>>", lambda event: fetch_info())
ttk.Button(select_frame, text="Refresh list", command=refresh_escrows).pack(side="left")

ttk.Label(deal_tab, text="Buyer operations", style="Section.TLabel").pack(
    anchor="w", pady=(0, 8)
)
amount_var = tk.StringVar(value="1.0")
amount_frame = ttk.Frame(deal_tab)
amount_frame.pack(fill="x", pady=(0, 10))
ttk.Label(amount_frame, text="Deposit amount (ETH):").pack(side="left")
ttk.Entry(amount_frame, textvariable=amount_var, width=20).pack(side="left", padx=10)

ttk.Button(
    deal_tab, text="1. Deposit Ether", style="Action.TButton", command=deposit
).pack(fill="x", pady=4)
ttk.Button(
    deal_tab, text="2. Confirm delivery and pay seller",
    style="Action.TButton", command=confirm_delivery
).pack(fill="x", pady=4)
ttk.Button(
    deal_tab, text="3. Raise a dispute", style="Action.TButton", command=raise_dispute
).pack(fill="x", pady=4)
ttk.Button(
    deal_tab, text="4. Cancel unpaid deal", style="Action.TButton", command=cancel_deal
).pack(fill="x", pady=4)

ttk.Label(status_tab, text="Selected deal details", style="Section.TLabel").pack(
    anchor="w", pady=(0, 8)
)
info_var = tk.StringVar(value="Create or select a deal, then refresh.")
ttk.Label(
    status_tab, textvariable=info_var, justify="left",
    font=("Consolas", 10), wraplength=780,
).pack(anchor="w", fill="x", pady=(0, 15))
ttk.Button(status_tab, text="Refresh contract status", command=fetch_info).pack(anchor="w")
ttk.Label(status_tab, text="All deals", style="Section.TLabel").pack(
    anchor="w", pady=(18, 8)
)
deal_list_var = tk.StringVar(value="No deals loaded.")
ttk.Label(
    status_tab, textvariable=deal_list_var, justify="left",
    font=("Consolas", 9), wraplength=780,
).pack(anchor="w", fill="x")

ttk.Label(
    arbitration_tab, text="Arbitrator operations", style="Section.TLabel"
).pack(anchor="w", pady=(0, 10))
ttk.Label(
    arbitration_tab,
    text=(
        "Only the owner of the Arbitrator contract can resolve a dispute. "
        "Select the disputed escrow above in the Deal tab first. "
        "The selected escrow must be in the Disputed state."
    ),
    wraplength=780,
).pack(anchor="w", pady=(0, 12))
refund_var = tk.BooleanVar(value=True)
ttk.Radiobutton(
    arbitration_tab, text="Refund the buyer",
    variable=refund_var, value=True,
).pack(anchor="w", pady=5)
ttk.Radiobutton(
    arbitration_tab, text="Release funds to the seller",
    variable=refund_var, value=False,
).pack(anchor="w", pady=5)
ttk.Button(
    arbitration_tab, text="Resolve dispute",
    style="Action.TButton", command=resolve_dispute,
).pack(fill="x", pady=(15, 5))

check_connection()
if w3.is_connected():
    refresh_escrows()

root.mainloop()
