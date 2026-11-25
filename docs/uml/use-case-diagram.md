# ENNOVA Use Case Diagram

This diagram shows the supported actor interactions at the Flask API boundary and the external components used by backend workflows. The trustee is not shown as an actor because the finalized requirements assign no actions or reading rights to a trustee.

```mermaid
flowchart LR
    Owner[Owner]
    Beneficiary[Registered beneficiary / asker]
    Prolog[SWI-Prolog access engine]
    Model[Local model: Ollama or fake]

    subgraph ENNOVA[ENNOVA system]
        UCRegisterOwner([Register owner])
        UCLogin([Log in])
        UCInvite([Issue beneficiary invitation])
        UCRedeem([Redeem invitation and register])
        UCCreate([Create diary entry or letter])
        UCList([List own entries])
        UCPolicy([Submit or replace policy])
        UCTrigger([Confirm death trigger and freeze policy])
        UCAsk([Ask a grounded question])
        UCAccess([Resolve per-entry access])
        UCRetrieve([Retrieve permitted entry views])
        UCAnswer([Generate answer from permitted context])
        UCMode([Apply selected writing mode to entry])
    end

    Owner --- UCRegisterOwner
    Owner --- UCLogin
    Owner --- UCInvite
    Owner --- UCCreate
    Owner --- UCList
    Owner --- UCPolicy
    Owner --- UCTrigger
    Owner --- UCMode

    Beneficiary --- UCRedeem
    Beneficiary --- UCLogin
    Beneficiary --- UCAsk

    UCAsk -. includes .-> UCAccess
    UCAsk -. includes .-> UCRetrieve
    UCAsk -. includes .-> UCAnswer
    Prolog --- UCAccess
    Model --- UCAnswer

    UCMode -. "planned: no owner API/UI flow" .-> UCCreate

    classDef planned stroke-dasharray: 5 5,fill:#fff7e6,color:#654;
    class UCMode planned;
```

The `/entries` endpoint supports owner-created diary entries and letters, and the writing-mode classes can derive immutable versions. However, the API does not accept a selected mode or call the mode registry when saving an entry; that owner-facing workflow remains planned. Beneficiary questions pass through Prolog authorization, and the model receives only permitted tool results. Owner Q&A is not implemented and returns the neutral reply. Policy `trustee is` and `transfer custody` statements are parsed into facts, but trustee administration is not an implemented interaction.
