import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("EscrowModule", (m) => {
    const arbitrator = m.contract("Arbitrator");
    // Account 0 address
    const sellerAddress = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266";
    const escrow = m.contract("Escrow", [sellerAddress, arbitrator]);
    return {arbitrator, escrow };
});