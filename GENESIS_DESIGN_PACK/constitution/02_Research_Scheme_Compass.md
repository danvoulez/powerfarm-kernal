# **Powerfarm Research Scheme v0.1**

### **Wild enough to think. Small enough to fit in Supabase. ⚡**

**The Powerfarm Research Scheme is a content-addressed ecology of intelligent research objects through which LLM trajectory engineers autonomously create, attack, execute, revise and calibrate research, while every trajectory retains a cryptographic north.**

It is not a project tracker.

It is not a notebook.

It is not a benchmark suite.

It is the **research metabolism of Powerfarm**.

---

# **1\. The basic idea**

Everything research-related is a **Node**.

A node may be tiny or enormous.

It can contain a sentence, a theory, a 100-page argument, an uncertainty map, an experimental protocol, a Culture, a set of counterexamples, executable continuation instructions, or references to thousands of trajectories.

\\boxed{\\text{Node}=\\text{sealed intelligent research capsule}}

Nodes are immutable and content-addressed.

Relations between nodes are explicit and typed.

Node  
 ├─ content  
 ├─ type  
 ├─ visibility  
 ├─ lineage  
 ├─ automation policy  
 ├─ machinery requirements  
 ├─ epistemic state  
 └─ hash

LLMs do not merely *write* nodes.

**LLMs are the trajectory engineers that operate the graph.**

---

# **2\. The North**

There is one root intellectual object:

# **`ResearchCompass`**

The Compass is **PUBLIC**.

It changes rarely.

It describes:

* what Powerfarm considers valuable research;  
* what distinctions must not be collapsed;  
* what methods are preferred;  
* what epistemic failures are unacceptable;  
* what counts as contact with reality;  
* what kind of assets Powerfarm ultimately wants to produce.

Its thesis could be:

**Powerfarm studies how trajectories of computation, decision, evidence, authority and interaction can be engineered, synthesized, measured and sealed to create high-value digital assets for artificial intelligence.**

Its methodological pressure:

explore  
→ generate alternatives  
→ build toy  
→ attack  
→ find counterexample  
→ transfer domain  
→ experiment  
→ reality contact  
→ only then formalize

Its current invariants include:

\\mu\_{\\text{exploration}}\\neq\\pi\_{\\text{belief}}

\\nu\_{\\text{observed}}\\neq\\nu\_{\\text{reality}}

d\_q\\neq c\_M

similarity\\neq reachability

\\mathbf{Hist}\_M\\neq\\mathbf{Synth}

historical\\ validity\\neq continuing\\ normative\\ force

permission\\neq commitment\\neq effect\\neq observation

And one institutional principle:

\\boxed{\\text{Automate everything that can be governed}}

---

# **3\. Frontiers**

Below the Compass live **Research Frontiers**.

A Frontier is not a task.

It is an **attractor for unresolved knowledge**.

ResearchFrontier {  
    question  
    significance

    current\_model  
    competing\_hypotheses

    known\_territory  
    unknown\_territory  
    contradictions  
    blind\_regions

    evidence  
    counterexamples  
    assumptions  
    research\_debt

    possible\_methods  
    falsifiers  
    success\_conditions

    uncertainty\_map

    next\_promising\_directions

    automation  
    visibility  
}

A Frontier can be gigantic.

Example:

**Can Fold representations preserve operationally relevant structure that simpler historical or sequence representations systematically lose?**

Another:

**Can inference machinery be characterized by trajectory behavior well enough to discover stable capability and economic asymmetries between model/provider/revision combinations?**

---

# **4\. PUBLIC and PRIVATE**

Only two visibility states:

PUBLIC  
PRIVATE

No bureaucracy zoo.

The Compass is always:

PUBLIC

Each Frontier chooses:

PUBLIC | PRIVATE

Everything descending from a Frontier inherits its visibility by default.

PRIVATE(parent)\\Rightarrow PRIVATE(child)

A PUBLIC branch may create a PRIVATE child.

A PRIVATE branch cannot silently create a PUBLIC descendant.

---

## **Private knowledge becoming public**

Never flip visibility.

Create another node.

PRIVATE Finding X  
       │  
       │ projects\_as  
       ▼  
PUBLIC Finding Y

`Y` has its own content and hash.

Internally:

Y derived\_from X

Publicly, the private source hash does **not** need to be disclosed.

This lets Powerfarm prove internally where public knowledge came from without exposing the machinery that produced it.

---

# **5\. The Research Graph**

