import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("EscrowModule", (m) => {
    const arbitrator = m.contract("Arbitrator");
    const factory = m.contract("EscrowFactory", [arbitrator]);

    return { arbitrator,factory };
});