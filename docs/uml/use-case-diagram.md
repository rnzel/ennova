# ENNOVA Use Case Diagram

This diagram shows the supported actor interactions at the Flask API boundary and the external components used by backend workflows. The trustee is not shown as an actor because the finalized requirements assign no actions or reading rights to a trustee.

```mermaid
flowchart LR
    Owner["🧍 Owner"]
    Beneficiary["🧍 Registered beneficiary / asker"]
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
        UCOwnerAsk([Chat about own diary])
        UCAccess([Resolve per-entry access])
        UCRetrieve([Retrieve permitted entry views])
        UCAnswer([Generate answer from permitted context])
        UCOwnerRetrieve([Retrieve own verified records])
        UCOwnerAnswer([Generate cited owner answer])
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
    Owner --- UCOwnerAsk

    Beneficiary --- UCRedeem
    Beneficiary --- UCLogin
    Beneficiary --- UCAsk

    UCAsk -. includes .-> UCAccess
    UCAsk -. includes .-> UCRetrieve
    UCAsk -. includes .-> UCAnswer
    UCOwnerAsk -. includes .-> UCOwnerRetrieve
    UCOwnerAsk -. includes .-> UCOwnerAnswer
    Prolog --- UCAccess
    Model --- UCAnswer
    Model --- UCOwnerAnswer

    UCMode -. "planned: no owner API/UI flow" .-> UCCreate

    classDef planned stroke-dasharray: 5 5,fill:#fff7e6,color:#654;
    class UCMode planned;
    classDef actor fill:transparent,stroke:transparent,color:#222;
    class Owner,Beneficiary actor;
```

The owner and registered beneficiary use a standing-person symbol as the actor figure, while the system boundary contains ENNOVA use cases. The owner chatbot and beneficiary Q&A are separate: owner questions retrieve only the authenticated owner's verified records and do not call Prolog; beneficiary questions pass through Prolog authorization and send only permitted tool results to the model. Owner conversation context is temporary and owner-bound. The `/entries` endpoint supports owner-created diary entries and letters, and the writing-mode classes can derive immutable versions. However, the API does not accept a selected mode or call the mode registry when saving an entry; that owner-facing workflow remains planned. Policy `trustee is` and `transfer custody` statements are parsed into facts, but trustee administration is not an implemented interaction.