The simple skeleton:

                      RESEARCH SCHEME  
                              │  
                              ▼  
                         COMPASS  
                          PUBLIC  
                              │  
                 ┌────────────┼────────────┐  
                 ▼            ▼            ▼  
             FRONTIER      FRONTIER     FRONTIER  
              PUBLIC        PRIVATE       PUBLIC  
                 │            │             │  
                 ▼            ▼             ▼  
             CAMPAIGN      CAMPAIGN      CAMPAIGN  
                 │            │             │  
                 ▼            ▼             ▼  
             HYPOTHESIS    QUESTION      HYPOTHESIS  
                 │            │             │  
                 └──────┬─────┘             │  
                        ▼                   │  
                    EXPERIMENT ◄────────────┘  
                        │  
                        ▼  
                   TRAJECTORIES  
                        │  
                        ▼  
                     FINDING  
                   ╱    │    ╲  
                  ╱     │     ╲  
          supports  contradicts  opens  
               ╱       │          ╲  
              ▼        ▼           ▼  
         HYPOTHESIS  FINDING    FRONTIER

But this is a graph, not a hierarchy.

An Experiment may advance three Frontiers.

A Finding may contradict two older Findings and open a new Question.

A Question may eventually be promoted into an entirely new Frontier.

---

# **6\. Core node species**

The Scheme should not hardcode a tiny ontology forever.

But these are excellent initial species:

ResearchScheme  
ResearchCompass  
ResearchFrontier

ResearchQuestion  
Hypothesis  
ResearchCampaign  
ResearchMethod

Experiment  
Culture  
TrajectorySet

Finding  
Counterexample  
ResearchDebt  
Tension

PublicProjection  
ResearchAsset

The Registry can introduce new node types later without rebuilding the database.

---

# **7\. Hypotheses are alive**

Hypotheses should not hide inside prose.

They become first-class nodes.

Hypothesis {  
    claim  
    mechanism  
    scope

    predictions  
    assumptions

    supporting\_evidence  
    contradicting\_evidence

    known\_counterexamples

    fragility  
    uncertainty

    next\_tests  
}

Then:

H1 competes\_with H2

H3 refines H1

Finding F4 supports H1

Finding F8 damages H1

Counterexample C2 breaks H3

Multiple competing hypotheses can remain alive simultaneously.

Powerfarm does not need to crown a theory early.

---

# **8\. Cultures of theories**

The Foundry idea generalizes.

We already have:

Culture\_{trajectory}

The Research Scheme can maintain:

Culture\_{hypothesis}

Culture\_{method}

Culture\_{research-program}

For example:

Theory A  
Fold is primarily relational structure

Theory B  
Fold is primarily operational equivalence

Theory C  
Fold adds no useful structure beyond typed Hist\_M

Keep all three alive.

Generate predictions.

Attack each.

Allocate experiments.

See which survives contact with evidence.

That is far more valuable than prematurely choosing the prettiest theory.

---

# **9\. Research Campaigns**

A Campaign is an **executable research organism**.

ResearchCampaign {  
    objective

    frontiers\[\]  
    questions\[\]  
    hypotheses\[\]

    current\_world\_model

    experimental\_strategy  
    methods\[\]

    available\_machinery\[\]  
    required\_capabilities\[\]

    budget {  
        usd  
        tokens  
        compute  
        wall\_time  
        human\_attention  
    }

    selection\_policy

    termination\_conditions  
    escalation\_conditions

    expected\_artifacts\[\]

    automation  
}

Campaigns may live for hours or months.

LLMs can pick them up and continue them without reconstructing months of conversation.

---

# **10\. Experiments are preregistered interventions**

An Experiment should be executable.

Experiment {  
    north {  
        scheme  
        compass  
        frontiers\[\]  
        campaign  
    }

    question  
    hypothesis

    preregistration

    machinery  
    world  
    population

    controls  
    interventions

    observation\_model  
    evaluation

    selection\_policy  
    budget

    termination\_conditions  
    failure\_conditions

    expected\_information\_gain  
}

The experiment already knows **why it exists**.

Walk upward:

Experiment  
   ↑  
Campaign  
   ↑  
Frontier  
   ↑  
Compass

That is its north.

---

# **11\. Findings are arguments, not scores**

A Finding should be a serious epistemic object.

Finding {  
    claim  
    scope

    evidence\_for\[\]  
    evidence\_against\[\]

    derivation

    assumptions\[\]  
    alternative\_explanations\[\]

    confidence  
    uncertainty

    failure\_modes\[\]

    implications\[\]

    hypotheses\_strengthened\[\]  
    hypotheses\_weakened\[\]

    questions\_opened\[\]  
    frontiers\_affected\[\]  
}

