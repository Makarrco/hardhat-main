# Escrow DApp --- Hardhat 3 + Solidity + Python Tkinter

A local Ethereum escrow application built with Hardhat 3, Solidity,
Hardhat Ignition, Web3.py, and a Tkinter desktop interface. It
demonstrates how a buyer can place ETH into an escrow contract, confirm
delivery to pay the seller, or raise a dispute for an arbitrator to
resolve.

> **Current scope:** local development and testing on the Hardhat
> localhost network. This is a learning/demo project, not audited
> production escrow software. Do not use real funds or real wallet
> private keys.

## Contents

-   [Project idea](#project-idea)
-   [Current functionality](#current-functionality)
-   [Technology stack](#technology-stack)
-   [Architecture](#architecture)
-   [Requirements](#requirements)
-   [Project files](#project-files)
-   [Install and run](#install-and-run)
-   [Deploy the contracts](#deploy-the-contracts)
-   [Configure the Python GUI](#configure-the-python-gui)
-   [Run the GUI](#run-the-gui)
-   [Manual test plan](#manual-test-plan)
-   [Contract states and rules](#contract-states-and-rules)
-   [Troubleshooting](#troubleshooting)
-   [Planned improvements](#planned-improvements)
-   [Security notes](#security-notes)
-   [Useful Hardhat commands and
    links](#useful-hardhat-commands-and-links)

## Project idea

The project is a simple decentralized escrow service. A buyer creates a
deal and names a seller. The factory deploys an individual escrow
contract for that deal. The buyer deposits ETH into the escrow. Once the
goods or service have been delivered, the buyer can confirm delivery and
release the funds to the seller.

If the buyer and seller disagree, either party can raise a dispute. The
arbitrator then chooses one of two outcomes:

-   refund the buyer; or
-   release the escrowed funds to the seller.

A buyer can cancel a deal only before depositing, while it is still in
`AwaitingPayment`.

The desktop GUI is intended to make the contracts easier to use during
development, without requiring the user to call contract functions
manually from a console.

## Current functionality

The contracts and GUI are intended to support:

-   connecting to a local Hardhat JSON-RPC node at
    `http://127.0.0.1:8545`;
-   creating escrow deals through `EscrowFactory`;
-   listing all escrow contracts created by the factory;
-   selecting a deal and viewing its buyer, seller, arbitrator, amount,
    state, and on-chain balance;
-   depositing ETH as the buyer;
-   confirming delivery and paying the seller;
-   raising a dispute as either the buyer or seller;
-   resolving a dispute as the authorized arbitrator, either refunding
    the buyer or paying the seller;
-   cancelling an unpaid deal, if the current account is the buyer;
-   displaying transaction confirmation and errors in the GUI.

The main transaction paths have been manually exercised on a local
Hardhat chain: deposit and delivery confirmation, dispute creation, and
buyer refund. Cancellation has been under investigation; use the
troubleshooting and test instructions below to verify it after updating
the GUI.

## Technology stack

-   **Hardhat 3** --- Solidity development, local blockchain, and
    deployment tooling.
-   **Solidity** --- escrow, factory, and arbitrator smart contracts.
-   **Hardhat Ignition** --- repeatable contract deployment.
-   **Python 3** --- desktop GUI and Ethereum RPC interaction.
-   **Tkinter / ttk** --- graphical interface.
-   **Web3.py** --- contract calls, transaction signing, and JSON-RPC
    communication.
-   **JSON artifacts and configuration** --- contract ABIs and deployed
    contract addresses.

The starter project may also contain Hardhat's example `node:test` and
`viem` integration tests. Those are separate from the Python GUI, which
uses Web3.py. Use the test commands supported by the installed Hardhat
project and its configuration.

## Architecture

``` text
Python Tkinter GUI
       |
       | Web3.py / JSON-RPC
       v
Hardhat local node (127.0.0.1:8545)
       |
       +--> EscrowFactory
       |       |
       |       +--> Escrow deal #1
       |       +--> Escrow deal #2
       |       +--> Escrow deal #N
       |
       +--> Arbitrator
```

### Contracts

-   **`Escrow.sol`** --- stores the buyer, seller, arbitrator, escrow
    amount, and deal state. It implements deposit, delivery
    confirmation, dispute creation, dispute resolution, and
    cancellation.
-   **`EscrowFactory.sol`** --- creates individual escrow contracts and
    records their addresses. It exposes methods such as `createEscrow`,
    `getAllEscrows`, and `getUserEscrows` if present in the deployed
    version.
-   **`Arbitrator.sol`** --- authorizes and executes a dispute decision
    for a selected escrow. The GUI assumes the contract has a
    `resolve(escrowAddress, refundBuyer)` function and that only the
    contract owner/authorized account may call it.

When the factory creates an escrow, the factory is the immediate caller
of the escrow constructor. Therefore, the buyer must be passed
explicitly into the escrow constructor; relying on `msg.sender` inside
that constructor would incorrectly identify the factory as the buyer.

## Requirements

-   Node.js compatible with the installed Hardhat 3 version.
-   npm.
-   Python 3.
-   A virtual environment is recommended for Python.
-   A local Hardhat project with the `Escrow`, `EscrowFactory`, and
    `Arbitrator` contracts and the `EscrowModule.ts` Ignition module.
-   Python dependencies: `web3`.

Check versions:

``` bash
node --version
npm --version
python --version
```

## Project files

The exact layout may vary slightly, but the project should contain
equivalents of:

``` text
hardhat-final/
├── contracts/
│   ├── Escrow.sol
│   ├── EscrowFactory.sol
│   └── Arbitrator.sol
├── ignition/
│   └── modules/
│       └── EscrowModule.ts
├── artifacts/
│   └── contracts/
│       ├── Escrow.sol/
│       │   └── Escrow.json
│       ├── EscrowFactory.sol/
│       │   └── EscrowFactory.json
│       └── Arbitrator.sol/
│           └── Arbitrator.json
├── python/
│   ├── app.py
│   ├── contracts.json
│   ├── Escrow.json
│   ├── EscrowFactory.json
│   └── Arbitrator.json
├── hardhat.config.ts
├── package.json
└── README.md
```

The `artifacts` directory is generated by compilation. The Python
directory needs the ABI artifacts and the `contracts.json` file
alongside the GUI script.

## Install and run

### 1. Install JavaScript dependencies

From the Hardhat project root:

``` bash
npm install
```

If this is the original Hardhat 3 sample project, its package scripts
and configuration may include `node:test`, `viem`, and Solidity tests.
Keep the project's existing package configuration unless you
deliberately intend to change it.

### 2. Compile the contracts

``` bash
npx hardhat compile
```

If compilation fails, resolve the Solidity compiler version and pragma
mismatch first. The Solidity `pragma` versions in the contracts must be
compatible with the compiler configured for the project.

### 3. Run tests

``` bash
npx hardhat test
```

Depending on the installed Hardhat 3 version and project configuration,
you may also be able to run test groups separately:

``` bash
npx hardhat test solidity
npx hardhat test nodejs
```

Use `npx hardhat test --help` if the installed version exposes different
test options. Passing the starter tests does not by itself verify every
escrow GUI workflow; use the manual test plan below as well.

## Deploy the contracts

### 1. Start a local Hardhat node

Open a terminal in the project root and keep it running:

``` bash
npx hardhat node
```

The node prints local test accounts and private keys. Use these
development-only accounts for GUI testing.

### 2. Deploy with Hardhat Ignition

In a second terminal, from the project root:

``` bash
npx hardhat ignition deploy ignition/modules/EscrowModule.ts --network localhost
```

The module should deploy the `Arbitrator` and then deploy
`EscrowFactory` with the arbitrator address. The factory creates
individual escrow contracts later, when a user clicks **Create new
deal** in the GUI.

Record the deployed addresses printed by Ignition.

### 3. Important: local-chain reset

If you stop and restart `npx hardhat node`, the local chain normally
starts from a clean state. Contracts deployed in the previous node
session will no longer exist at their old addresses. Start the node and
deploy again, then update `contracts.json` and the copied artifacts as
needed.

## Configure the Python GUI

### 1. Copy the contract artifacts

After compiling, copy the JSON artifacts into the Python folder:

-   `artifacts/contracts/Escrow.sol/Escrow.json`
-   `artifacts/contracts/EscrowFactory.sol/EscrowFactory.json`
-   `artifacts/contracts/Arbitrator.sol/Arbitrator.json`

These files contain the contract ABI used by Web3.py. If the Python code
expects a filename such as `EscrowFactory.json`, the copied file must
use that exact name.

### 2. Update `contracts.json`

Put the addresses from the most recent Ignition deployment into
`python/contracts.json`:

``` json
{
  "Arbitrator": "PASTE_THE_DEPLOYED_ARBITRATOR_ADDRESS_HERE",
  "EscrowFactory": "PASTE_THE_DEPLOYED_ESCROW_FACTORY_ADDRESS_HERE"
}
```

Replace both placeholders with actual addresses printed by your own
deployment. Do not keep old addresses after restarting the local node
and redeploying.

### 3. Install Python dependencies

Open a terminal in the Python folder:

``` bash
python -m venv .venv
```

Activate it on Windows:

``` powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

Install Web3.py:

``` bash
python -m pip install --upgrade pip
python -m pip install web3
```

Tkinter is usually included with the standard Windows Python installer.
If `import tkinter` fails, repair/reinstall Python with Tcl/Tk support
enabled.

## Run the GUI

Keep the Hardhat node running, then from the Python folder run:

``` bash
python app.py
```

The app should show the localhost connection status and load existing
escrow addresses from the deployed factory.

### Creating a deal

1.  Choose a Hardhat test account private key for the buyer.
2.  Enter the public address of a different Hardhat test account as the
    seller.
3.  Click **Create new deal**.
4.  Wait for the transaction to be mined. The new escrow address should
    appear in the dropdown and deal list.
5.  Select the deal and inspect its status.

### Depositing

1.  Select a deal in `AwaitingPayment`.
2.  Enter a positive ETH amount, for example `0.01`.
3.  Enter the buyer's private key.
4.  Click **1. Deposit Ether**.
5.  Verify the state becomes `AwaitingDelivery` and the amount is
    nonzero.

### Confirming delivery

1.  Select a deal in `AwaitingDelivery`.
2.  Enter the buyer's private key.
3.  Click **2. Confirm delivery and pay seller**.
4.  Verify the state becomes `Complete`, the escrow amount becomes zero,
    and the seller received the payment.

### Raising a dispute

1.  Select a deal in `AwaitingDelivery`.
2.  Use the buyer or seller's private key.
3.  Click **3. Raise a dispute**.
4.  Verify the state becomes `Disputed`.

### Resolving a dispute

1.  Select a deal in `Disputed`.
2.  Open the **Arbitration** tab.
3.  Enter the private key of the authorized arbitrator account (commonly
    the account that deployed `Arbitrator` if the contract restricts
    resolution to its owner).
4.  Select **Refund the buyer** or **Release funds to the seller**.
5.  Click **Resolve dispute**.
6.  Verify the final state and that the escrow balance is zero.

### Cancelling an unpaid deal

Cancellation is allowed only if:

-   the deal state is `AwaitingPayment`;
-   the selected transaction account is the buyer for that deal; and
-   the transaction is sent successfully.

Select a newly created deal, leave it unpaid, enter the buyer's key, and
click **4. Cancel unpaid deal**. The expected state is `Cancelled`. A
deal that has reached `AwaitingDelivery` cannot be cancelled by the
current contract, even if the buyer and seller agree.

## Manual test plan

Use separate test deals so that one final state does not prevent testing
another workflow.

  -----------------------------------------------------------------------
  Test                    Actions                 Expected result
  ----------------------- ----------------------- -----------------------
  Create                  Buyer creates a deal    New escrow address
                          with a different seller appears; state is
                                                  `AwaitingPayment`

  Deposit                 Buyer deposits          State
                          `0.01 ETH`              `AwaitingDelivery`;
                                                  amount `0.01 ETH`

  Delivery                Buyer confirms delivery State `Complete`;
                                                  escrow amount zero;
                                                  seller paid

  Dispute                 Buyer or seller raises  State `Disputed`
                          a dispute after deposit 

  Refund                  Arbitrator resolves     State `Refunded`;
                          with refund enabled     escrow amount zero;
                                                  buyer refunded

  Seller payout           Arbitrator resolves     State `Complete`;
                          with refund disabled    escrow amount zero;
                                                  seller paid

  Cancel                  Buyer cancels a fresh,  State `Cancelled`;
                          unpaid deal             escrow amount zero

  Permission checks       Use a non-buyer to      Transaction should be
                          cancel, or try to       rejected/reverted with
                          cancel after deposit    a visible error
  -----------------------------------------------------------------------

Keep the Hardhat node running during these tests. Local balances and
addresses belong to the local test chain.

## Contract states and rules

The escrow state enum used by the GUI is expected to be ordered as
follows:

  ------------------------------------------------------------------------
                    Enum value State                 Meaning
  ---------------------------- --------------------- ---------------------
                             0 `AwaitingPayment`     Deal created; buyer
                                                     has not deposited

                             1 `AwaitingDelivery`    Escrow has received
                                                     the buyer's deposit

                             2 `Complete`            Payment released to
                                                     seller, either after
                                                     delivery confirmation
                                                     or arbitration

                             3 `Disputed`            Buyer or seller has
                                                     raised a dispute

                             4 `Refunded`            Arbitrator refunded
                                                     the buyer

                             5 `Cancelled`           Buyer cancelled
                                                     before depositing
  ------------------------------------------------------------------------

The GUI maps numeric enum values to labels using this order. If the enum
order in `Escrow.sol` changes, update the Python `STATES` list to match.

## Troubleshooting

### The GUI says it cannot connect

-   Confirm `npx hardhat node` is still running.
-   Confirm the RPC URL is `http://127.0.0.1:8545`.
-   Check that the node is listening on the expected port.

### Contract address or ABI errors

-   Recompile the contracts.
-   Copy the current artifact JSON files into the Python folder.
-   Confirm `contracts.json` contains the latest `Arbitrator` and
    `EscrowFactory` addresses.
-   Redeploy if the local node was restarted.

### Create Deal produces repeated popups

A submitted popup, a mined-transaction popup, and a deal-created popup
can all describe the same transaction. The preferred GUI behavior is one
final success message containing the new escrow address, while errors
remain visible.

### Cancel asks for confirmation but appears to do nothing

Check the following in order:

1.  Select the exact deal you intend to cancel.
2.  Refresh its status and confirm it is `AwaitingPayment`.
3.  Confirm the account shown by the GUI matches the deal's buyer
    address.
4.  Try again and read any error message.
5.  If no transaction hash is created, the failure likely occurred
    before broadcast; inspect the GUI's error handling or the terminal
    traceback. If a transaction was broadcast and reverted, inspect the
    receipt and error details.

The contract's `cancel()` function should be restricted to the buyer and
the `AwaitingPayment` state. It is expected to fail for
`AwaitingDelivery` deals. Do not change the contract to allow
cancellation after deposit unless you also design and test a safe refund
mechanism.

### A transaction fails with an authorization error

-   For buyer-only operations, use the buyer's private key.
-   For arbitration, use the account authorized by `Arbitrator.sol`.
-   The seller's key cannot cancel a deal unless the contract explicitly
    grants that permission.

### Transaction succeeds but the GUI shows stale information

Click **Refresh list** or **Refresh contract status**. Verify the
on-chain state before attempting the operation again.

## Planned improvements

Potential next steps for the project:

1.  **Transaction UX:** one success notification per operation, concise
    messages, and clear errors with transaction hashes only when useful.
2.  **Cancellation diagnostics:** show the reason cancellation is
    unavailable (wrong state, wrong account, or RPC/transaction
    failure).
3.  **Automated tests:** cover all state transitions, authorization
    rules, refunds, seller payouts, and cancellation.
4.  **Input validation:** improve address validation and prevent invalid
    actions based on the selected state.
5.  **Deal history:** display creation time/block, transaction hashes,
    participants, amount, and final outcome.
6.  **Account UX:** show the active account and clarify which role is
    required for each action.
7.  **Events and refresh:** use contract events to update the interface
    and show transaction progress without unnecessary modal dialogs.
8.  **Safer key handling:** replace manual private-key entry with a
    wallet provider or another safer signing workflow.
9.  **Production readiness:** professional security review, tests,
    threat modeling, deployment configuration, and a deliberate
    dispute-resolution policy before any real funds are used.

These are proposed improvements, not claims that they have already been
implemented.

## Security notes

-   Only use Hardhat's local development keys for this project.
-   Never commit private keys, seed phrases, or production credentials.
-   Do not send real ETH to contracts that have not been audited.
-   A local demo contract is not sufficient for real commercial escrow:
    production use requires stronger access control, careful failure
    handling, security testing, and legal/operational decisions about
    arbitration.
-   Smart-contract transactions are irreversible once confirmed, except
    for actions explicitly supported by the contract.

## Useful Hardhat commands and links

``` bash
# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Run configured tests
npx hardhat test

# Start local JSON-RPC node (leave running)
npx hardhat node

# Deploy the escrow module to localhost (run in another terminal)
npx hardhat ignition deploy ignition/modules/EscrowModule.ts --network localhost
```

Official references:

-   [Hardhat 3 Getting
    Started](https://hardhat.org/docs/getting-started#getting-started-with-hardhat-3)
-   [Hardhat 3 Telegram
    group](https://hardhat.org/hardhat3-telegram-group)
-   [Hardhat issue
    tracker](https://github.com/NomicFoundation/hardhat/issues/new)
-   [Hardhat Ignition documentation](https://hardhat.org/ignition/docs)
-   [Web3.py documentation](https://web3py.readthedocs.io/)
-   [Solidity documentation](https://docs.soliditylang.org/)
-   [Tkinter
    documentation](https://docs.python.org/3/library/tkinter.html)
