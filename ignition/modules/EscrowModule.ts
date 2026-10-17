import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("EscrowModule", (m) => {
    const arbitrator = m.contract("Arbitrator");
    // Account 1 address
    const sellerAddress = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
    const escrow = m.contract("Escrow", [sellerAddress, arbitrator]);
    return {arbitrator, escrow };
});