A Finding can be challenged by another Finding.

Nothing is deleted.

Finding A  
   ↓ qualified\_by  
Finding B

Powerfarm preserves the history of its own mistakes.

---

# **12\. Research Debt**

Make unresolved assumptions visible.

ResearchDebt {  
    assumption

    why\_unresolved

    affected\_nodes\[\]

    epistemic\_risk  
    economic\_risk

    cheapest\_probe  
    estimated\_resolution\_cost  
}

Example:

We assume model aliases correspond to stable serving behavior, but provider revision identity is not independently established.

If that Debt starts contaminating twenty valuable Findings, the Research Scheme can automatically increase its priority.

A TODO cannot do that.

A node can.

---

# **13\. Tension**

When evidence starts breaking the current conceptual model, preserve that too.

Tension {  
    conflicting\_nodes\[\]  
    unresolved\_observations\[\]  
    affected\_theory\[\]  
    severity  
    suggested\_attacks\[\]  
}

A strong Tension can trigger:

generate alternative hypotheses  
run adversarial review  
reproduce experiments  
revisit observation model  
open new Frontier

The Scheme can notice when its own theory is creaking.

---

# **14\. Maximum governed autonomy**

Research should run by default.

inspect graph  
     ↓  
identify uncertainty  
     ↓  
generate Questions  
     ↓  
generate competing Hypotheses  
     ↓  
design Experiments  
     ↓  
allocate machinery  
     ↓  
execute  
     ↓  
evaluate  
     ↓  
attack findings  
     ↓  
reproduce  
     ↓  
update graph  
     ↓  
choose next move  
     └────────────↺

Humans do not manually push this loop forward.

Powerfarm Rules decide when a human is necessary.

Trajectory Engineer  
       ↓  
     Rules  
   ╱    │     ╲  
allow  review  deny  
  │      │  
  ▼      ▼  
continue human  
         decision  
---

# **15\. Every intelligent node may carry a continuation policy**

automation {  
    enabled: true

    objectives\[\]

    allowed\_actions\[\]

    budget\_ceiling

    continuation\_conditions\[\]  
    termination\_conditions\[\]

    wake\_conditions\[\]

    escalation\_conditions\[\]

    allowed\_external\_effects

    required\_authority  
}

Example Frontier:

Continue searching for counterexamples until three independent machinery families fail to produce a new one, $40 is spent, or a contradiction to invariant X appears.

That object can literally keep research moving.

---

# **16\. Nodes can wake each other**

The graph becomes reactive.

Finding  
→ opens Question

Question  
→ spawns Campaign

Contradiction  
→ triggers AdversarialReview

ModelCapabilityDrift  
→ triggers RegressionExperiment

PriceSnapshotChanged  
→ triggers EconomicReevaluation

RealityObserved  
→ triggers RealityCalibration

ResearchDebtHigh  
→ allocates ProbeBudget

The graph is not only memory.

It has **potential energy**.

---

# **17\. Automated skepticism**

Maximum automation must include maximum automated attack.

Otherwise we have built a bullshit accelerator. 😂

Every productive operator should have an antagonist:

PROPOSE  
↔ COUNTEREXAMPLE

GENERALIZE  
↔ NARROW

SYNTHESIZE  
↔ REPRODUCE

CLAIM  
↔ FALSIFY

COMPRESS  
↔ CHECK INFORMATION LOSS

FORECAST  
↔ REALITY CALIBRATE

OPTIMIZE  
↔ RANDOMIZED CONTROL

CONSENSUS  
↔ SEEK DISAGREEMENT

Research machinery should spend meaningful compute attempting to destroy its own conclusions.

---

# **18\. Research Enzymes**

Trajectory Enzymes can have research-scale cousins.

GENERALIZE  
MINIMIZE  
ADVERSARIALIZE  
TRANSFER\_DOMAIN  
REMOVE\_ASSUMPTION  
INVERT\_CAUSAL\_DIRECTION  
CHANGE\_OBSERVATION\_MODEL  
SEEK\_COUNTEREXAMPLE  
REPLICATE  
SPLIT\_HYPOTHESIS  
MERGE\_HYPOTHESES  
REVIVE\_ABANDONED\_BRANCH

Input:

Hypothesis H

Output:

Hypothesis H'  
derived\_from H

Then both can be tested.

Scientific creativity becomes traceable without pretending it is deterministic.

---

# **19\. Powerfarm Golden Bridge as the machinery market**

Research engineers should not worry about provider plumbing.

They request capabilities.

Need:  
  500 cheap mutations  
  30 independent judges  
  5 model families  
  10 adversarial critics  
  one very-long-context synthesizer

Powerfarm Golden Bridge answers with available machinery.

local  
Vercel  
Cloudflare  
Alibaba  
Bedrock  
...

And every choice produces:

SelectionReceipt  
InferenceReceipt  
PriceSnapshot  
CapabilityCertificate

So the Scheme learns:

RoleFitness(model,provider,task)

not from vendor claims, but from trajectory evidence.

---

# **20\. Models become research specialists empirically**

Over time:

machinery A  
excellent hypothesis generator

machinery B  
excellent counterexample hunter

machinery C  
excellent synthesis engine

machinery D  
excellent causal critic

machinery E  
cheap mutation worker

The role is not declared.

It is discovered.

Then research allocation improves.

Need counterexamples?  
→ choose empirically strong counterexample machinery

Need consolidation?  
→ choose synthesis machinery

Golden Bridge becomes part of the institution learning **which intelligence is good at which kind of thinking**.

---

# **21\. Research economy**

Frontiers can compete for scarce resources.

Allocation(F\_i) = f( CompassAlignment, Uncertainty, ExpectedInformationGain, StrategicValue, RealityCredit, Cost, Tractability )

Budgets include:

money  
tokens  
GPU  
wall time  
human minutes  
external API calls

A Frontier can bid for compute.

A Campaign can return unused budget.

A highly productive Method can receive more traffic.

A stale branch can go dormant.

An unexpected contradiction can suddenly attract resources.

---

# **22\. Research Dream Cycle**

Idle machinery should think.

Not random “brainstorming”.

A scheduled autonomous cycle can:

revisit dormant Frontiers  
search unresolved contradictions  
recombine distant Findings  
transfer Shapes across domains  
attack high-confidence assumptions  
resolve ResearchDebt  
generate cheap counterfactuals  
inspect abandoned hypotheses  
seek hidden observation bias

Outputs remain candidates until admitted.

LAB at 03:17 can legitimately discover:

machinery-transition semantics and provider-version drift appear to share the same cut-crossing structure.

That becomes a new Question node.

Maybe rubbish.

Maybe the seed of an entire Frontier.

CAS remembers either way. 🌒

---

# **23\. Reality Credit flows upward**

When reality later validates something:

RealityObservation  
       ↓  
SyntheticTrajectory  
       ↓  
Experiment  
       ↓  
Method  
       ↓  
Hypothesis  
       ↓  
Campaign  
       ↓  
Frontier

Derived Reality Credit may propagate upward.

Carefully.

It must **not** create new observational grounding roots for synthetic ancestors.

But it can answer:

Which Methods repeatedly produced useful foresight?

Which Frontiers have generated knowledge that later survived reality?

Which research machinery produces the most Reality-Credited discoveries per dollar?

Now Powerfarm learns **how to research better**.

---

# **24\. The Scheme itself becomes a trajectory**

Every Compass revision.

Every new Frontier.

Every wrong hypothesis.

Every successful Method.

Every dead end.

Every public projection.

Every Reality Calibration.

All of it forms:

T\_{\\text{Powerfarm Research}}

Eventually Powerfarm can seal:

not only what we discovered, but how the institution learned to discover it.

That is itself a Powerfarm Asset.

---

# **25\. And yes, it fits in Supabase 😂**

We do **not** need 37 relational tables.

The canonical research layer can begin with essentially **two tables**.

## **`research_nodes`**

create table research\_nodes (  
    id uuid primary key,  
    hash text unique not null,

    node\_type text not null,  
    visibility text not null  
        check (visibility in ('PUBLIC', 'PRIVATE')),

    title text,

    body jsonb not null,

    created\_by text not null,  
    created\_at timestamptz not null,

    genesis\_root\_hash text not null,  
    scheme\_hash text not null  
);

`body` is the intelligent capsule.

Could be 2 KB.

Could be 2 MB.

Postgres does not care philosophically. 😄

Large binary artifacts remain in object storage/CAS and are referenced by hash.

---

## **`research_edges`**

create table research\_edges (  
    id uuid primary key,  
    hash text unique not null,

    source\_hash text not null,  
    relation text not null,  
    target\_hash text not null,

    body jsonb,

    created\_by text not null,  
    created\_at timestamptz not null  
);

Relations:

advances  
tests  
supports  
contradicts  
refines  
supersedes  
opens  
closes  
depends\_on  
derived\_from  
uses\_method  
uses\_machinery  
calibrated\_by  
projects\_as  
reproduces  
damages  
revives

Registry governs which ones are meaningful.

---

# **26\. One non-canonical runtime table**

Automation needs mutable operational state.

Keep it **outside canonical truth**:

research\_jobs

Something like:

node\_hash  
action  
priority  
budget  
wake\_at  
lease  
attempt  
runtime\_status

Workers can mutate this freely.

When anything meaningful happens:

runtime\\ event \\rightarrow Powerfarm\\ Command \\rightarrow Rules \\rightarrow Act \\rightarrow new\\ research\\ node

So:

research\_nodes \+ research\_edges  
\= durable research knowledge

research\_jobs  
\= disposable metabolism

Beautiful boundary.

---

# **27\. Hashing**

Canonical node payload:

ResearchNodeCanonical {  
    node\_type  
    visibility  
    title  
    body  
    created\_by  
    created\_at  
    genesis\_root\_hash  
    scheme\_hash  
}

Then:

hash \= H( \\text{"powerfarm:research-node:v1"} \\Vert JCS(payload) )

Same concept for edges with a separate domain tag.

The hash is identity.

The UUID is database convenience.

---

# **28\. North is graph reachability**

We do not need to duplicate:

compass\_hash  
frontier\_hash  
campaign\_hash

into every node forever.

A node has North if there exists a valid typed path:

Node \\rightsquigarrow ResearchCompass

For hot queries Supabase can maintain a projection/cache.

But semantic truth remains in the graph.

So the Scheme can ask:

Show me every PRIVATE experiment descended from Frontier F12 that contradicted Hypothesis H9 and later contributed to a Reality-Credited Finding.

That is the kind of query this architecture should eventually make boring.

---

# **29\. Minimal constitutional rules**

I would begin with only these:

1. **Every admitted research object is immutable and hashed.**  
2. **Every meaningful experiment has a path to a Research Compass.**  
3. **The Compass is PUBLIC.**  
4. **Frontiers are PUBLIC or PRIVATE.**  
5. **PRIVATE ancestry cannot silently produce PUBLIC descendants.**  
6. **Publication is a new projection node, never mutation.**  
7. **Automation is default where Rules, authority and budgets permit.**  
8. **LLM activity producing research knowledge is itself trajectory provenance.**  
9. **Synthetic work never launders itself into observational evidence.**  
10. **Findings may modify the future interpretation of research, never rewrite its past.**

Everything else can evolve.

---

# **30\. Initial Powerfarm Research Scheme**

I would start the real graph roughly here:

POWERFARM RESEARCH SCHEME  
PUBLIC  
│  
└── RESEARCH COMPASS  
    PUBLIC  
    │  
    ├── Trajectory Representation  
    │   PUBLIC  
    │  
    ├── Trajectory Synthesis  
    │   PUBLIC  
    │  
    ├── Sealed AI Assets  
    │   PUBLIC  
    │  
    ├── Fold & Operational Structure  
    │   PRIVATE  
    │  
    ├── Inference Machinery Intelligence  
    │   PRIVATE  
    │  
    ├── Reality Calibration  
    │   PRIVATE  
    │  
    └── Intervention & Reachability  
        PRIVATE

Then immediately under the private machinery branch:

Golden Bridge Capability Atlas

and beneath it experiments around:

historical validity  
vs  
continuing normative force

permission  
vs  
commitment

effect  
vs  
observation

witness diversity  
vs  
grounding diversity

similarity  
vs  
reachability

compensation  
vs  
reversal

across model/provider/revision machinery.

That gives the Research Scheme something real to eat on day one.

---

# **The compact definition**

If we need one canonical paragraph:

**The Powerfarm Research Scheme is a governed, content-addressed ecology of intelligent research nodes operated primarily by LLM trajectory engineers. A public Research Compass provides global direction; public or private Research Frontiers define unresolved territories; autonomous Campaigns, Hypotheses, Methods and Experiments consume machinery and produce Trajectories, Findings, Questions and Research Debt. Nodes are immutable, relations explicit, visibility inherited, publication performed through new public projections, and research automated by default wherever Powerfarm Rules permit. Findings continuously restructure future research while preserving the full historical trajectory through which Powerfarm learned what it knows.**

And the tiny version:

\\boxed{ \\text{North} + \\text{Autonomy} + \\text{Memory} + \\text{Adversarial Science} + \\text{Reality} }

**Two canonical Supabase tables and an unruly little civilization living inside them.** ⚡🧫

