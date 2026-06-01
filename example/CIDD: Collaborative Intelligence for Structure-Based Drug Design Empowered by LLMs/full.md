# CIDD: Collaborative Intelligence for Structure-Based Drug Design Empowered by LLMs

Bowen Gao1,2∗, Yanwen Huang3∗, Yiqiao Liu3, Wenxuan Xie4, Bowei He5, Haichuan Tan1, Wei-Ying Ma1, Ya-Qin Zhang1, Yanyan Lan1,6,7†

1Institute for AI Industry Research (AIR), Tsinghua University, Beijing, China   
2Department of Computer Science and Technology, Tsinghua University, Beijing, China   
3Department of Pharmaceutical Science, Peking University, Beijing, China   
4School of Future Technology, South China University of Technology, Guangzhou, China   
5Department of Computer Science, City University of Hong Kong, Hong Kong SAR, China   
6Beijing Frontier Research Center for Biological Structure, Tsinghua University, Beijing, China   
7Beijing Academy of Artificial Intelligence (BAAI), Beijing, China

# Abstract

Structure-guided molecular generation is pivotal in early-stage drug discovery, enabling the design of compounds tailored to specific protein targets. However, despite recent advances in 3D generative modeling, particularly in improving docking scores, these methods often produce uncommon and intrinsically unreasonable molecular structures that deviate from drug-like chemical space. To quantify this issue, we propose a novel metric, the Molecule Reasonable Ratio (MRR), which measures structural rationality and reveals a critical gap between existing models and real-world approved drugs. To address this, we introduce the Collaborative Intelligence Drug Design (CIDD) framework, the first approach to unify the 3D interaction modeling capabilities of generative models with the general knowledge and reasoning power of large language models (LLMs). By leveraging LLMbased Chain-of-Thought reasoning, CIDD generates molecules that are not only compatible with protein pockets but also exhibit favorable drug-likeness, structural rationality, and synthetic accessibility. On the CrossDocked2020 benchmark, CIDD consistently improves drug-likeness metrics, including QED, SA, and MRR, across different base generative models, while maintaining competitive binding affinity. Notably, it raises the combined success rate (balancing drug-likeness and binding) from 15.72% to 34.59%, more than doubling previous results. These findings demonstrate the value of integrating knowledge reasoning with geometric generation to advance AI-driven drug design.3

# 1 Introduction

Structure-based drug design (SBDD) enables the direct generation of compounds tailored to protein binding sites, making it a powerful tool in drug discovery. Recent 3D generative models—including autoregressive approaches like AR [24] and Pocket2Mol [25], and diffusion-based methods such as TargetDiff [12], DecompDiff [13], and MolCRAFT [26]—have advanced rational molecule design. However, expert evaluation often reveals chemically unreasonable features, such as overly fused polycyclic systems and partially unsaturated rings (Figure 1a). While these distortions may improve docking scores via geometric complementarity, they often compromise intramolecular stability and result in poor pharmacokinetic properties.

![](images/427941a5c1afc9a0a7055126e95fb0988e9fbdf2f28c2bc95003052926f01840.jpg)

<details>
<summary>chemical</summary>

Molecular structures of imatinib and polycyclic systems with correctional labeling
</details>

(a)

![](images/7b5c48bae98fbf8fe69ff257689a12206a0f082f875c9341ab41658cfe6b0083.jpg)

<details>
<summary>bar</summary>

MRR Comparison Across Methods
| Method | Molecule Reasonable Ratio (MRR, %) |
| :--- | :--- |
| AR | 56.7 |
| Pocket2MoL | 67.9 |
| TargetDiff | 37.8 |
| DecompDiff | 62.6 |
| MoICRAFT | 58.5 |
| TAGMol | 37.3 |
| LLM | 97.5 |
| CIDD | 81.7 |
FDA Drugs MRR (85.9%)
</details>

(b)   
Figure 1: (a) Common errors in 3D-SBDD outputs. Minor structural changes can cause large deviations in 3D conformation, highlighting the challenge of correcting chemically uncommon structures without disrupting valid 3D shapes. (b) MRR comparison. While FDA drugs reach 85.9% MRR, existing 3D models lag behind. LLM achieves 97.5%, and CIDD closes the gap with 81.7%.

While current models effectively generate molecules that fit target pockets, they often overlook the physicochemical and pharmacological features common to clinically approved drugs. These limitations stem from a fundamental mismatch: the narrow focus on binding-site compatibility often comes at the expense of structural reasonability and drug-likeness, which depend solely on the chemical structure itself and often conflict with geometric fit. To quantify the gap, we propose the Molecular Reasonability Ratio (MRR), which measures the proportion of generated molecules that are structurally valid and chemically reasonable relative to drug-like standards. As shown in Figure 1b, based on our experiments, existing 3D generative models perform poorly under this metric (e.g., TargetDiff: 37.8%, MolCRAFT: 58.5%), falling well below the 85.9% observed in FDA-approved drugs. Some recent methods, such as TAGMol, build on TargetDiff by incorporating gradient-based guidance to jointly optimize for drug-likeness properties like QED [3]. While this leads to improvements in QED scores, it does not result in a general enhancement of drug potential, as evidenced by TAGMol’s similarly low MRR. In contrast, LLMs achieve high MRRs on SBDD tasks (e.g., GPT-4: 97.5%) thanks to their general chemical and pharmaceutical knowledge, but they struggle to generate molecules with high binding affinity due to limited spatial reasoning and the inherent trade-off between potency and drug-likeness.

To bridge this gap, we propose CIDD—a Collaborative Intelligence for Drug Design framework that combines the interaction modeling capabilities of 3D generative models with the domain knowledge and instruction following strengths of LLMs. Rather than directly producing final drug candidates, 3D models generate interaction-focused molecular proposals that capture key binding features. These serve as structured input for an LLM-driven design process that translates spatial intent into chemically viable drug-like molecules. This division of roles allows CIDD to generate compounds that are both interaction-competent and structurally plausible. CIDD decomposes the generation task into a series of specialized modules, each powered by the LLM. The Interaction Analysis Module identifies fragment-level interactions; the Design Module proposes chemically informed modifications; the Reflection Module provides analysis; and the Selection Module ranks candidates by interaction quality and chemical coherence. CIDD follows a structured Chain-of-Thought (CoT) prompting strategy guided by domain knowledge guided prompts, enabling interpretable, stepwise molecular design. This modular, CoT-guided architecture mirrors real-world medicinal chemistry workflows and enables the generation of pharmaceutically relevant, structurally sound compounds.

Evaluated on the CrossDocked2020 dataset [9], CIDD significantly outperforms state-of-the-art baselines, boosting the overall success ratio from 15.72% to 34.59%. It consistently improves key drug-likeness metrics—including Quantitative Estimation of Drug-likeness (QED) [3], synthetic accessibility (SA), MRR, and the proportion of molecules meeting QikProp [30] thresholds—across diverse baseline models. Our key contributions are:

(1) Identifying a core limitation in current SBDD models: We introduce the MRR to assess intrinsic structural rationality, revealing that pocket-based 3D generative models often produce intrinsically irrational and rare molecules that deviate from drug-like chemical space despite favorable docking scores.

(2) A unified framework for rational molecule generation: We propose CIDD, the first framework to combine the spatial modeling of 3D generative models with the chemical reasoning capabilities of LLMs. By leveraging their complementary strengths, CIDD uses Chain-of-Thought guidance to overcome the common trade-off between binding affinity and drug-likeness.   
(3) Validated performance and broader implications: CIDD achieves state-of-the-art results on CrossDocked2020, significantly improving drug-likeness metrics (QED, SA, MRR) while preserving binding affinity. This demonstrates its effectiveness and highlights the advantage of combining LLMs with geometric modeling for AI-driven drug design.

# 2 Preliminaries

# 2.1 Structure-Based Drug Design

The goal of SBDD is to generate a molecule x that binds to a given protein pocket P . Recent work has explored a variety of deep generative approaches. LiGAN [27] uses a conditional variational autoencoder (CVAE) to generate 3D point clouds of ligands conditioned on pocket geometry. Autoregressive models such as AR [24] and Pocket2Mol [25] sequentially construct molecules in 3D space. Diffusion-based methods like TargetDiff [12], IPDiff [15], and DecompDiff [13] iteratively refine 3D structures or molecular graphs, while TAGMol [7] further applies gradient-based optimization during generation. Other approaches include the fragment-based DrugGPS [37] and MolCRAFT [26], a Bayesian flow model that learns the distribution of drug-like molecules conditioned on pocket structures. All these methods generate intermediate 3D point clouds or graphs, which are subsequently mapped into chemically valid molecules as the final output.

# 2.2 Large Language Models

LLMs are advanced neural networks trained on vast corpora of textual data, enabling them to understand, generate, and reason with human-like language. Notable examples include GPT-4 [2], LLaMA [33], ChatGLM [11], and DeepSeek [21], which have demonstrated impressive capabilities in tasks such as natural language understanding, code generation, mathematical problem solving, and logical reasoning. Their versatility and ability to capture complex patterns have made them increasingly relevant in domains beyond traditional natural language processing, including drug discovery [4]. Recent work has explored the use of LLMs to generate or modify molecules with desired properties. For example, ChatDrug [22] employs conversational LLMs for generating and editing molecules with desired properties. However, the application of LLMs to pocket-based molecular design remains largely unexplored. This is primarily due to the challenge of capturing essential three-dimensional structural information, which is critical for modeling protein-ligand interactions. Unlike textual or sequence-based data, protein binding pockets and small molecules interact through spatially complex, non-linear, and chemically rich environments that cannot be directly encoded in natural language.

# 3 Methods

# 3.1 Evaluating the Gap Between Generated Molecules and Real Drugs

Drug-likeness is an inherently multidimensional attribute that dictates the probability p(drug) that a molecule will reach its biological target—an assessment that precedes, and is distinct from, estimating binding affinity. Widely used machine-learning surrogates, most notably QED [3] and Lipinski’s Rule of Five [20], are inadequate for two principal reasons: (i) Legacy bias: These metrics were calibrated on historical chemical space and fail to recognize the unconventional scaffolds produced by modern generative models. Consequently, structurally implausible or pharmacologically irrelevant molecules can still achieve high "drug-like" scores. (ii) Oversimplification: QED relies on only seven physicochemical descriptors, and its average value for DrugBank [17] molecules is below 0.5, illustrating its limited discriminative power.

To close this gap, we introduce a broader evaluation framework comprising two complementary tiers. Structural reasonability screens for fundamental medicinal-chemistry principles such as aromaticity, ring-system stability, and hybridization consistency, while physicochemical and pharmacokinetic suitability evaluates absorption, distribution, metabolism, excretion, and toxicity (ADME/T) properties using established descriptors. Together, these tiers ensure that generated molecules are both chemically plausible and therapeutically relevant, providing a more reliable benchmark for modern AI-driven molecular design.

Molecular Reasonability Ratio. To address the lack of metrics capable of identifying the structural gap between generated molecules and rationally designed drugs, we introduce MRR as a targeted solution. MRR is a rule-based, empirically motivated metric designed to flag structures that are uncommon in medicinal chemistry practice. Its design is informed by expert analyses of SBDD outputs, which consistently reveal a predominant failure mode: the improper use of ring conjugation—particularly aromaticity—that often deviates from patterns observed in clinically validated drugs.

MRR operates by analyzing the hybridization states of atoms within a molecule. It sequentially excludes fully aromatic or fully saturated rings and focuses on the remaining atoms within each ring system. After removing peripheral substituents, if the hybridization states of the residual ring atoms are neither all $\operatorname { s p } ^ { 2 }$ nor all $\displaystyle { \mathsf { s p } } ^ { 3 }$ , the structure is classified as chemically unreasonable. For example, structures such as cyclohexene and cyclohexa-1,3-diene are flagged, as they likely result from the model’s failure to correctly generate either fully aromatic or fully saturated systems. Although not intended as an exhaustive classifier, MRR provides an interpretable, medicinal-chemistry-guided screen that complements basic valence checks and ADME filters, thereby reducing the incidence of structurally implausible candidates generated by models. The full algorithm for MRR is shown in Appendix D.

QikProp Multiple Property Requirements. To further evaluate the physicochemical and pharmacokinetic properties of the generated molecules, we employ QikProp [30], a tool recognized for its robust performance in predicting molecular drug-likeness properties [16]. The assessed properties include aqueous solubility, lipophilicity, polar surface area (PSA), the number of metabolizable sites, and oral absorption. Detailed requirements for each property are provided in Appendix E.

A molecule is considered to have passed the evaluation if it satisfies all N predefined property requirements: $P _ { 1 } , P _ { 2 } , \dots , P _ { N }$ . If any of the properties fall outside the acceptable range, the molecule is classified as failing.

$$
\text { QikProp } = \left\{ \begin{array}{l l} 1 & \text { if   } P _ {1} \wedge P _ {2} \wedge \dots \wedge P _ {N} \text {   are   satisfied }, \\ 0 & \text { otherwise }. \end{array} \right.
$$

# 3.2 Bridging the Gap with CIDD framework

We propose the Collaborative Intelligence Drug Design (CIDD) framework (Figure 2), a modular system for target-specific molecule generation that combines 3D interaction modeling with LLMenhanced molecular design. It consists of two components: the Structure-Based Interaction Generator (SBIG) and the LLM-Enhanced Drug Designer (LEDD).

SBIG uses 3D generative models to produce interaction-oriented molecular structures—intermediates that fit the protein pocket but might be chemically incomplete.

LEDD then refines these raw proposals into drug-like molecules using LLMs. The whole process is formalized as:

$$
x _ {0} = \operatorname{SBIG} (T a r g e t), \quad x = \operatorname{LEDD} (x _ {0}, T a r g e t)
$$

Here, $x _ { 0 }$ encodes the intended spatial interactions, and LEDD completes it into a chemically valid, synthetically accessible compound x. A key limitation of prior approaches is the absence of ground-truth mappings from interaction scaffolds to drug-like molecules, making supervised training infeasible. Traditional generative models—based on direct optimization or limited heuristics—struggle to bridge this gap. In contrast, LEDD leverages the implicit drug-relevant knowledge embedded in largescale pretrained LLMs. With strong instruction-following, reasoning, and coordination abilities, the LLM enables design decisions that generate molecules without incurring the typical trade-offs between potency and drug-likeness in drug design.

![](images/80d0771b998e91f9719407159775a28a0a5f2ee8d60e6c9547264b06833e300b.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["Structure-Based Interaction Generator (SBIG)"] --> B["LLM-Enhanced Drug Designer (LEDD)"]
    B --> C["LEDD Generation"]
    C --> D["Step 1: Interaction-Critical Fragment Identification"]
    C --> E["Step 2: Detection of Unfavorable or Atypical Substructures"]
    C --> F["Step 3: Strategic Design Planning"]
    C --> G["Step 4: Generate Molecule based on Design"]
    
    subgraph_A["Structure-Based Interaction Generator (SBIG)"]
        H["CIDD input"] --> I["Deep Generative Model"]
        I --> J["Raw molecules"]
        J --> K["Design"]
        K --> L["Reflection"]
        L --> M["Selection"]
        M --> N["CIDD output"]
    end
    
    subgraph_B["LLM-Enhanced Drug Designer (LEDD)"]
        O["Design"] --> P["Reflection"]
        P --> Q["Design"]
        Q --> R["Selection"]
        R --> S["CIDD output"]
    end
    
    subgraph_C["LEDD Generation"]
        T["Step 1: Interaction-Critical Fragment Identification"] --> U["Step 2: Detection of Unfavorable or Atypical Substructures"]
        U --> V["Step 3: Strategic Design Planning"]
        V --> W["Step 4: Generate Molecule based on Design"]
        W --> X["CIDD output"]
    end
    
    subgraph_D["LEDD Generation"]
        Y["Step 1: Interaction-Critical Fragment Identification"] --> Z["Step 2: Detection of Unfavorable or Atypical Substructures"]
        Z --> AA["Step 3: Strategic Design Planning"]
        AA --> AB["Step 4: Generate Molecule based on Design"]
        AB --> AC["CIDD output"]
    end
    
    subgraph_E["LEDD Generation"]
        AD["Step 1: Interaction-Critical Fragment Identification"] --> AE["Step 2: Detection of Unfavorable or Atypical Substructures"]
        AE --> AF["Step 3: Strategic Design Planning"]
        AF --> AG["Step 4: Generate Molecule based on Design"]
        AG --> AH["CIDD output"]
    end
    
    subgraph_F["LEDD Generation"]
        AI["Step 1: Interaction-Critical Fragment Identification"] --> AJ["Step 2: Detection of Unfavorable or Atypical Substructures"]
        AJ --> AK["Step 3: Strategic Design Planning"]
        AK --> AL["Step 4: Generate Molecule based on Design"]
        AL --> AM["CIDD output"]
    end
    
    subgraph_G["LEDD Generation"]
        AN["Step 1: Interaction-Critical Fragment Identification"] --> AO["Step 2: Detection of Unfavorable or Atypical Substructures"]
        AO --> AP["Step 3: Strategic Design Planning"]
        AP --> AQ["Step 4: Generate Molecule based on Design"]
        AQ --> AR["CIDD output"]
    end
```
</details>

Figure 2: Overview of the CIDD framework. Top: end-to-end pipeline integrating SBIG and LEDD. Bottom: detailed view of LEDD’s LLM-based design process, which designs and generates molecules through interaction analysis, reflection, and Chain-of-Thought-driven reasoning.

The CIDD framework is inspired by the real-world workflow of medicinal chemists, who begin by identifying key interaction patterns between a ligand and its target, and then construct molecules that retain these interactions while satisfying broader drug development constraints. CIDD formalizes this reasoning process: SBIG captures spatial interaction intent, while LEDD—powered by LLMs—assumes the role of a virtual chemist to transform raw scaffolds into viable drug-like molecules. By leveraging the LLM’s instruction-following and general knowledge, CIDD effectively substitutes human expertise in the molecule design process.

# 3.2.1 Pipeline Overview

CIDD decomposes the complex task of drug-oriented molecule generation into a structured pipeline of modular reasoning steps. It begins with SBIG, which generates interaction-focused intermediate structures conditioned on the target pocket. These intermediates are passed to the Interaction Analysis Module, which extracts fragment-level binding profiles using docking, fragmentation, and rule-based NCI detection. The Design Module then interprets these profiles to generate chemically plausible molecules that maintain critical interaction motifs. Each design is re-evaluated, and its updated interaction profile is processed by the Reflection Module, which compares successive design states and produces feedback for new designs. After generating $N$ new candidates, the Selection Module ranks all candidates based on their interaction quality and chemical viability, selecting the final molecule for downstream use. This modular pipeline mirrors expert workflows and enables interpretable, multi-stage control over both structural interaction and chemical relevance.

# 3.2.2 Interaction Analysis Module

This module evaluates the molecular interaction between a candidate molecule $x _ { i }$ and a target protein pocket $P$ . The process begins by re-docking $x _ { i }$ into the binding site of $P$ to generate a protein–ligand complex conformation. The molecule $x _ { i }$ is then decomposed into chemically meaningful fragments via the BRICS algorithm [6], enabling fragment-level attribution of interaction features.

Next, non-covalent interactions (NCIs), such as hydrogen bonding, $\pi { - } \pi$ stacking, salt bridges, and hydrophobic contacts, are identified from the docked complex based on geometric and chemical features. The resulting interaction map—capturing both atomic contacts and fragment-level organization—is then analyzed by an interaction-specialized large language model, $L L M _ { I }$ . Conditioned on spatial interaction cues and chemical context, $L L M _ { I }$ synthesizes this information into a structured interaction profile $I _ { i }$ , which semantically links molecular fragments to their respective roles in target engagement.

Formally, the process can be represented as:

$$
\mathrm{LLM} _ {I} (x _ {i}, P) \rightarrow I _ {i}
$$

The resulting profile $I _ { i }$ provides fragment-level interpretation of binding contributions and serves as the basis for chemically informed design in subsequent modules.

# 3.2.3 Design Module

Given a raw molecule $x _ { 0 } .$ , its interaction report $I _ { 0 }$ , and prior feedback from the reflection module $R = \{ R _ { 1 } , R _ { 2 } , . . . , R _ { i - 1 } \}$ , the Design Module leverages an LLM with a Design role $( L L M _ { D } )$ to produce a refinement plan $D _ { i }$ and an updated molecule $x _ { i }$ .

$$
L L M _ {D} (x _ {0}, I _ {0}, R) \rightarrow (D _ {i}, x _ {i})
$$

Here, $D _ { i }$ is a structured and interpretable set of design decisions grounded in medicinal chemistry, and $x _ { i }$ is the generated compound for further evaluation.

To emulate real-world drug design workflows, we implement a Chain-of-Thought prompting strategy that guides the LLM through a domain-informed reasoning pipeline with four sequential stages. (1) Interaction-Critical Fragment Identification: the model analyzes $x _ { 0 }$ and highlights fragments forming key non-covalent interactions with the target, based on ${ \bar { I } } _ { 0 } .$ . (2) Detection of Unfavorable or Atypical Substructures: chemically undesirable fragments—such as synthetically inaccessible motifs, strained rings, or poor physicochemical regions—are flagged for replacement. (3) Strategic Design Planning: the model proposes modifications that improve chemical viability while preserving interaction and topology, often substituting problematic regions with pharmaceutically preferred alternatives. (4) Candidate Molecule Generation: a new structure $x _ { i }$ is generated based on the design plan, ensuring both target interaction and drug-like properties.

By encoding expert priors into the prompt structure, the Design Module reframes molecule generation as a chemically grounded reasoning task. The LLM is able to coordinate multiple design objectives within a unified framework. This enables the CIDD to effectively mitigate the trade-offs between affinity and drug-likeness that commonly arise in drug design. It bridges raw interaction scaffolds to viable candidate molecules in a transparent and interpretable manner.

# 3.2.4 Reflection and Selection Modules

The Reflection Module evaluates whether each candidate design $x _ { i }$ achieves design goals by comparing it to the initial raw molecule $x _ { 0 }$ and their respective interaction profiles:

$$
L L M _ {R} (x _ {0}, I _ {0}, D _ {i}, x _ {i}, I _ {i}) \rightarrow R _ {i}
$$

The Selection Module evaluate all the designed molecules $\{ x _ { 1 } , x _ { 2 } , \ldots , x _ { N } \}$ and their interaction reports to identify the most promising candidate:

$$
L L M _ {S} \left(\left\{\left(x _ {1}, I _ {1}\right), \dots , \left(x _ {N}, I _ {N}\right)\right\}\right)\rightarrow x _ {\text { best }}
$$

Here, $x _ { \mathrm { b e s t } }$ balances interaction quality and chemical viability. Full prompt examples for each module are in Appendix C.

# 4 Experiments

# 4.1 Experiment Settings

Dataset. We follow prior 3D-SBDD settings and use the CrossDocked2020 dataset [9], adopting the same train/test split as TargetDiff [12], resulting in 100 protein pockets for test.

Metrics. We evaluate models using standard metrics: Vina docking score [34] for binding affinity, QED [3] for drug-likeness, SA score [8] for synthetic accessibility, and molecular diversity (computed as 1 − ECFP4 similarity [29]) for structural variety. As we do not directly generate 3D conformations,

Vina Score/Min is excluded. Beyond conventional metrics, we emphasize the evaluation of drug potential via two additional metrics: MRR (Molecular Rule-based Reasonability), which captures domain-informed structural plausibility, and QikProp pass ratio, which assesses a wide range of physicochemical and pharmacokinetic properties. Together with QED and SA, these offer a more holistic assessment of molecular viability. We also report the success ratio, defined as the percentage of molecules that satisfy all of the following criteria: Vina < −8.18, QED > 0.25, and SA > 0.59, following [23]. In addition, we introduce molecular reasonability as an extra constraint for defining success. We also evaluate the proportion of molecules that pass all QikProp filters.

Baseline Models. We compare CIDD against a diverse set of 3D-SBDD baselines spanning multiple generative paradigms: the VAE-based LiGAN [27]; autoregressive models AR [24] and Pocket2Mol [25]; and diffusion-based approaches including TargetDiff [12], IPDiff [15], DecompDiff [13], and TAGMol [7]. IPDiff uses interaction-guided sampling, while DecompDiff leverages interaction-aware priors; TAGMol adds gradient-based optimization for drug-likeness. We also evaluate DrugGPS [37], a fragment-based method, and MolCRAFT [26], a Bayesian flow network shown to be state-of-the-art in recent benchmarks [19, 10].

CIDD Settings. We use MolCRAFT in the SBIG step. All modules in the LEDD step are powered by GPT-4o. The Design Module generates 5 candidates per round, and the Selection Module selects the final molecule. For each protein pocket, we generate 10 molecules. All SBIG models are trained on CrossDocked2020 with their released weights.

# 4.2 General Results

As shown in Table 1, CIDD demonstrates strong overall performance across key drug-likeness metrics—including QED, MRR, SA, and QikProp pass ratio—as well as favorable binding affinity. In comparison, IPDiff, which leverages a trained binding affinity predictor to guide both training and sampling, achieves some improvement in docking scores over TargetDiff. However, it performs worse in terms of MRR, highlighting the potential limitations of focusing solely on binding affinity. Similarly, the gradient-guided method TAGMol aims to enhance multiple properties through predictor guidance during sampling. While TAGMol shows notable improvements in QED, it brings minimal gains and still performs badly in metrics such as MRR and SA, performing comparably to the unguided diffusion model TargetDiff. This suggests that optimization-driven approaches like TAGMol may overfit individual scoring functions rather than learning to generate molecules with generally improved drug-like profiles. In contrast, CIDD delivers consistent improvements across all major drug-likeness dimensions, indicating a more robust and comprehensive molecular design capability. These results stem from CIDD’s ability to integrate the complementary strengths of distinct modeling

Table 1: Test Results on CrossDocked2020. We benchmark several evaluation metrics, including Vina docking score, QED, SA, MRR, success ratio, and QikProp pass ratio. We also report the average molecular weight. Performance ranking per column is color-coded as follows: best , second-best 

<table><tr><td>Category</td><td>Method</td><td>Vina ↓</td><td>QED ↑</td><td>SA ↑</td><td>MRR ↑</td><td>Success ↑</td><td>QikProp ↑</td><td>MW</td></tr><tr><td>VAE-based</td><td>LiGAN</td><td>-6.640</td><td>0.394</td><td>0.601</td><td>59.08%</td><td>2.79%</td><td>17.37%</td><td>286.44</td></tr><tr><td>AR-based</td><td>AR</td><td>-6.737</td><td>0.507</td><td>0.635</td><td>56.67%</td><td>3.28%</td><td>18.66%</td><td>247.50</td></tr><tr><td>AR-based</td><td>Pocket2Mol</td><td>-7.246</td><td>0.573</td><td>0.758</td><td>67.88%</td><td>14.60%</td><td>29.58%</td><td>234.30</td></tr><tr><td>Diffusion-based</td><td>TargetDiff</td><td>-7.452</td><td>0.474</td><td>0.579</td><td>37.81%</td><td>3.04%</td><td>27.63%</td><td>346.24</td></tr><tr><td>Diff + Inter-Guide</td><td>IPDiff</td><td>-7.745</td><td>0.511</td><td>0.627</td><td>29.83%</td><td>5.31%</td><td>25.11%</td><td>328.34</td></tr><tr><td>Diff + Inter-Prior</td><td>DecompDiff</td><td>-8.260</td><td>0.444</td><td>0.609</td><td>62.60%</td><td>15.72%</td><td>29.04%</td><td>424.09</td></tr><tr><td>Diff + Multi-Guide</td><td>TAGMol</td><td>-7.563</td><td>0.563</td><td>0.583</td><td>37.31%</td><td>3.23%</td><td>32.31%</td><td>325.50</td></tr><tr><td>Fragment-based</td><td>DrugGPS</td><td>-7.396</td><td>0.463</td><td>0.622</td><td>54.80%</td><td>7.17%</td><td>25.60%</td><td>329.88</td></tr><tr><td>BFN-based</td><td>MolCRAFT</td><td>-7.783</td><td>0.503</td><td>0.685</td><td>58.47%</td><td>13.72%</td><td>22.37%</td><td>325.63</td></tr><tr><td>3DSBDD + LLM</td><td>CIDD</td><td>-8.496</td><td>0.576</td><td>0.735</td><td>81.74%</td><td>34.59%</td><td>35.22%</td><td>336.70</td></tr></table>

paradigms—combining the strong binding affinity modeling capability of 3D generative models with the drug-likeness reasoning and instruction-following power of large language models. Guided by expert-designed prompts and leveraging the LLM’s embedded chemical knowledge, CIDD refines molecular structures toward realistic and pharmacologically meaningful candidates. As a result, it achieves a significantly higher success ratio of 34.59%, compared to 15.72% for the best baseline—demonstrating its unique capacity to generate molecules that are not only strong binders, but also truly drug-like and synthetically feasible. Interestingly, CIDD achieves comparable QED and SA scores, while significantly outperforming Pocket2Mol in MRR, despite generating molecules that are approximately 50% larger on average in terms of molecular weight (336.70 vs. 234.30). Moreover, it achieves a substantially better docking score. This result provides strong evidence that CIDD is capable of generating larger molecules that are still drug-like, suggesting that its strong performance on drug-likeness metrics is not simply a result of hacking these metrics by producing smaller, simpler molecules.

![](images/286e22bb1e996e4576474a13da62a307ee9638e11e35796334d4a77813dbb26b.jpg)

<details>
<summary>bar</summary>

| Category     | with LEDD (Darker Shade) | SBIG only (Lighter Shade) |
| ------------ | ------------------------ | ------------------------- |
| pocket2mol   | 19.4%                    |                           |
| targetdiff   |                          | 31.4%                     |
| decompdiff   |                          | 13.7%                     |
| molcraft     |                          | 14.7%                     |
</details>

(a) QED

![](images/090a59e1436de6147043677854225fe02299a45e1c100a70310230213e91d438.jpg)

<details>
<summary>bar</summary>

| Method | with LEDD (Darker Shade) (%) | SBIG only (Lighter Shade) (%) |
| :--- | :--- | :--- |
| pocket2mol | 3.4 | 0.75 |
| targetdiff | 20.0 | 0.58 |
| decompdiff | 13.8 | 0.61 |
| molcraft | 7.6 | 0.69 |
</details>

(b) SA Score

![](images/47e02d6fbbafa0960d8a52917cbd421ef6f203314ee6ef4d67533a6f0d6ed9ae.jpg)

<details>
<summary>bar</summary>

| Category     | with LEDD (Darker Shade) | SBIG only (Lighter Shade) |
| ------------ | ------------------------ | ------------------------- |
| pocket2mol   | 25.3%                    | 85.2%                     |
| targetdiff   | 15.3%                    | 64.5%                     |
| decompdiff   | 39.2%                    | 64.5%                     |
| molcraft     | 39.2%                    | 64.5%                     |
</details>

(c) Reasonable Ratio

![](images/64b3e22b25fe3580141577b1094565b856cbbb87ce8ccb7b085e4ebfecb3203d.jpg)

<details>
<summary>bar</summary>

| Category     | with LEDD (Darker Shade) | SBIG only (Lighter Shade) |
| ------------ | ------------------------ | ------------------------- |
| pocket2mol   | 92.6%                    |                           |
| targetdiff   | 102.8%                   |                           |
| decompdiff   | 29.3%                    |                           |
| molcraft     | 57.4%                    |                           |
</details>

(d) QikProp Pass Ratio   
Figure 3: Performance comparison across different metrics indicative of drug potential between models using only SBIG outputs and those incorporating LEDD outputs, evaluated across various 3D-SBDD models as the SBIG module.

# 4.3 Improvements with Different Models on Multiple Metrics

CIDD is a flexible framework designed to interface smoothly with a broad spectrum of 3D SBDD models, significantly enhancing the quality of generated molecules. As illustrated in Figure 3, CIDD brings substantial and consistent improvements across key drug-likeness metrics—including QED, SA Score, Reasonable Ratio, and QikProp Pass Ratio—achieving gains of 31.4%, 20.0%, 85.2%, and 102.8%, respectively. These improvements are observed across different base models, demonstrating CIDD’s strong generalization ability and its capacity to enhance diverse, diverse aspects of druglikeness simultaneously. In contrast to optimization-based methods that often overfit individual metrics, CIDD drives broad and meaningful improvements that reflect a true advancement in the quality of generated drug candidates.

# 4.4 Ablation and Analysis

Table 2: Ablation studies on LLM variants and pure LLM-based SBDD.   
(a) Different LLM Backends in CIDD 

<table><tr><td>LLM</td><td>Vina↓</td><td>MRR↑</td><td>Similarity↑</td></tr><tr><td>-</td><td>-7.78</td><td>58.47%</td><td>-</td></tr><tr><td>GPT-4o-mini</td><td>-8.29</td><td>80.02%</td><td>0.220</td></tr><tr><td>GPT-4o</td><td>-8.50</td><td>81.37%</td><td>0.296</td></tr><tr><td>DeepSeek-v3</td><td>-8.49</td><td>76.00%</td><td>0.379</td></tr><tr><td>DeepSeek-r1</td><td>-8.57</td><td>79.17%</td><td>0.182</td></tr></table>

(b) LLM-Only vs. CIDD Comparison 

<table><tr><td></td><td>Vina↓</td><td>MRR↑</td><td>Success Ratio↑</td></tr><tr><td>LLM-SBDD</td><td>-6.244</td><td>97.45%</td><td>5.95%</td></tr><tr><td>CIDD-LLM</td><td>-7.230</td><td>90.97%</td><td>17.59%</td></tr><tr><td>CIDD</td><td>-8.496</td><td>81.74%</td><td>35.22%</td></tr></table>

# 4.4.1 Impact of Different LLMs

We evaluate GPT-4o, GPT-4o-mini, DeepSeek-v3 [5], and DeepSeek-r1 [14] using MolCRAFT as the SBIG module (Table 2a). All models improve drug-likeness metrics (MRR, QikProp) and docking scores. DeepSeek-v3 achieves property gains with minimal edits, while GPT-4o-mini struggles with similarity, and DeepSeek-r1 makes broader, less controllable changes. GPT-4o and DeepSeek-v3 best support CIDD’s goal of generating similar yet improved molecules. Smaller models like LLAMA-7B fail to follow design instructions. CIDD remains plug-and-play, benefiting from future LLM advances.

![](images/d22bb6ea791705d37ed955a28cd8f6de9850b8052ecfe9878108ff85ca6a3a5c.jpg)

(b)   
![](images/77f69ba79a99faacd91882a59511b5322d5c11e47cac208f14e55568671b5c27.jpg)

<details>
<summary>bar_line</summary>

| Number of Previous Experiences | Success Ratio (Bar) (%) | Success Ratio (Line) (%) |
| :--- | :--- | :--- |
| 0 | 30.5 | 30.5 |
| 5 | 31.2 | 31.2 |
| 10 | 33.0 | 33.0 |
| 15 | 36.4 | 36.4 |
</details>

（c）

![](images/4ccf9d39732180cf93ae525cba8a601ea255a6151dbc6029c7609e917ebae34f.jpg)

<details>
<summary>line</summary>

| Point Label | Description |
| --- | --- |
| Drug-Likeness | i. QED/SA/Rule of Five ii. Physiochemical; iii. Biological |
| Rapid Output | Gap/ Misalignment |
| Rapid Impact | Traditional Hit-to-lead |
| Rapid Release | Widely Accessible Molecules (Structures Preferred by Chemists) |
| Rapid End | CIDD |
| Rapid Target | Potency ΔG = ΔH - TΔS; Estimated by Vina |
</details>

Figure 4: (a) A generation case and corresponding interpretable design strategy produced by CIDD, resulting in a structurally similar yet better compound. (b) CIDD demonstrates the ability to evolve by leveraging previous design experiences as context, improving generation success rates. (c) CIDD integrates the strengths of 3D-SBDD models and LLMs to enable practical drug design with both high potency and drug-likeness.

# 4.4.2 Using Pure LLM for SBDD

LLMs alone struggle with 3D protein pocket interpretation in structure-based drug design (SBDD). To test this, we prompted an LLM with PDB-format pocket data and also evaluated CIDD-LLM, which uses LLM-SBDD within the CIDD framework. As shown in Table 2b, LLM-SBDD generates chemically reasonable molecules but performs poorly on binding affinty, leading to a lower success rate than standard CIDD. This highlights the need for combining 3D models’ interaction modeling with LLMs’ reasoning.

# 4.5 Advantages and Impact of the CIDD Framework

Interpretable Molecule Design. Figure 4a illustrates the CIDD generation process. The LLMpowered modules analyze and refine the raw supporting molecule (green), producing a high-quality final structure (blue). Problematic fragments—such as an unreasonable diene or an uncommon fluorinated chain—are automatically identified and replaced (e.g., with a benzene ring), while side chains are adjusted to preserve key hydrogen bonds with Gln316 on both Chain A and B. These edits improve docking scores and enhance drug-relevant properties. CIDD performs this refinement through localized fragment substitutions, maintaining the core structure while improving overall drug potential. Notably, the process is inherently interpretable: each design step is traceable, with explicit rationales highlighting structural strengths and weaknesses. This transforms conventional opaque SBDD into a transparent, expert-assisting workflow. CIDD also enables the automated creation of molecule pairs that differ in drug-likeness with minimal structural edits. These pairs effectively capture how small chemical changes influence pharmaceutical viability, offering highquality, distributionally aligned data for fine-tuning. Compared to random sampling, they provide more meaningful supervision and help mitigate data scarcity in 3D-SBDD (see Appendix H).

Evolvement Ability. One key advantage of LLMs is their ability to leverage prior experience, provided as context, to generate insightful outputs. To illustrate this, we conducted a proof-of-concept experiment using a relatively lightweight LLM: GPT-4o-mini. The model was given varying numbers of previous design reports and results (0, 5, 10, and 15) as contextual input and tasked with generating insights to support the design module of CIDD. As shown in Figure 4b, the success rate improved as more prior reports were included. These results demonstrate CIDD’s capacity for continual evolution by incorporating accumulated experience—without requiring model retraining. This mirrors the way human experts enhance their performance through repeated exposure and practice.

Generating Small Molecules with Both High Potency and Drug-Likeness. Drug potential hinges on two key factors: potency and drug-likeness. While most 3D-SBDD models emphasize target fit, they often produce chemically unreasonable structures. As shown in Figure 4c, our CIDD framework bridges this gap by combining geometric modeling with LLM-driven reasoning. The LLM not only corrects unfavorable fragments but also plans coherent molecular edits that balance multiple objectives. By coordinating spatial and chemical constraints within a unified generation process, CIDD effectively overcomes the traditional trade-off between interaction strength and drug-likeness.

# 5 Conclusion

We presented CIDD, a collaborative framework that unifies 3D interaction modeling and LLM-driven reasoning for structure-based drug design. CIDD addresses a key limitation of current generative models: the tendency to generate interaction-compatible but chemically unreasonable molecules. Through a modular, interpretable generation process, CIDD achieves state-of-the-art results on the CrossDocked2020 benchmark—substantially improving drug-likeness metrics (QED, SA, MRR, QikProp) while maintaining high binding affinity. By bridging 3D geometric modeling with languageguided design, our approach sets a foundation for future directions in rational, interpretable, and generalizable drug generation. We envision such a collaborative paradigm enabling broader tasks such as target discovery and hit-to-lead optimization in early-stage drug discovery.

# Acknowledgements

This work is supported by Beijing Academy of Artificial Intelligence and Beijing Frontier Research Center for Biological Structure Fundings.

# References

[1] Asad Aali, Adney Cardoza, and Melissa Capo. Splitwiser: Efficient lm inference with constrained resources. arXiv preprint arXiv:2505.03763, 2025.   
[2] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. arXiv preprint arXiv:2303.08774, 2023.   
[3] G Richard Bickerton, Gaia V Paolini, Jérémy Besnard, Sorel Muresan, and Andrew L Hopkins. Quantifying the chemical beauty of drugs. Nature chemistry, 4(2):90–98, 2012.   
[4] Chiranjib Chakraborty, Manojit Bhattacharya, and Sang-Soo Lee. Artificial intelligence enabled chatgpt and large language models in drug target discovery, drug discovery, and development. Molecular Therapy-Nucleic Acids, 33:866–868, 2023.   
[5] DeepSeek-AI, Aixin Liu, Bei Feng, Bing Xue, Bingxuan Wang, Bochao Wu, Chengda Lu, Chenggang Zhao, Chengqi Deng, Chenyu Zhang, Chong Ruan, Damai Dai, Daya Guo, Dejian Yang, Deli Chen, Dongjie Ji, Erhang Li, Fangyun Lin, Fucong Dai, Fuli Luo, Guangbo Hao, Guanting Chen, Guowei Li, H. Zhang, Han Bao, Hanwei Xu, Haocheng Wang, Haowei Zhang, Honghui Ding, Huajian Xin, Huazuo Gao, Hui Li, Hui Qu, J. L. Cai, Jian Liang, Jianzhong Guo, Jiaqi Ni, Jiashi Li, Jiawei Wang, Jin Chen, Jingchang Chen, Jingyang Yuan, Junjie Qiu, Junlong Li, Junxiao Song, Kai Dong, Kai Hu, Kaige Gao, Kang Guan, Kexin Huang, Kuai Yu, Lean Wang, Lecong Zhang, Lei Xu, Leyi Xia, Liang Zhao, Litong Wang, Liyue Zhang, Meng Li, Miaojun Wang, Mingchuan Zhang, Minghua Zhang, Minghui Tang, Mingming Li, Ning Tian, Panpan Huang, Peiyi Wang, Peng Zhang, Qiancheng Wang, Qihao Zhu, Qinyu Chen, Qiushi Du, R. J. Chen, R. L. Jin, Ruiqi Ge, Ruisong Zhang, Ruizhe Pan, Runji Wang, Runxin Xu, Ruoyu Zhang, Ruyi Chen, S. S. Li, Shanghao Lu, Shangyan Zhou, Shanhuang Chen, Shaoqing Wu, Shengfeng Ye, Shengfeng Ye, Shirong Ma, Shiyu Wang, Shuang Zhou, Shuiping Yu, Shunfeng Zhou, Shuting Pan, T. Wang, Tao Yun, Tian Pei, Tianyu Sun, W. L. Xiao, Wangding Zeng, Wanjia Zhao, Wei An, Wen Liu, Wenfeng Liang, Wenjun Gao, Wenqin Yu, Wentao Zhang, X. Q. Li, Xiangyue Jin, Xianzu Wang, Xiao Bi, Xiaodong Liu, Xiaohan Wang, Xiaojin Shen, Xiaokang Chen, Xiaokang Zhang, Xiaosha Chen, Xiaotao Nie, Xiaowen Sun, Xiaoxiang Wang, Xin Cheng, Xin Liu, Xin Xie, Xingchao Liu, Xingkai Yu, Xinnan Song, Xinxia Shan, Xinyi

Zhou, Xinyu Yang, Xinyuan Li, Xuecheng Su, Xuheng Lin, Y. K. Li, Y. Q. Wang, Y. X. Wei, Y. X. Zhu, Yang Zhang, Yanhong Xu, Yanhong Xu, Yanping Huang, Yao Li, Yao Zhao, Yaofeng Sun, Yaohui Li, Yaohui Wang, Yi Yu, Yi Zheng, Yichao Zhang, Yifan Shi, Yiliang Xiong, Ying He, Ying Tang, Yishi Piao, Yisong Wang, Yixuan Tan, Yiyang Ma, Yiyuan Liu, Yongqiang Guo, Yu Wu, Yuan Ou, Yuchen Zhu, Yuduan Wang, Yue Gong, Yuheng Zou, Yujia He, Yukun Zha, Yunfan Xiong, Yunxian Ma, Yuting Yan, Yuxiang Luo, Yuxiang You, Yuxuan Liu, Yuyang Zhou, Z. F. Wu, Z. Z. Ren, Zehui Ren, Zhangli Sha, Zhe Fu, Zhean Xu, Zhen Huang, Zhen Zhang, Zhenda Xie, Zhengyan Zhang, Zhewen Hao, Zhibin Gou, Zhicheng Ma, Zhigang Yan, Zhihong Shao, Zhipeng Xu, Zhiyu Wu, Zhongyu Zhang, Zhuoshu Li, Zihui Gu, Zijia Zhu, Zijun Liu, Zilin Li, Ziwei Xie, Ziyang Song, Ziyi Gao, and Zizheng Pan. Deepseek-v3 technical report, 2024.   
[6] Jorg Degen, Christof Wegscheid-Gerlach, Andrea Zaliani, and Matthias Rarey. On the art of compiling and using’drug-like’chemical fragment spaces. ChemMedChem, 3(10):1503, 2008.   
[7] Vineeth Dorna, D Subhalingam, Keshav Kolluru, Shreshth Tuli, Mrityunjay Singh, Saurabh Singal, NM Krishnan, and Sayan Ranu. Tagmol: Target-aware gradient-guided molecule generation. arXiv preprint arXiv:2406.01650, 2024.   
[8] Peter Ertl and Ansgar Schuffenhauer. Estimation of synthetic accessibility score of drug-like molecules based on molecular complexity and fragment contributions. Journal of cheminformatics, 1:1–11, 2009.   
[9] Paul G Francoeur, Tomohide Masuda, Jocelyn Sunseri, Andrew Jia, Richard B Iovanisci, Ian Snyder, and David R Koes. Three-dimensional convolutional neural networks and a crossdocked data set for structure-based drug design. Journal of chemical information and modeling, 60(9):4200–4215, 2020.   
[10] Bowen Gao, Haichuan Tan, Yanwen Huang, Minsi Ren, Xiao Huang, Wei-Ying Ma, Ya-Qin Zhang, and Yanyan Lan. Reframing structure-based drug design model evaluation via metrics correlated to practical needs. In The Thirteenth International Conference on Learning Representations.   
[11] Team GLM, Aohan Zeng, Bin Xu, Bowen Wang, Chenhui Zhang, Da Yin, Dan Zhang, Diego Rojas, Guanyu Feng, Hanlin Zhao, et al. Chatglm: A family of large language models from glm-130b to glm-4 all tools. arXiv preprint arXiv:2406.12793, 2024.   
[12] Jiaqi Guan, Wesley Wei Qian, Xingang Peng, Yufeng Su, Jian Peng, and Jianzhu Ma. 3d equivariant diffusion for target-aware molecule generation and affinity prediction. arXiv preprint arXiv:2303.03543, 2023.   
[13] Jiaqi Guan, Xiangxin Zhou, Yuwei Yang, Yu Bao, Jian Peng, Jianzhu Ma, Qiang Liu, Liang Wang, and Quanquan Gu. Decompdiff: diffusion models with decomposed priors for structurebased drug design. arXiv preprint arXiv:2403.07902, 2024.   
[14] Daya Guo, Dejian Yang, Haowei Zhang, Junxiao Song, Ruoyu Zhang, Runxin Xu, Qihao Zhu, Shirong Ma, Peiyi Wang, Xiao Bi, et al. Deepseek-r1: Incentivizing reasoning capability in llms via reinforcement learning. arXiv preprint arXiv:2501.12948, 2025.   
[15] Zhilin Huang, Ling Yang, Xiangxin Zhou, Zhilong Zhang, Wentao Zhang, Xiawu Zheng, Jie Chen, Yu Wang, Bin Cui, and Wenming Yang. Protein-ligand interaction prior for bindingaware 3d molecule diffusion models. In The Twelfth International Conference on Learning Representations, 2024.   
[16] Leukothea Ioakimidis, Loizos Thoukydidis, Amin Mirza, Saira Naeem, and Johannes Reynisson. Benchmarking the reliability of qikprop. correlation between experimental and predicted values. QSAR & Combinatorial Science, 27(4):445–456, 2008.   
[17] Craig Knox, Mike Wilson, Christen M Klinger, Mark Franklin, Eponine Oler, Alex Wilson, Allison Pon, Jordan Cox, Na Eun Chin, Seth A Strawbridge, et al. Drugbank 6.0: the drugbank knowledgebase for 2024. Nucleic acids research, 52(D1):D1265–D1275, 2024.

[18] Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph Gonzalez, Hao Zhang, and Ion Stoica. Efficient memory management for large language model serving with pagedattention. In Proceedings of the 29th symposium on operating systems principles, pages 611–626, 2023.   
[19] Haitao Lin, Guojiang Zhao, Odin Zhang, Yufei Huang, Lirong Wu, Zicheng Liu, Siyuan Li, Cheng Tan, Zhifeng Gao, and Stan Z Li. Cbgbench: fill in the blank of protein-molecule complex binding graph. arXiv preprint arXiv:2406.10840, 2024.   
[20] Christopher A Lipinski, Franco Lombardo, Beryl W Dominy, and Paul J Feeney. Experimental and computational approaches to estimate solubility and permeability in drug discovery and development settings. Advanced drug delivery reviews, 64:4–17, 2012.   
[21] Aixin Liu, Bei Feng, Bin Wang, Bingxuan Wang, Bo Liu, Chenggang Zhao, Chengqi Dengr, Chong Ruan, Damai Dai, Daya Guo, et al. Deepseek-v2: A strong, economical, and efficient mixture-of-experts language model. arXiv preprint arXiv:2405.04434, 2024.   
[22] Shengchao Liu, Jiongxiao Wang, Yijin Yang, Chengpeng Wang, Ling Liu, Hongyu Guo, and Chaowei Xiao. Conversational drug editing using retrieval and domain feedback. In The twelfth international conference on learning representations, 2024.   
[23] Siyu Long, Yi Zhou, Xinyu Dai, and Hao Zhou. Zero-shot 3d drug design by sketching and generating. Advances in Neural Information Processing Systems, 35:23894–23907, 2022.   
[24] Shitong Luo, Jiaqi Guan, Jianzhu Ma, and Jian Peng. A 3d generative model for structure-based drug design. Advances in Neural Information Processing Systems, 34:6229–6239, 2021.   
[25] Xingang Peng, Shitong Luo, Jiaqi Guan, Qi Xie, Jian Peng, and Jianzhu Ma. Pocket2mol: Efficient molecular sampling based on 3d protein pockets. In International Conference on Machine Learning, pages 17644–17655. PMLR, 2022.   
[26] Yanru Qu, Keyue Qiu, Yuxuan Song, Jingjing Gong, Jiawei Han, Mingyue Zheng, Hao Zhou, and Wei-Ying Ma. Molcraft: Structure-based drug design in continuous parameter space. arXiv preprint arXiv:2404.12141, 2024.   
[27] Matthew Ragoza, Tomohide Masuda, and David Ryan Koes. Generating 3d molecules conditional on receptor binding sites with deep generative models. Chemical science, 13(9):2701– 2713, 2022.   
[28] Raimond BG Ravelli, Benoît Gigant, Patrick A Curmi, Isabelle Jourdain, Sylvie Lachkar, André Sobel, and Marcel Knossow. Insight into tubulin regulation from a complex with colchicine and a stathmin-like domain. Nature, 428(6979):198–202, 2004.   
[29] David Rogers and Mathew Hahn. Extended-connectivity fingerprints. Journal of chemical information and modeling, 50(5):742–754, 2010.   
[30] Schrödinger, LLC. QikProp. Schrödinger, LLC, New York, NY, 2025. Schrödinger Release 2021-2.   
[31] Yuxuan Song, Zheng Zhang, Cheng Luo, Pengyang Gao, Fan Xia, Hao Luo, Zheng Li, Yuehang Yang, Hongli Yu, Xingwei Qu, et al. Seed diffusion: A large-scale diffusion language model with high-speed inference. arXiv preprint arXiv:2508.02193, 2025.   
[32] Bart L Staker, Michael D Feese, Mark Cushman, Yves Pommier, David Zembower, Lance Stewart, and Alex B Burgin. Structures of three classes of anticancer agents bound to the human topoisomerase i- dna covalent complex. Journal of medicinal chemistry, 48(7):2336–2345, 2005.   
[33] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971, 2023.   
[34] Oleg Trott and Arthur J Olson. Autodock vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. Journal of computational chemistry, 31(2):455–461, 2010.

[35] Xiaolun Wang, Shelley Allen, James F Blake, Vickie Bowcut, David M Briere, Andrew Calinisan, Joshua R Dahlke, Jay B Fell, John P Fischer, Robin J Gunn, et al. Identification of mrtx1133, a noncovalent, potent, and selective krasg12d inhibitor. Journal of medicinal chemistry, 65(4):3123–3133, 2021.   
[36] Jiale Xu, Rui Zhang, Cong Guo, Weiming Hu, Zihan Liu, Feiyang Wu, Yu Feng, Shixuan Sun, Changxu Shao, Yuhong Guo, et al. vtensor: Flexible virtual tensor management for efficient llm serving. arXiv preprint arXiv:2407.15309, 2024.   
[37] Zaixi Zhang and Qi Liu. Learning subpocket prototypes for generalizable structure-based drug design. In International Conference on Machine Learning, pages 41382–41398. PMLR, 2023.

# A Discussion on the Pharmaceutical Terminology

In this work, we employ a comprehensive set of evaluation metrics—Vina, QED, SA, our proposed MRR, the Success Ratio, and QikProp—to analyze different facets of molecular generation performance. Following established practices, we use Vina scores to assess the 3D complementarity between generated molecules and their target binding sites. Meanwhile, we evaluate broader molecular properties using standard metrics (QED and SA), the domain-informed MRR, and physicochemical and pharmacokinetic descriptors from QikProp, which are widely used in computer-aided drug design (CADD).

To clarify the key concepts underpinning our evaluation framework, we distinguish among drug potential, drug-likeness, molecular reasonability, and chemical validity.

Previous studies have often focused too narrowly on geometric complementarity, overlooking other essential requirements a drug-like molecule must fulfill. We introduce the term drug potential to describe the overall suitability of a molecule as a drug candidate, encompassing not only binding affinity but also synthetic accessibility, chemical stability, pharmacokinetics (absorption, distribution, metabolism, and excretion), and safety. These properties are intrinsically determined by molecular structure and collectively influence whether a molecule can reach its intended biological target and survive the drug development process.

The term drug-likeness is widely used in medicinal chemistry to reflect the multidimensional suitability of a molecule as a drug candidate. Drug discovery and development (DDD), however, are deeply influenced by human expertise—including implicit preferences for molecular scaffolds and nuanced, often tacit, domain knowledge that is difficult to formalize or quantify. As a result, even experienced medicinal chemists struggle to define or approximate the true probability function p(drug), which represents the likelihood that a molecule will become a viable therapeutic candidate. However, the machine learning community often oversimplifies drug-likeness to metrics such as QED or Lipinski’s Rule of Five, which capture only a narrow range of basic physicochemical properties. This simplification overlooks critical factors such as oral bioavailability, metabolic stability, and toxicity risks (e.g., hERG liability).

At a more fundamental level, a molecule must be chemically valid, meaning it adheres to basic chemical rules such as proper valence and atom types. However, we observe that many modelgenerated molecules—while technically valid—contain rare or unstable structural substructures that would be flagged by human medicinal chemists. These structures are neither common nor practically accessible and thus fall outside the bounds of what is typically accepted in pharmaceutical research. Despite the central importance of this distinction, prior work has not proposed an effective metric to differentiate between chemically plausible structures and those that are formally valid but unrealistic. To fill this gap, we propose MRR, a rule-based metric that reflects medicinal chemistry heuristics. It identifies implausible features such as unstable ring systems and uncommon conjugation patterns, offering an interpretable and practical means of identifying unrealistic model outputs.

By explicitly defining these concepts and introducing MRR, we aim to guide molecular generation efforts toward pharmaceutically meaningful directions, bridging the gap between computational outputs and real-world drug development feasibility.

# B Limitations

One limitation of CIDD is its dependence on pretrained LLMs, which may occasionally introduce hallucinations in underexplored chemical regions.

# C Detailed Prompts and Responses for LEDD

In this section, we present the detailed workflow of the CIDD framework, including the prompts and example responses for each module.

Figure 5 illustrates the complete drug design pipeline. The Interaction Module first identifies key fragments within the supporting molecule that interact with the protein pocket. This information is then utilized by the Design Module, which devises strategies to replace uncommon or unfavorable fragments while preserving crucial interactions. Once a new molecule is designed, the Evaluation

Phase within the Design Module assesses its viability. Finally, the Reflection Module analyzes the design process and outcomes, highlighting both strengths and areas for improvement.

Figure 6 presents the prompt and example response for the Interaction Analysis Module.

Figures 7 and 8 display the prompt and example response for the Design Module.

Figures 9, 10, and 11 illustrate the prompt and example responses for the Reflection Module.

Figures 12 and 13 show the prompt and example response for the Selection Module.

![](images/b35ce107fa8d6cfd0fe00109e87e1f486a9250bbe49990ebedce614a6a12910f.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["SBIG"] --> B["PDB Id: 7kSI"]
    B --> C["P"]
    C --> D["x0"]
    D --> E["SBDD Model"]
    E --> F["x0"]
    F --> G["R1"]
    G --> H["Comparison to xg"]
    H --> I["Hydrogen Binding ↓"]
    I --> J["## &quot;Strengths of the Modifications&quot;"]
    J --> K["1. &quot;Improved Stability and Synthetic Accessibility&quot;..."]
    K --> L["2. &quot;Retention of Key Interaction Models&quot;"]
    L --> M["3. &quot;The reliability of complex interactions such as hydrogen bonding with HIS17 and ARG152&quot;"]
    M --> N["4. &quot;Weaknesses of the Modifications&quot;"]
    N --> O["5. &quot;Over-Simplification of the Aromatic Core&quot;"]
    O --> P["6. &quot;Reduced Hydrogen Bonds...&quot;"]
    P --> Q["7. &quot;Original molecule formed multiple strong hydrogen bonds&quot;..."]
    Q --> R["8. &quot;Reduced Hydrogen Bonds...&quot;"]
    R --> S["9. &quot;Over-simplification of the Aromatic Core ...&quot;"]
    
    A --> T["LEDD: Generation"]
    T --> U["x1"]
    U --> V["I0/I1"]
    V --> W["Original Molecule Docking score = -11.76"]
    W --> X["The following fragments are most integral for interactions with the protein pocket: 1. Aromatic and Hydrophobic Core 2. Carbonyl (C=O) 3. Aromatic r-System 4. Halogenated Group"]
    X --> Y["I0/I1"]
    Y --> Z["D1"]
    Z --> AA["Step 1: Core Scaffold Replacement"]
    AA --> AB["Step 2: Optimize the Halogenated Region"]
    
    T --> AC["I"]
    AC --> AD["I0/I1"]
    AD --> AE["X"]
    
    AF["LEDD: Selection"] --> AG["I"]
    AG --> AH["LLMb"]
    
    AI["Selection and reasoning"] --> AJ["Molecule 1 Docking score = -10.48"]
    AJ --> AK["Molecule 2 Docking score = -10.3"]
    AK --> AL["Molecule 3 Docking score = -12.472"]
    
    AM["### &quot;Step 1: Review Docking Scores&quot; **Molecule 3&quot;, with the best score = -12.472, has the strongest binding affinity among the candidates."]
    AN["### &quot;Step 2: Analyze Interaction Profiles&quot; **Molecule 3: Interaction Highlights** - Hydrogen Bonds: Forms strong hydrogen bonds with key residues (e.g., SER150, AR0152). The interaction with SER150 (1.99 Å) and TYR246 (2.13 Å) are particularly stabilizing ... - Hydrophobic Interactions: Strong and multiple hydrophobic interactions with HIS60, TYR90, LEU147, and LEU149"]
    AO["### &quot;Step 3: Assess Drug-Like Properties&quot; **While binding affinity is crucial, the molecule must also exhibit potential as a drug. Other molecules lack some features of Molecule 3. For example: - Molecule 2 lacks halogen bonds and achieves a lower affinity score ..."]
    AP["### &quot;Step 4: Final Recommendation&quot; **Based on docking score, interaction diversity, and drug-likeness potential. **Molecule 3* is the best candidate. Its strong binding affinity (-12.472), balanced polar and nonpolar interactions, and drug-like properties make it an excellent starting point for further optimization."]
```
</details>

Figure 5: Workflow of CIDD framework

# Interaction analysis

The interactionanalysis resultsare asfollows:[PIP(Docking(xo,P))

The smiles string of the molecule is:[x]

![](images/18b22c3eecd8d5a349d41e39d44b459d6d111935859e87c6b69a03a72d6e8d00.jpg)  
Query

[Important] Using theinformation fromtheinteractionanalysisand thefragmentlabels,basedonthecoordinates matching，youneedtoidentifythekeyfragmentonthemoleculethatonducttheinteractionwiththeproteinpocket [Important]Theformatshouldbewhichfragmentcaninteractwithwhichresidueintheproteinpocket.Forexample Thefragment'ethanol'caninteractwiththeresidue'ASP123'intheproteinpocket. [Important]Itshouldbeatfragmentlevel,insteadofatomlevel.Youneedusetheinformationfromthefragmentlabel toidentifywhichatombelongstowhichfragment.   
![](images/984749926f152b1906e4965912017d2ac0f180293e545b1f1543687541d929a5.jpg)

# Output [/]:

# ### \*\*Key Fragmentsof Importance\*\*

Basedontheanalysis,thefolowingfragmentsaremostcrucialforinteractionswiththeproteinpocket:

1.\*\*Aromatic and Hydrophobic Core\*\*

-[C]C1=C[C]=[C][C]=C1(Atoms:511)   
-CriticalforhydrophobicinteractionswithIE113,LEU142andLEU147.hisfragmentanchorsthemoleculeinthe hydrophobicpocket.

2. \*\*Carbonyl (-C=O):\*\*

"-tms12

\- Vitalforhydrogenbonds,particularlywithGLY63andGLU64.Thisfragmentcontributes tothespecificityof the interaction.

3.\*\*Oxetane Ring:\*\*

"-[C]1[C][CJO1 (Atoms:15-18)   
-KeyforhydrogenbondingwithTYR246,providing excelentspecificityand strength.

4. \*\*Aromatic n-System:\*\*

-[C]1=NN[C]=C1 (Atoms:0-4)   
-Engagedin-stackingwithR90,stabilizingtheligandinthebndingpocket.

5. \*\*Halogenated Group:\*\*

-FC1=CC(Cl)=[C][C]=[C]1(Atoms:23-30)   
-Responsible for halogen bonding withPHE61,contributing touniqueand specificinteractions.

Figure 6: Interaction analysis module

# [Instruction]

This is theoriginalmolecule:[Xo]

This is the interactionanalysis:[]

Basedontheinteractionanalysis,designmodicationstotheoriginalmolecule.Yourjobisscaffldhopping:change thecorescaffoldstructurewhileretainingkeypharmacophores.

# [Design Objectives]

1.Themodifiedmoleculeshouldbemorestableandeasiertosynthesizethantheoriginalmolecule.Thenew fragmentsshouldbecommon,stableandnotweird.   
2.Themodifiedmoleculeshouldretainkeypropetiesofthoriginalmolecule,suchasshape,sizendfucioality.   
3.Themodifiedmoleculeshouldcontainthekeyinteractiontypeswiththesameresiduesastheoriginalmolecule.   
4.Theoriginalmoleculemaycontainuncommonorunstablefragments.Identifythesefragmentsandreplacethem withmorecommonandstablecounterparts,ensuringthatthemodificationsretainkeypropertiesoftheoriginal molecule,suchassape,sizeandfunctionality.Forinstance,youmightreplacecyclohexadienewithene. 5.Themodifiedmoleculeshouldbemorelikeadrugcandidatethantheoriginalmolecule.

# [Design Requirements]

1.Do notmodify the molecule too much.   
2.Pleaseonlygivethemodificationsteps,donotgeneratesmilesbyyourself.Wewilluseanotheragenttogenerate thenewmoleculebasedonyourdesign.

# [Experience Summary]

Wehavedonesomemodificationsbefore.Youcanlearnfromthepreviousdesignsandreflectionstomakebetter modifications.

Here is the summary of the previous designs and reflections:[R]

Now,giveusthemodificationsuggestionsandrequirements.

![](images/c069ebfa0aa2268fe000f80b2169c3d92694d3e8c64c962f85d3df9cc48f0ec4.jpg)  
Query

![](images/d2fe711570b7d2fb6d3ebd6a32e6dbe8e1364eb04f909daae198ad989334cbdc.jpg)  
LLMD

# Output [D11:

# ### \*\*Step1: Core Scaffold Replacement\*\*

\*\*Unstableor Uncommon Scaffold:\*\*

-Theoriginalaoldotainsoxetaneing([CCCO)，hichhileeicialfrolubilityndo bonding，canbehemicallyunstableundermetaboliconditionsandissyntheticallyalleging.

\*\*Proposed Modification:\*\*

-Replacethexetaneringwithatetrahydrofuran(THF)ring\*\*THFismorestable,syntheticallaccessiblendetains theabilitytoformdrogenodsiaitsgentom.mportantlyitintainsimilarzeapendrity

# ### \*\*Step 2: Optimize the Halogenated Region\*\*

\*\*UncommonorUnstableFragment:\*\*

-Thehalogenatedaromaticfragment(FC1=CC(Cl)=[C]C]=[C]1)cancontributetometabolicinstabilityooicit (especiallywithchlorine)insomecases.Thepositionandtypeofhalogenationalsodetermineinteractionstrength.

\*\*Proposed Modification:\*\*

-Replacethechlorineatom('-Cl)inthehalogenatedringwithatrifluoromethylgroup(-CF3),whichismetabolically morestableandprovidessimilarhydrophobiccharacterandelectronicpropertiestomaintainhalogen-bonding interactions.Thefluorineatomcanremainunaltered.

# ###\*\*Step 3:Revise the Aromatic Core\*\*

\*\*UncommonorUnstableFragment:\*

-Thecorering[C]C1=C[C]=[C][C]=C1isapolycyclicconjugatedsystempronetooxidativemetabolism.Whileit provideshydrophobicityandanchorsthemolecule,replacingitwithamorecommonaromaticfragment(e.g.,phenyl)can reducemetabolicliabilitieswithoutcompromising interactions.

\*\*Proposed Modification:\*\*

-Replace[CC1=C[C]=[C]C]=C1with\*aphenylring(benzene)\*\*.Phenylringsretainhydrophobicityandsizewhile reducingthelikelihoodofoxidationandincreasingsyntheticaccessibility.

Figure 7: Design Module

![](images/c16368cc8d4615bb1ab3f938874a954ee0050b4625cccd61b56d87084c6021b9.jpg)

LLMp

# Output [D1]:

# ###\*\*Step 4: Replace the1,2,4-Triazine Ring\*\*

\*\*UncommonorUnstableFragment:\*\*

-The[C1C]C1(12,4-trinering)noedinackingithR9caneetaied,utthistructure verycommonindrug-likescaffoldsandmayposesyntheticchallenges.

\*\*Proposed Modification:\*\*

-Replacethe1,2,4-triazineringwitha\*\*pyridinering(C5H5N)\*\*.Pyridinemaintainsaromaticityandhydrogenbond acceptorpotential (viathenitrogenatom)forTt-stackingbutismoredrug-likeandeasiertosynthesize.

# ###\*\*Step 5:Simplify Linker Chains\*\*

\*\*UncommonorUnstableFragment:\*\*

-Thelinkerfragmentconnectingtheoxetaneringandotherpartsofthemoleculemayintroduceunnecessary flexibilityon

\*\*Proposed Modification:\*\*

-Shortenthelinkerchainbyremovingorsimplifyingalkylgroups.Usefewermethylenegroupswhereapplicable to reduce flexibilitywhilemaintainingshapeandsizeforproper binding.

# ###\*\*Summary of Modifications\*\*

1.\*\*OxetaneRing(Unstable/Uncommon)：\*\*Replacewith\*\*THFring\*\*toimprovestabilityandsyntheticaccessibility whileretaininghydrogen-bondingcapability.

2.\*\*alogenatedromaticingetabolicLability)\*Replacechlorine(C)with\*tifuoromethylgroup improvemetabolicstabilitywhilemaintaininghydrophobicinteractionsandhalogenbonding.

3.\*\*PolycyclicAromaticCore(OxidativeRisk)：\*Replace[CJ=C[C]=CCC1withaphenylring(benzene)\*\* reducemetabolicliabilitywhileretaininghydrophobicity.

4.\*\*1,2,4-TineRing(UncommonScaold)：\*Replacewitha\*\*pyridinering\*\*toretaintackinganddrogenbondacceptorpotential whileimprovingdrug-likeness.

5.\*FlexibleLinkers(EntropicPenalty)\*Simplifyandrigidifylinkerregionsbyshorteningalkylchainsducing flexiblity.

# This is the original molecule: [xo]

This is the modificationdesigned by thedesign expert:[D]

Changethemoleculestructurebasedonthemodificationdesignedbythedesignexpert.Importantly，themodified moleculeshouldbe validandmakesenseinthecontextofmedicinalchemistry.

Nowplease only return thesmilesstringof thegeneratedmolecule.Thesmiles string shouldbeenclosed inapair of \$\$.For example:\$\$\$cccc\$

![](images/9b4e4498dbbbb74f7e1b7fbcdd5fe3f2fa3c2e6efa1606b2f93ab5ddcf5a57c9.jpg)

Query

![](images/8ac71105c440f0a9b1fc8aa1ea5189e85f05fa9e66b794bc606f079f9330ea8f.jpg)

LLMD

# Output [x1:

\$\$C1=CC(C(F)(F)F)=C(C(=O)NC(C2CCOC2)NC(=O)C3=CC=CN3)C=C1\$\$\$

Figure 8: Design Module

# [Instruction]

This istheoriginalmoleculestructure]

Thisistheinteractionanalysisoftismoleculeandtheproteinpocet:

This is hemodificationdesign generatedbyyou:[D]

This is hemoleculestructuredesignedbasedonyourmodification:x]

Thisistheinteractionanalysisgeneratedbyinteractionexportagent:[]

Previously， weasked you tomodifya molecule togetanew molecule thatbinds beter to theprotein pocket. We analyzedthebindingofthenewmoleculetotheproteinpocketandputittogetherwiththebindingbeforethe modificationforcomparison.

Basedontheseanalyses,youneedtoreflectonthepreviousmodificationandprovidefeedbackonthedesign.

Besides,wehopeyoucanfindoutwhichfragmentsinsidethestructureofthesetwomoleculesareusefulforbinding totheproteinpocket.

Pleaseusecriticalthinking toanalyze,pointingoutboththegoodandthebad points.Yourreflection is:

![](images/9570e16c3fa58662a15526057dc5d487a2f2656788a2a08b74f75e07da79a6d3.jpg)  
Query

![](images/5ad2423b32b6df290305eb10634ba9f5f194c2486931457b24fadb7e76862276.jpg)

# Output [R1:

# ###\*\*Strengths of the Modifications\*\*

1.\*\*lmproved Stabilityand SyntheticAccessibility:\*\*

-Replacingthe\*oxetanering\*\*withatetrahydrofuran(THF)ring\*\*isacommendableadjustment.THFringsare morestableundermetabolicconditions,whileetainingkeyhydrogen-bondinginteractionsandsimilarstericbulk. Thiswasasensiblechangethatalignswellwithdrug-likenessprinciples.

-Removingthe\*\*chlorineatom\*\*infavorofa\*trifluoromethyl(CF3)group\*\*wasanotherthoughtfulmodification. TheCF3groupimprovesmetabolictabilityandducesotentialtoicityfromactiveogenshiletaining theoriginal hydrophobicityandshape.

2.\*Retention of Key Interaction Modes:\*\*

-TheredesignedmoleculeretainscriticalinteractionssuchashydrogenbondingwithHIS117andARG152， hydrophobicnteractionswith6U147ndH88ndackingwith90enteractie crucialforbindingafinityandensurethemoleculecontinuestoengagetheproteinpocketefectively.

-Thepyridinering\*\*(replacingthelesscommon1,24triainering)alignsbetterwithdrug-lienessulehile maintaininghydrogenbondingandhydrophobiccapabilites.Thissubstitutionstrengthensthemolecule's pharmacokineticprospects.

3.\*\*Refinement of Scaffolds and Simplification:\*\*

-Simplifyingthepolycyclicaromaticcoreintoa\*\*benzenering\*\*wasareasonablemodificationtoreduceoxidationproneelements.Thisensuresthemoleculeismorestableandsyntheticalytractablewithoutlosingsignificant hydrophobicinteractions.

# ###\*\*Weaknesses of theModifications\*\*

1.\*\*ReductioninDockingScore:\*\*

Tedck7)le) cleardropinindingafinityWhilethemodifiedmoleculeretainskeyinteractions,somecriticalbindingcontributions wereinadvertentlyweakenedduringredesign.TheTEFreductionsuggestsalossofkeycomplementarycontacts between the ligandand protein pocket.

2.\*\*Over-Simplification of the Aromatic Core:\*\*

-Replacingtheconjugatedaromaticsystem([C]C1=C[C]=[C][C]=C1) withasimple\*\*benzenering\*\*reducedthe hydrophobicsurfaceareaandtelectronsystemavailableforinteractions.Consequentlydrophobicnteactios withesidu1edelit keyr-interactionswithinthepocket.

3.\*UnutilizedPotentialoftheTrfluoromethylGroup:\*

-Whilethetrforomethyl(CF3)groupmprovedmetabolictabilityitidotirectlyontributetoding interactionswithintheproteinpocket.Thisfunctionalgroupoccupiesspacebutdoesnotengagewithanyspecific residues，effectivelyaddingtomolecularweightwithoutenhancingbinding.Abettr-placedorfunctionallyactive replacementcouldhaveyieldedgreaterinteractionstrength.

Figure 9: Reflection Module

![](images/4b1d4b40eaad7d16f83905059229ea27ff27d6ad32226446bc61a41659201743.jpg)

LLMR

# Output [R1]:

4. \*\*Reduced Hydrogen Bonds:\*\*

-Theoriginalmoleculeformed\*\*multiplestrong hydrogenbonds\*,particularlywithresiduessuchasGLY63， GLU64，andTYR246viaitsoxetaneringandcarbonylgroup.Thesehydrogenbondswereeitherweakenedorlostin theredesignwitherogenods(foingwithH117dG52)alingtofullyompensateis depletion.

5.\*\*FlexibilityintheTHFRing:\*\*

-WhiletheTHFringismorestablethantheoxetanering,itlikelyintroducesgreaterflexibilityduetoitssp3- hybridizedcarbons.Thisflexibitymayleadtoentropicpenaltiesuponbinding，makingthemoleculelesseffcientin achievingapreorganized,bioactiveconformation.

6.\*\*Over-Reliance on Hydrophobic Interactions:\*\*

-Similartotheoriginalmolecule,themodifiedstructurestillreliesheavilyon\*hydrophobicinteractions\*\*forbding (e.g.HIS6)ooiceactioreifioteaios criticalforselectivityndafinityBynotintroducingadditionalpolargroups,theredesignmissedanopportunityto improveoverallbindingspecificity.

# ###\*\*Comparison of Binding Fragments\*\*

####\*\*OriginalMolecule:\*

1.\*\*Oxetane Ring (Lost in the Redesign):\*\*

-FormskeyhydrogenbondswithTYR246inthebindingpocket,contributingsignificantlytospecificandstrong ligandbinding.Itsremovalweakenedoverallbindingaffnity.

2.\*\*Conjugated Hydrophobic Core ([C]C1=C[C]=[C][C]=C1):\*\*

-Providesextensivehydrophobicandt-stackinginteractionswithresiduessuchasILE113,LEU142,andTY90. Replacingthisricharomaticstructurewithabenzeneringreducedthehydrophobicandrt-electroncontributionto binding.

3. \*\*HalogenatedAromaticRing (FC1=CC(Cl)=[C]C]=])\*\*

EngagestheproteiniaogenodingithH61ddingspcificitytoindinginteractions.eplacingclorie withCF3abolishedsomehalogenbonds,weakeningprotein-ligandcomplementarity

###\*\*Modified Molecule:\*\*

1.\*\*THF Ring (Introduced):\*\*

-Retainstheabilitytoformhydrogenbonds (e.g.withARG152).However,itsintroductionhascausedgreater flexibilityandentropicpenaltiesthatmayoffsetitsstabilizingcontributions.

2.\*\*Trifluoromethyl Group (CF3,Introduced):\*\*

-Metabolicallstableandhydrophobicbutdoesnotdirectlyinteractwiththeprotein.Itsplacementonthearomatic ringaddsmolecularweightbutnofunctionalenhancementtobinding.

3.\*\*PyridineRing (Introduced)\*\*

-Maintainshydrogen-bondingwithHIS117and interacts hydrophobicallwithHlS60,performing wellasa replacementfor12,4-triazine.Thoughnotasinherentlydiverseininteractionopportunitiesasitspredecsorit improvesthedrug-likenessof themolecule.

4.\*\*BenzeneRing (Simplified)\*\*

-WhileitretainssomehydrophobicinteractioncapabilitythisfragmentnolongerengagesresidueslikeTYR90or PHE188asrobustlyastheoriginalconjugatedaromaticsystem.Thisreducedbindingafinity

Figure 10: Reflection Module

![](images/20d07239c02fbd3caf4544b92e6af27dab73b9cf21d65ef6a0b4ef54c215f99b.jpg)

LLMR

# Output [R1]:

# ###\*\*Key Fragments Retained or Lost for Binding\*\*

\*\*CriticalRetainedFragments:\*\*

1.\*\*PyridineRing\*\*forrt-stackingandhydrogenbonding withTYR90and HIS117.   
2.\*\*Hydrogen BondingCarbonyiGroup\*\*interactingwith HIS117andARG152.

\*\*CriticalFragmentsLost\*\*

1.OxetaneRing\*\*ontributedunusuallytronghydrogenbondsto246，whichwerelostinthedeign.   
2.\*ConjugatedHydrophobicCore\*\*ensuredmultisitehydrophobicinteractionsandrt-stackingwithresidueslike LEU142andTYR90.   
3.HalogenatedAromaticingprovdedhalogebondswithPHE61contributingunquespecicitytith redesign.

# ###\*\*Suggestions for Improvement\*\*

1.\*\*Reintroduce Hydrogen BondingGroups\*\*   
-Addbackpoarfragments(e.g.roylmideoups)toreasedrogenodingpacityithie TYR246,GY63,andGLU64.   
2.\*\*Revisit the Aromatic Core:\*\*   
-Insteadofoversimplifyingthehydrophobiccoretobenzene,considerapolycyclicaromaticorheterocyclicsystem tobalancehydrophobicityandmetabolicstabity.   
3.\*\*OptimizeTrifluoromethylGroup Placement:\*\*   
-MoveorreplacetheCF3groupwithafragmenthatdirectlyengagesresiduesintheproteinpocket(e.g.,a difluorophenyl or hydrophilicsubstituent).   
4. \*\*Rigidify the THFRing:\*\*   
-LocktheTHFringintoaconstrainedsystem (e.g.,fusedbicyclicrings)toreduceflexibilityandentropicpenalties.

# ### \*\*Conclusion\*\*

Themodificationsresultedinamoleculethatissyntheticallyandmetabolicallyimprovedbutlessefectiveinbinding totheproteinpocketasindicatedbythediminisheddockingscore.Whileretainingimportantinteractionsthe redesignlosttoomanyadvantageousfragments(e.g.，oxetane,conjugatedaromaticcore).Futureoptimizations shouldaimtorelotteactiosroeroeingndeopoicityitarctfo strongerandmorespecificbinding.

Figure 11: Reflection Module

# [Instruction]

Givenaproteinpocketandanumberofdifferentmolecules,Ineedyoutofindamoleculethatisbestsuitedto bindthisproteinpocket.Wewillprovideyouwithinteractionreportsforeachmoleculeandproteinpocketand askyoutomakechoicesbasedonthisinformation.Youshouldconsiderboththebindinganalysisandwhether themoleculehaspotentialtobearealdrug.Youshouldoutputthereasonandthesmilesstringofthechosen molecule.Thesmilesstringshouldbeenclosedinapairof\$\$s.Forexample:.(Thereason)Thechosensmiles is:\$\$\$CCO\$\$\$

This is the molecule structure:[Xn]

Thisistheinteractioanalysisoftismoleculeandtheproteinpoc[]

Thisisthemolecule structureXm]

Thisistheinteractioanalysisoftismoleculeandtheproteinpock:[m

Thisisthe molecule structure:xp]

Thisistheinteractionanalysisofthismoleculeandtheproteinpocket:p]

Please think stepby step:

![](images/3b897bb80596b03cff776667fb69660c1c2ef7dddd9c713c7af441811ad481b5.jpg)  
Query

![](images/45c33c3700d2b03aed8bd315ccb99d1baa3e1bd6585a3e8bd839656c61477343.jpg)

# The chosen molecule is:

# O=C(C1=CC=C(C=C1)C2=CC=CC=C2)N(C3CCOC3)C(NC4=C(F)N=CC=C4)=O

Thedocking score of the chosenmoleculeis:-12.472

Thereason forchoosing themolecule is:Toselect the bestmolecule for binding to the proteinpocket,wewillstepthroughthe following considerations:

# ###\*\*Step1:ReviewDocking Scores\*\*

Thedockingscoreisakeymetricindicating thebindingaffnitybetweenamolecule andtheproteinpocket.Lowerdockingscores(morenegativevalues)suggeststronger binding.Thedockingscoresfortherespectivemoleculesareasfollows:

1.Molecule1:-10.148

2.Molecule2:-10.3

3.Molecule3:-12.472

Fromthis，\*Molecule3\*，withthebestscoreof -12.472\*\*，hasthestrongestbinding affinityamong thecandidates.

# ### \*\*Step 2:Analyze Interaction Profiles\*\*

Buildingoffthedockingscores,wenowconsidertherichinteractionprofilesofeach molecule.Amoleculethatformsdiverseinteractionswilloftenbindmorerobustlyand specificallytotheproteinpocket.

####\*\*Molecule3:Interaction Highlights\*\*

-\*\*Hydrophobic Interactions:\*\*Strongand multiple hydrophobic interactions with HIS60，90,U147andU149choredyearomaticeein.

-\*\*HydrogenBonds:\*\*Formsstrong hydrogenbondswithkeyresidues (e.g.,S150, ARG152).TheinteractionwithSER150(1.99A)andTYR246(2.13A)areparticularly stabilizing.

-\*\*r-Stacking:\*\* Strong I-stacking with TYR9o (T-shaped geometry).

-\*\*-Cation Interactions:\*\*Robust Tt-cation interactionwithARG152(3.85A), stabilized furtherby ideal offsetalignment (1.32A).

-\*\*HalogenBonds:\*\*TwohalogenbondswithGLU189 (3.84A)andASN237 (3.40A) provideanadditionallayerofinteractionmakingthismoleculeuniqueinitsineraction diversity.

Figure 12: Selection Module

![](images/80ae9efcd7445bc61533b3e9209ef9a83d819ea49f8c0cfaf49824f8943ba761.jpg)

\*\*Key Strengths:\*\*

-Theinteractiondiversityand strengthofMolecule3far surpassother molecules, leveraginonii halogenbonding.   
-Themolecleiesielftothladarsin specificity fortheproteinpocket.

# ### \*\*Step 3:Assess Drug-Like Properties\*\*

Whilebindingaffnityiscrucial,themoleculemustalsoexhibitpotentialasadrug. Propertiesrelevanttodrug-likenessinclude:

-\*\*HydrophobicComponents:\*\*Ensuresolubilityand stabilityformembrane difusion.   
-\*\*Hydrogen Bonding Groups:\*\*Contributetospecificityand bioactivity.   
-\*\*HalogenIncorporation:\*\*Enhancesmembranepermeabilityandmetabolicstability.   
\*\*CompactNon-Bukytructure\*\*Ensuresthemoleculefiswithinteroteinocket withoutstericclashes.

# ForMolecule3:

-Thecombinationofaromaticrings,amidegroups,andfluorineatomssupports balancedhdrophobicandpolarproperties,increasingstabilityandbioavailability.   
-Theinclusionof halogensenhancesdrug-likeness further.

Othermolecules lacksome featuresofMolecule3.Forexample:

-Molecule2lackshalogenbondsandachievesa loweraffinityscore.

-Molecule1havegoodbindingbutlackthebreadthof interactionsseenwithMolecule 3.

# ### \*\*Step4:Final Recommendation\*\*

Basedondockingscore,interactiondiversityanddrug-likenesspotential,\*\*olecule3\*\* isthebestcandidate.Itsstrongbindingaffinity(-12.472)，balancedpolarandnonpolar interactionsanddrug-likepropertiesmakeitanexcellentstartingpointforfurther optimization.

# ### \*\*Chosen Molecule\*\*

\*\*Reason:\*\*Molecule3exhibitsthehighestdocking score，withdiverseinteractiontypes (hydropicni itincriticalgionsofteproteinocketAdditionallitesromisingrug-like featuressuchashalogenincorporationandawelloptimizedmolecularstructure.

\*\*Selected SMILES String:\*\*

$$
\S \S \S O = C (C 1 = C C = C (C = C 1) C 2 = C C = C C = C 2) N (C 3 C C O C 3) C (N C 4 = C (F) N = C C = C 4) = O \S \S
$$

Figure 13: Selection Module

# D Algorithm for MRR and AUR

The complete calculation process for assessing the reasonability of a molecule is outlined in Algorithm 1.

# Algorithm 1: Evaluation of Molecular Reasonability

Input: Molecule object (mol)

Output: Molecular Reasonability (MRR) and Atom Unreasonable Ratio (AUR)

# Step 1: Detect Carbonyl and Imine Group Carbons

Initialize an empty list for carbonyl/imine carbons.

foreach bond in mol do

if bond is double and one atom is carbon, the other is oxygen or nitrogen then Record the carbon atom in carbonyl/imine groups.

# Step 2: Identification of Ring Systems

Identify all ring structures and their corresponding atom indices within mol.

Calculate the number of atoms in each ring.

foreach ring in the molecule do

if the ring shares one or more atoms with another ring then

Group the connected rings into a single ring system.

# Step 3: Evaluation of Molecular Reasonability

Exclude any atoms previously identified as part of carbonyl or imine groups.

Classify the remaining carbon atoms in each ring system as follows:

• sp2 hybridized: Aromatic or unsaturated carbons.2   
• Non-sp hybridized: Saturated carbons.

foreach ring system in the ring systems do

if the ring system contains multiple rings and all carbon atoms are non-sp2 then

Mark the molecule as unreasonable.

Add the atoms to the unreasonable atom list.

foreach ring system in the remaining ring systems do

foreach ring in the ring system do

if all carbon atoms within the ring are consistent in hybridization (either all sp2 or all non-sp2) then

Mark the ring as reasonable.

Add the ring to the remaining ring list.

while the remaining ring list is not empty do

foreach ring in the remaining ring list do

Exclude atoms that have already been classified as reasonable.

if all remaining carbon atoms are consistent in hybridization (either all sp2 or all non-sp2) then

Mark the ring as reasonable.

if no new reasonable rings are identified then

Mark the molecule as unreasonable.

Add the carbon atoms in the remaining rings to the unreasonable atom list.

Exit the loop.

Calculate AUR as the ratio of unreasonable atom count to the total ring atom count.

Return MRR and AUR.

# E QikProp properties

The full set of properties used for the QikProp pass ratio analysis is presented in Table 3.

The QikProp filter applied in the main text incorporates a comprehensive range of criteria provided by QikProp, including "#stars", "#amine", "#amidine", "#acid", "#amide", "#rotor", "#rtvFG", "mol\_MW", "dipole", "SASA", "FOSA", "FISA", "PISA", "WPSA", "volume", "donorHB", "accptHB", "dip2/V ", "ACxDN.5/SA", "glob", "QPpolrz", "QPlogPC16", "QPlogPoct", "QPlogPw", "QPlogPo/w", "QPlogS", "CIQPlogS", "QPPCaco", "QPlogBB", "QPPMDCK", "QPlogKp", "IP(eV)", "EA(eV)", "#metab", "QPlogKhsa", "PercentHumanOralAbsorption", "SAFluorine", "SAamideO", "PSA", "#NandO", and "RuleOfThree".

Table 3: QikProp Properties and Descriptors 

<table><tr><td>Property or Descriptor</td><td>Description</td><td>Range or Recommended Values</td></tr><tr><td>Molecule name</td><td>The molecule&#x27;s identifier derived from the title line in the input structure file. If no title is provided, the file name is used.</td><td></td></tr><tr><td>#stars</td><td>Count of descriptors or properties falling outside the 95% range for known drugs. A higher count indicates reduced drug-likeness.</td><td>0 – 5</td></tr><tr><td>#amine</td><td>Total non-conjugated amine groups present in the molecule.</td><td>0 – 1</td></tr><tr><td>#amidine</td><td>Number of amidine or guanidine functional groups in the structure.</td><td>0</td></tr><tr><td>#acid</td><td>Quantity of carboxylic acid groups in the molecule.</td><td>0 – 1</td></tr><tr><td>#amide</td><td>Count of non-conjugated amide groups.</td><td>0 – 1</td></tr><tr><td>#rotor</td><td>Number of rotatable bonds that are neither trivial nor sterically hindered.</td><td>0 – 15</td></tr><tr><td>#rtvFG</td><td>Total reactive functional groups present in the molecule, potentially affecting stability or toxicity.</td><td>0 – 2</td></tr><tr><td>mol_MW</td><td>Molecular weight of the compound.</td><td>130.0 – 725.0</td></tr><tr><td>Dipole</td><td>Calculated dipole moment of the molecule in Debye units.</td><td>1.0 – 12.5</td></tr><tr><td>SASA</td><td>Solvent-accessible surface area (SASA) in square angstroms, measured with a probe of 1.4 Å radius.</td><td>300.0 – 1000.0</td></tr><tr><td>FOSA</td><td>Hydrophobic part of the SASA, representing saturated carbon and attached hydrogen atoms.</td><td>0.0 – 750.0</td></tr><tr><td>FISA</td><td>Hydrophilic fraction of the SASA, encompassing polar atoms like nitrogen and oxygen.</td><td>7.0 – 330.0</td></tr><tr><td>PISA</td><td>SASA component attributable to π-systems.</td><td>0.0 – 450.0</td></tr><tr><td>WPSA</td><td>Weakly polar component of the SASA, including atoms like halogens, phosphorus, and sulfur.</td><td>0.0 – 175.0</td></tr><tr><td>Volume</td><td>Total solvent-accessible volume in cubic angstroms, determined with a 1.4 Å radius probe.</td><td>500.0 – 2000.0</td></tr><tr><td>donorHB</td><td>Estimated number of hydrogen bonds donated to water in solution.</td><td>0.0 – 6.0</td></tr><tr><td>accptHB</td><td>Estimated number of hydrogen bonds accepted from water.</td><td>2.0 – 20.0</td></tr><tr><td>Dip $^{2}$ /V</td><td>Dipole moment squared divided by molecular volume, a key factor in solvation energy.</td><td>0.0 – 0.13</td></tr><tr><td>ACxDN $^{0.5}$ /SA</td><td>Cohesive interaction index in solids based on molecular properties.</td><td>0.0 – 0.05</td></tr><tr><td>glob</td><td>Descriptor measuring how close the shape of a molecule is to a sphere.</td><td>0.75 – 0.95</td></tr><tr><td>QPpolrz</td><td>Predicted molecular polarizability in cubic angstroms.</td><td>13.0 – 70.0</td></tr><tr><td>QPlogPC16</td><td>Predicted partition coefficient between hexadecane and gas phases.</td><td>4.0 – 18.0</td></tr><tr><td>QPlogPoct</td><td>Predicted partition coefficient between octanol and gas phases.</td><td>8.0 – 35.0</td></tr><tr><td>QPlogPw</td><td>Predicted partition coefficient between water and gas phases.</td><td>4.0 – 45.0</td></tr><tr><td>QPlogPo/w</td><td>Predicted partition coefficient between octanol and water phases.</td><td>-2.0 – 6.5</td></tr><tr><td>QPlogS</td><td>Predicted solubility of the molecule in water (log S, in mol/L).</td><td>-6.5 – 0.5</td></tr><tr><td>CIQPlogS</td><td>Conformation-independent prediction of water solubility (log S).</td><td>-6.5 – 0.5</td></tr><tr><td>QPPCaco</td><td>Predicted permeability through Caco-2 cells, in nm/s.</td><td>&lt;25 poor, &gt;500 great</td></tr><tr><td>QPlogBB</td><td>Predicted partition coefficient for brain/blood.</td><td>-3.0 – 1.2</td></tr><tr><td>QPPMDCK</td><td>Predicted permeability through MDCK cells, in nm/s.</td><td>&lt;25 poor, &gt;500 great</td></tr><tr><td>QPlogKp</td><td>Predicted skin permeability (log Kp).</td><td>-8.0 – -1.0</td></tr><tr><td>IP(eV)</td><td>Ionization potential calculated using PM3.</td><td>7.9 – 10.5</td></tr><tr><td>EA(eV)</td><td>Electron affinity calculated using PM3.</td><td>-0.9 – 1.7</td></tr><tr><td>#metab</td><td>Predicted number of possible metabolic reactions.</td><td>1 – 8</td></tr><tr><td>QPlogKhsa</td><td>Predicted binding affinity to human serum albumin.</td><td>-1.5 – 1.5</td></tr><tr><td>HumanOralAbsorption</td><td>Qualitative assessment of oral absorption: 1 (low), 2 (medium), or 3 (high).</td><td></td></tr><tr><td>PercentHumanOralAbsorption</td><td>Quantitative prediction of oral absorption percentage.</td><td>&gt;80% high, &lt;25% poor</td></tr><tr><td>SAFluorine</td><td>Solvent-accessible fluorine surface area.</td><td>0.0 – 100.0</td></tr><tr><td>SAamideO</td><td>Solvent-accessible surface area of amide oxygen atoms.</td><td>0.0 – 35.0</td></tr><tr><td>PSA</td><td>Polar surface area, calculated for nitrogen, oxygen, and carbonyl groups.</td><td>7.0 – 200.0</td></tr><tr><td>#NandO</td><td>Total count of nitrogen and oxygen atoms.</td><td>2 – 15</td></tr><tr><td>RuleOfFive</td><td>Number of Lipinski’s Rule of Five violations.</td><td>Max 4</td></tr><tr><td>RuleOfThree</td><td>Number of Jorgensen’s Rule of Three violations.</td><td>Max 3</td></tr><tr><td>#ringatoms</td><td>Count of atoms within molecular rings.</td><td></td></tr><tr><td>#in34</td><td>Number of atoms in 3- or 4-membered rings.</td><td></td></tr><tr><td>#in56</td><td>Number of atoms in 5- or 6-membered rings.</td><td></td></tr><tr><td>#noncon</td><td>Number of ring atoms unable to form conjugated aromatic systems.</td><td></td></tr><tr><td>#nonHatm</td><td>Count of heavy (non-hydrogen) atoms in the structure.</td><td></td></tr><tr><td>Jm</td><td>Predicted maximum transdermal transport rate ( $\mu g \text{ cm}^{-2} \text{ hr}^{-1}$ ).</td><td></td></tr></table>

# F Computing Resource

In this work, we primarily utilize pretrained 3D generative models and large language model (LLM) APIs to conduct our experiments. The 3D model sampling is performed using a single NVIDIA A100 GPU. For the LLM component, we rely on API-based access provided by the service provider, which requires no local computational resources.

# G More Experiment Results

Based on the different criteria presented in Table 3, we provide additional pass ratio results in Table 4.

Filter 1 is identical to the QikProp filter used in the main text.

Filter 2 removes some non-essential properties and focuses on well-defined physicochemical properties, including "#rtvFG", "QPlogS", "QPlogPo/w", "mol\_MW", "dipole", $" \mathrm { S A S A " }$ , $" \mathrm { F O S A " }$ , $" \mathrm { F I S A " }$ , $\ " \mathrm { I P } ( \mathrm { e V } ) \ "$ , "EA(eV)", "#metab", "PercentHumanOralAbsorption", and "PSA".

Filter 3 assesses molecular compliance with the "RuleOfFive" criterion. However, instead of allowing up to four violations as typically recommended, this filter adopts a stricter definition, considering only molecules that fully comply (i.e., setting the maximum allowable violations to zero).

Table 4: QikProp results for different methods with and without CIDD 

<table><tr><td>Method</td><td>Filter 1</td><td>Filter 2</td><td>Filter 3</td></tr><tr><td colspan="4">Pocket2Mol</td></tr><tr><td>Original</td><td>29.58%</td><td>51.52%</td><td>89.58%</td></tr><tr><td>CIDD</td><td>56.97%</td><td>75.64%</td><td>92.24%</td></tr><tr><td colspan="4">TargetDiff</td></tr><tr><td>Original</td><td>26.32%</td><td>48.20%</td><td>69.47%</td></tr><tr><td>CIDD</td><td>53.37%</td><td>75.60%</td><td>81.85%</td></tr><tr><td colspan="4">DecompDiff</td></tr><tr><td>Original</td><td>29.04%</td><td>53.96%</td><td>55.14%</td></tr><tr><td>CIDD</td><td>37.54%</td><td>68.48%</td><td>65.64%</td></tr><tr><td colspan="4">MolCRAFT</td></tr><tr><td>Original</td><td>22.37%</td><td>43.52%</td><td>66.45%</td></tr><tr><td>CIDD</td><td>35.22%</td><td>63.23%</td><td>74.09%</td></tr></table>

# H More cases

More generated molecules from CIDD are presented below. For each case, we display the initial supporting molecule derived from 3D-SBDD models alongside the final designed molecules produced by CIDD.

Supporting molecule CIDD output 

<table><tr><td><img src="images/010c62e609b98617432eb9c24a0ab6be63b21324486a9e9e31376776d9fc24fd.jpg"/></td><td><img src="images/558750b01c55e0f9ae4adf0032152372dd93980857feeb68f269bc527c490d77.jpg"/></td></tr><tr><td>title: IDHP_HUMAN_40_452_0: Unreasonable vina: -7.824</td><td>title: IDHP_HUMAN_40_452_0: Reasonable vina: -10.106</td></tr><tr><td><img src="images/0c225c4630b14b095a56a20434dfd7c4a12e9912f3d73346018a0fff169048f7.jpg"/></td><td><img src="images/b5928b0b5f3e51a4dffbe31e3f2b9691b2b104e114fedf97f62f9b40778e647b.jpg"/></td></tr><tr><td>title: NOS1_HUMAN_302_723_0: Unreasonable vina: -9.415</td><td>title: NOS1_HUMAN_302_723_0: Reasonable vina: -10.098</td></tr><tr><td><img src="images/00f5e3737fba5900a4a2e64d540b0205fad014d0fa2b441a9fd078107c142eb2.jpg"/></td><td><img src="images/25fe50bdf374a03ffdd60cc2c925793828d4ffbe0305c23aaea71dcc9969367e.jpg"/></td></tr><tr><td>title: NOS1_HUMAN_302_723_0: Unreasonable vina: -10.069</td><td>title: NOS1_HUMAN_302_723_0: Reasonable vina: -10.22</td></tr><tr><td><img src="images/e7fb0e6146d9bb137febef86ad9cf7051a0c35ee072ff018a3d6b27f17890d84.jpg"/></td><td><img src="images/8a622ebb76655f0db947c0c76c4881453a279def4a27d625cfb6ee2cfe9765b6.jpg"/></td></tr><tr><td>title: ABL2_HUMAN_274_551_0: Unreasonable vina: -10.007</td><td>title: ABL2_HUMAN_274_551_0: Reasonable vina: -10.946</td></tr><tr><td><img src="images/f3f9e982d22efbbaa2d55b82bf2bda8ec4581262910ab543d8943891a2a78440.jpg"/></td><td><img src="images/2f46ead844af0fea6002db0f24db91a1402023b2a120e935416492365bf538a1.jpg"/></td></tr><tr><td>title: AK1BA_HUMAN_1_316_0: Unreasonable vina: -10.421</td><td>title: AK1BA_HUMAN_1_316_0: Reasonable vina: -10.778</td></tr><tr><td><img src="images/f9e36d260f55898535efa6b7ae7862e9f891aaa3e53e43b2635fcd7f17186d95.jpg"/></td><td><img src="images/3e4d1c6957ed543e562cc61b9d248ef3d5e6ecef1a17dc6ffdbbdd3fa54ad15e.jpg"/></td></tr><tr><td>title: NQO1_HUMAN_2_274_0: Unreasonable vina: -7.951</td><td>title: NQO1_HUMAN_2_274_0: Reasonable vina: -9.51</td></tr></table>

![](images/a78339f95b9d29d6d7f771d52cf664276352f1e6fc6caf1d6ffee6ba32339691.jpg)

![](images/a83f4111bf035e4a93aa14e8f549d3824987dfa535f11506985ab2f7bf3f610d.jpg)

![](images/e7e365b599f6c0ca6124e9aa3f3ec711bd40432908779284ba49b09ff03121b4.jpg)

![](images/5f1eab05417813e3fdc654fb4402bcbbd904d279bd8da076b40dfc19822e9106.jpg)

![](images/26bbd8df33893143ea739379ab072774a5cdf15ae2ec58e7e01b89604eebead4.jpg)

![](images/ead6bffb4e03cbb8683bddf32c15c25cf3400c8132cf690f1ff2341a1cf96258.jpg)

![](images/c2c5c3c96c220567feda0c9469ab79aa88b919f4229c9779040ff8c4932a9590.jpg)

![](images/a80d28875caff28ff4c2a7a6a4a6077e812864f90f6e6b8bae5b39080ec022d0.jpg)

![](images/f46c826f18e8815f652ef2f77aba3a9dd86183f71c85977a6cfde70816950e6a.jpg)

![](images/1ceb60445da62bff851bfb4c63978accee67b6812cef01961f1b05a6d90b95df.jpg)

![](images/555d2c7677c86ba7c66ce7a4edd3e52f31dbbb75df5d94ff88ffd06cb351cd48.jpg)

![](images/58929d0c7d48c8cc25fb9331d7836cf8403e054e595d2931fa95bdf3015a8a65.jpg)

Supporting molecule CIDD output 

<table><tr><td><img src="images/5a5ae25ba732346f277c07714a37c58aad29a99d746694a53f92e8e06b47c66d.jpg"/>title:PHKG1_RABIT_6_296_ATPsite_0:Unreasonablevina: -8.548</td><td><img src="images/3002fdeab57c5bb230c3c04aed533c107924665bf13a07ded07797d25d530fd4.jpg"/>title:PHKG1_RABIT_6_296_ATPsite_0:Reasonablevina: -8.727</td></tr><tr><td><img src="images/fe9327518231f4ea4b32a6865930295d6c9ff017595f497cb3ed11a1bfc7109b.jpg"/>title:CD38_HUMAN_44_300_0:Unreasonablevina: -7.443</td><td><img src="images/f9ff555beba594a62b9eb5953089ec4e9ad3a4497bc47fb6e899debd3771dd81.jpg"/>title:CD38_HUMAN_44_300_0:Reasonablevina: -8.863</td></tr><tr><td><img src="images/b2879588e17c26b02359bd2ed2ed9152199e3cefe6bcdd37db60b1d7451b6423.jpg"/>title:P2Y12_HUMAN_1_342_0:Unreasonablevina: -10.463</td><td><img src="images/b1961a22294ea35e37e98ade976656cd95458f326c95983f817ddbf622d0eb8f.jpg"/>title:P2Y12_HUMAN_1_342_0:Reasonablevina: -10.674</td></tr><tr><td><img src="images/0a125897ba1b77a95c38e01c962fc9e372568fdc435d303f1857116edaa51e49.jpg"/>title:SQHC_ALIAD_1_631_0:Unreasonablevina: -14.278</td><td><img src="images/e88a16875c44d33884643d3be7c45e88a8d87ef1522268114d327fa5b2d87992.jpg"/>title:SQHC_ALIAD_1_631_0:Reasonablevina: -17.408</td></tr><tr><td><img src="images/c09d212983808b3834231a5dd5b846b4befb974c525b1ec8aa429a698399a7fb.jpg"/>title:BGAT_HUMAN_63_353_0:Unreasonablevina: -7.891</td><td><img src="images/80a7cfd835579ce29e724165ff1b7afb80a87b759951f22b7a58ec7b3df34f59.jpg"/>title:BGAT_HUMAN_63_353_0:Reasonablevina: -9.201</td></tr><tr><td><img src="images/0c54f734232add5af78313c0465390dbbd097dd47887030a03178fac699d6c3b.jpg"/>title:CHIB_SERMA_1_499_0:Unreasonablevina: -7.115</td><td><img src="images/bafea344bf08ec380fa451f4381f2aa5a50aca093f57fc209e26356d31147fd0.jpg"/>title:CHIB_SERMA_1_499_0:Reasonablevina: -8.719</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/f093591049aa61a4467cdd9d306098a04b75df810ad243d2cf9e1755e240e064.jpg"/>title: BGL07_ORYSJ_25_504_0: Unreasonable vina: -8.041</td><td><img src="images/d880817971bf934a0e4fce6abb222c22d31ccd4662876f8e13612acbc43bd84c.jpg"/>title: BGL07_ORYSJ_25_504_0: Reasonable vina: -9.949</td></tr><tr><td><img src="images/aa6d17d5d80abd56dbc021a3bff2b259571d776d5229acda2c8c791cf6355b22.jpg"/>title: TNKS2_HUMAN_948_1162_0: Unreasonable vina: -10.284</td><td><img src="images/46577ebbfb5edf40e92f602f4d6dfcf4834a58f9e6a2c917887c4404fec2f55b.jpg"/>title: TNKS2_HUMAN_948_1162_0: Reasonable vina: -10.974</td></tr><tr><td><img src="images/ea5a1138a1c00d8e9ed13193180faf3d9f1307a84eb56935dd7df25a74be2072.jpg"/>title: HMD_METJA_1_358_0: Unreasonable vina: -9.259</td><td><img src="images/cd7c540058c3199f9bc523a64c98b1eda52c5c16d27724246d8f542ef0d5f723.jpg"/>title: HMD_METJA_1_358_0: Reasonable vina: -10.458</td></tr><tr><td><img src="images/3f62de7d08dee958c65db6ff66e6c4f5af66f92808335270daba7bce38b4ae3a.jpg"/>title: SQHC_ALIAD_1_631_0: Unreasonable vina: -13.626</td><td><img src="images/b7fdd69a03603262470046e4f483c19cf99934ac476f8c21719a25662f78a4bb.jpg"/>title: SQHC_ALIAD_1_631_0: Reasonable vina: -13.825</td></tr><tr><td><img src="images/17f52556f0f00fdb533074d166704e23bcf6cee4aa478968d4e3138baea5d863.jpg"/>title: CHIB_SERMA_1_499_0: Unreasonable vina: -10.676</td><td><img src="images/8f0a52cc82e691a06e06640d6779b6a907bfd6107792caf6ea227b0cbe33b237.jpg"/>title: CHIB_SERMA_1_499_0: Reasonable vina: -13.113</td></tr><tr><td><img src="images/e51ce9d0ae4bd6eb78202f82122db543547c12c15dbbd5a6e4d1195cf61d59bb.jpg"/>title: NR1H4_HUMAN_258_486_0: Unreasonable vina: -10.038</td><td><img src="images/bebbbc0ab7437cc19a59d3e99afa4d511f546a5ddbe447b2b21c18a4dbec07df.jpg"/>title: NR1H4_HUMAN_258_486_0: Reasonable vina: -11.021</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/6f38cdcab953fa0977aa6d9fcf441be3bb38be22659911f3b99f2fadbb681e9d.jpg"/></td><td><img src="images/460351e62547e7b322117592fa762369c2a99008aa4a42642177c86f499503a9.jpg"/></td></tr><tr><td>title: SDIA_ECOLI_1_171_0 : Unreasonable vina: -11.019</td><td>title: SDIA_ECOLI_1_171_0 : Reasonable vina: -11.294</td></tr><tr><td><img src="images/8e2e40e006363b4e5b2c9adcb08ab806e85c095d976b34341f796b00772632ac.jpg"/></td><td><img src="images/e914e43c7286f1c27e216ea1f34fa55ded632e9c892c2a30593ba00fca78b98e.jpg"/></td></tr><tr><td>title: GSTP1_HUMAN_2_210_0 : Unreasonable vina: -7.591</td><td>title: GSTP1_HUMAN_2_210_0 : Reasonable vina: -8.725</td></tr><tr><td><img src="images/acf890a617d1ea212af138e92e075fd448cb160cd81b3f64930a1a9d2bf5fa10.jpg"/></td><td><img src="images/08d6c2815e1942e9b39b91ef504198e6500ecdfaf6df0a73c28789cc4c039f97.jpg"/></td></tr><tr><td>title: HDHA_ECOLI_1_255_0 : Unreasonable vina: -8.5</td><td>title: HDHA_ECOLI_1_255_0 : Reasonable vina: -8.515</td></tr><tr><td><img src="images/d289fd2af6c4fdb4ff60f61460f9137fd4b0eb06576d6bd91d27e35caa8cfdd1.jpg"/></td><td><img src="images/060c97d25622284f82d3d08b2d640a53af0cdeafd3871cca229f0052fab6b87c.jpg"/></td></tr><tr><td>title: IDHP_HUMAN_40_452_0 : Unreasonable vina: -8.176</td><td>title: IDHP_HUMAN_40_452_0 : Reasonable vina: -10.774</td></tr><tr><td><img src="images/44066470f496e56a1e2ff6bdc49951670b7c0b61bf03a0309fd1fdff90c3b1d3.jpg"/></td><td><img src="images/361c6dcceda5c3913322246da136694946a4c9010dcabc4cdb3b70a4e712c9d4.jpg"/></td></tr><tr><td>title: IDHP_HUMAN_40_452_0 : Unreasonable vina: -7.605</td><td>title: IDHP_HUMAN_40_452_0 : Reasonable vina: -11.661</td></tr><tr><td><img src="images/1c51c9f1901fd8d59509bec0067cd6376c50dd6b66f026a985277f12e683f3df.jpg"/></td><td><img src="images/f510a62c25266ee07101f4ce7625a526bb9d50b413b5c12891b97681d537df52.jpg"/></td></tr><tr><td>title: AK1BA_HUMAN_1_316_0 : Unreasonable vina: -9.845</td><td>title: AK1BA_HUMAN_1_316_0 : Reasonable vina: -9.981</td></tr><tr><td><img src="images/f656f6b5d6511d550d6d7bb16ba3250c347bfad815905f3edd8cd636c371b757.jpg"/></td><td><img src="images/537a2d5c20efcd9bb7b8a2f2877bf463a150b43d0fadc3b5cfa2be31fb9d925f.jpg"/></td></tr><tr><td>title: OLIAC_CANSA_1_101_0 : Unreasonable vina: -7.631</td><td>title: OLIAC_CANSA_1_101_0 : Reasonable vina: -8.866</td></tr></table>

![](images/34c7b5a562b977c0df9bc362d0842e4565e200be1a0901e2c6ab30f195aa094f.jpg)

![](images/0deb26d3b8a9cfa3a47a4fa3617e70c61e14c1343da0019f52ecc12e6a554d78.jpg)

![](images/4c7eb6bf16fc9a6575de9d2a19ad7dfcffb93524c5cd36a3b5e146c252594cd6.jpg)

![](images/680c279a5924cc72beea601d982f368596f816dfb275bc806a5d4779085c5f03.jpg)

![](images/fd283951012624cea1127e51eeee0b196af75c67604bdb3b64d714bf34cb8888.jpg)

![](images/92d16c2aa34826977406804c3403f5aa478d0d0717879fe05773ef7e92d82ea8.jpg)

![](images/93c5351a1d3845c1d5fb27026f7d56c6af6cf9c07b67b75f3403a11299dc2a3f.jpg)

![](images/13d11ef88b18882e246b70ed9c2131fc7fab4d124bee5e29d75e9391d10b120e.jpg)

![](images/2812542653bff8fe1f9ebd220ce130025f71b582646adb89bc6963ee086842a9.jpg)

![](images/2e768e59d7ce39419be34e7b089558dcc8de09af94a490cd0a6acf64aa05a03c.jpg)

![](images/7feeccf4ebe8c1cfa93b8776f295f73bcb4b9b4f9245ee03d2cca23401409f35.jpg)

![](images/b08aaac3c75593e1e8ed1ec9786515cd29acee36f9bcc46e0e1f9e8a1c76798e.jpg)

![](images/603450c6c62694bd679268113bfb6906e5ecf9692e9a425a3edf7c9901d2c6b7.jpg)

![](images/1069f6bdc78995bdc8bbf7b180ad439bdf0457ed322dd7f15d4cc9dead86e302.jpg)

Supporting moleculeCIDD output 

<table><tr><td><img src="images/1cc6ce39014f47a8cf581448f52205824a343589d6f65abb9987aed3ef0fd30c.jpg"/>title: MCCF_ECOLX_1_344_0: Unreasonable vina: -8.726</td><td><img src="images/58ca25ed9f01b3d73a416634b2caa53c06b04a425220b99f7f45a1957f2c6863.jpg"/>title: MCCF_ECOLX_1_344_0: Reasonable vina: -8.947</td></tr><tr><td><img src="images/41dfdd32147c5f66c37a316dedec6f9f58db8bb7a2012e8880b7ea493f424a2d.jpg"/>title: IDHP_HUMAN_40_452_0: Unreasonable vina: -7.796</td><td><img src="images/22ce115e8f937cc0b898ff4b5a69600dbe7fd99c391fbffee987c52e702d8cb3.jpg"/>title: IDHP_HUMAN_40_452_0: Reasonable vina: -11.383</td></tr><tr><td><img src="images/93a2ff1d3938f8b4cb9137786d40b7c0d7b9899bba4bbaf522e4720f2f1c7ee9.jpg"/>title: AKT1_HUMAN_1_137_0: Unreasonable vina: -8.605</td><td><img src="images/f039735b93d9fd276465aa206b3743d1305197cee08e64b34ce17072e65fecf8.jpg"/>title: AKT1_HUMAN_1_137_0: Reasonable vina: -9.926</td></tr><tr><td><img src="images/6402c582628aeabab9125790169e0cb984df00286a9f6a8def97f8b02f390a6a.jpg"/>title: HMD_METJA_1_358_0: Unreasonable vina: -7.825</td><td><img src="images/336b8910c0452b56df0e6f1c736aa8d0b0739b96854cfaa9888d4f9b9fd6734b.jpg"/>title: HMD_METJA_1_358_0: Reasonable vina: -8.55</td></tr><tr><td><img src="images/7d0c9026ad70734e84d594acb0f8754d475033e67f499fd0e995e39160e7b419.jpg"/>title: SIR3_HUMAN_117_398_0: Unreasonable vina: -7.93</td><td><img src="images/06277ffd873260f57dcc17512365addfeb0bddde5c006bc551a371c8131656c4.jpg"/>title: SIR3_HUMAN_117_398_0: Reasonable vina: -10.435</td></tr><tr><td><img src="images/75edfc9a08e33a1fa809de52a6cc5b30f672fbf856cf588938ba4c764f744555.jpg"/>title: DYRK2_HUMAN_145_550_0: Unreasonable vina: -7.961</td><td><img src="images/77bc16b9501c54fd540ec0bebe479a58667b7cad5b1a0d41c19119bc064d0a41.jpg"/>title: DYRK2_HUMAN_145_550_0: Reasonable vina: -8.399</td></tr><tr><td><img src="images/5c01e90efc04b40ecda224884e55979c25c190199a7d579abed519c857f17a8a.jpg"/>title: DIDH_RAT_1_319_0: Unreasonable vina: -9.165</td><td><img src="images/ec96c00e2fea72209983c3642a1c4f28322a0efdce6b063f30b133ffc1c0d37d.jpg"/>title: DIDH_RAT_1_319_0: Reasonable vina: -10.631</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/90026fe32d5fef118a88d6edafac0c7731fffd2fe0f11c73b36ac38b5e800339.jpg"/>title: DIDH_RAT_1_319_0: Unreasonable vina: -8.26</td><td><img src="images/3fd90ac18c03ea1879beac9167939d56d0da85ee4cc67a18133bb674de30642a.jpg"/>title: DIDH_RAT_1_319_0: Reasonable vina: -8.722</td></tr><tr><td><img src="images/f53cf95757617c1a84ad27ecd0f6459daa8b94ae6840249c86b004bbb8f00b6e.jpg"/>title: COAA_MYCTU_1_312_0: Unreasonable vina: -7.572</td><td><img src="images/b201a65c9d7d676060b11f0af3ff41c10ccf079b4fd850df2872f9d1cec91e4c.jpg"/>title: COAA_MYCTU_1_312_0: Reasonable vina: -8.731</td></tr><tr><td><img src="images/738daaa7783fe072009fe26aa15623dd38c7181670635a15a805e5ceee24a949.jpg"/>title: M3K14_HUMAN_321_678_0: Unreasonable vina: -7.453</td><td><img src="images/6056315834d1244237a824abd3ef42a6d94fb2c15dc106a79bad2bc1784e5d97.jpg"/>title: M3K14_HUMAN_321_678_0: Reasonable vina: -9.209</td></tr><tr><td><img src="images/e5f7adc82ec85a2b9c756cb42411854d5e02a7768001852b47ef48c174112293.jpg"/>title: CHIB1_ASPFM_39_433_0: Unreasonable vina: -8.054</td><td><img src="images/24b8943657b388ed9f7cfeba47ea9a95a7fa87659d484f23aff8e1650c118f04.jpg"/>title: CHIB1_ASPFM_39_433_0: Reasonable vina: -10.096</td></tr><tr><td><img src="images/84b4ba079379e6234c068cdaac8ab812676982c4e24263ceaab57c11b4263427.jpg"/>title: SIR3_HUMAN_117_398_0: Unreasonable vina: -6.991</td><td><img src="images/d78b4758e85719b52624b04e4c92b32ca608cc309e1f3b654e509d5f7e819764.jpg"/>title: SIR3_HUMAN_117_398_0: Reasonable vina: -10.758</td></tr><tr><td><img src="images/06745ebe7279da60ea5590a49ac955b893cdef4672df498f93ad418d5cf33824.jpg"/>title: NOS3_HUMAN_65_480_0: Unreasonable vina: -9.583</td><td><img src="images/abf7c850f054e8bff1c934e21cc3aeed129022a0394e87cd0f3742393bb28ef8.jpg"/>title: NOS3_HUMAN_65_480_0: Reasonable vina: -10.652</td></tr><tr><td><img src="images/36514b2410731f26bba6c07c2a801cd4217f116c3d502ce4c6fccf43bf3a5a88.jpg"/>title: DIDH_RAT_1_319_0: Unreasonable vina: -8.503</td><td><img src="images/b76d1f69b1ffb17c98be3de25c72525f4b6c94a452d3d6f5cf6c528f8b82d1c8.jpg"/>title: DIDH_RAT_1_319_0: Reasonable vina: -8.895</td></tr></table>

Supporting molecule  CIDD output 

<table><tr><td><img src="images/deab9c2f8040c24579b836ac9b55b06c3e84c916ed0d174bee228c04b9372bd9.jpg"/></td><td><img src="images/4341064183a11cec211db55f3f921d35f7e5cbf35f9b294330ba824d2f3a199d.jpg"/></td></tr><tr><td>title: BACE2_HUMAN_76_460_0 : Unreasonable vina: -8.586</td><td>title: BACE2_HUMAN_76_460_0 : Reasonable vina: -9.854</td></tr><tr><td><img src="images/18a4b847a4351d096aefe27d4c33bf479fac5f34c3eaeb14f3b54197967427a8.jpg"/></td><td><img src="images/f8ee291454f8069dbad9280ddbd9ec5432a19579c3a74b6f527f18023d832f9e.jpg"/></td></tr><tr><td>title: F16P1_HUMAN_1_338_0 : Unreasonable vina: -8.173</td><td>title: F16P1_HUMAN_1_338_0 : Reasonable vina: -8.633</td></tr><tr><td><img src="images/5e9ba25bdfb974a7d1e53301d13c6c836fdb0e41e6b5dc111c9c2bd2acb0b7f0.jpg"/></td><td><img src="images/23d35e4cb9dd8522434283b7dc15b3b78b2584b9d71a5c3eb32eb04cafdba1b8.jpg"/></td></tr><tr><td>title: CAT_ECOLX_1_219_0 : Unreasonable vina: -9.838</td><td>title: CAT_ECOLX_1_219_0 : Reasonable vina: -10.164</td></tr><tr><td><img src="images/ef87e560f87fd8260cc6dfba91fecdeeb835f6ae9803f8630fe6077135c071e8.jpg"/></td><td><img src="images/4a5bc605d6d810c3abbf9c978cd2164928f8e2213775dd2f49e9a7d24d5c9f7f.jpg"/></td></tr><tr><td>title: DFPA_LOLVU_2_314_0 : Unreasonable vina: -7.208</td><td>title: DFPA_LOLVU_2_314_0 : Reasonable vina: -8.581</td></tr><tr><td><img src="images/769b8ecbf46233b20592b8d9ca89d994231288e14b64e1a23832c86981446030.jpg"/></td><td><img src="images/c394c8eb241c731e2d17663610a0f7935035850f104f447273c7804e27caa5c9.jpg"/></td></tr><tr><td>title: QPCT_HUMAN_33_361_0 : Unreasonable vina: -8.178</td><td>title: QPCT_HUMAN_33_361_0 : Reasonable vina: -9.527</td></tr><tr><td><img src="images/c4a22e2f46673323ca9006e9099f4ff319a0bf104dc01bced9e0f15ba3cbbc34.jpg"/></td><td><img src="images/6a8a279f24616b23f405cd50767dea365b5eb946e51f5fc233643f1fc5296f7a.jpg"/></td></tr><tr><td>title: KS6A3_HUMAN_41_357_0 : Unreasonable vina: -8.242</td><td>title: KS6A3_HUMAN_41_357_0 : Reasonable vina: -8.738</td></tr><tr><td><img src="images/5845f482cbb482a4184eac0359de4164fa5a8fed4df73db5603f7fb4aab32665.jpg"/></td><td><img src="images/1e4d60ef865af47451d0512102538ae20e71ee53ba6a6fd43b5f8f3c3d4d32d9.jpg"/></td></tr><tr><td>title: AROE_THET8_1_263_0 : Unreasonable vina: -8.741</td><td>title: AROE_THET8_1_263_0 : Reasonable vina: -8.794</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/f469eb8c5cf9d457d5b313dcba356577ef11de0e3f27ca2c5e39cd486c86f118.jpg"/>title: GRK4_HUMAN_1_578_0 : Unreasonable vina: -7.158</td><td><img src="images/ec0e829e7cc9c53e68fda42ee459c3f810b5b259086236a9718392f7c48debfa.jpg"/>title: GRK4_HUMAN_1_578_0 : Reasonable vina: -8.93</td></tr><tr><td><img src="images/7c59a031fdd7bfc9b50dd18d39bcac25d9c579e9509952182ca5d0225dcd45b6.jpg"/>title: CPXB_BACMB_2_464_0 : Unreasonable vina: -10.201</td><td><img src="images/4fe11a5d235dcc4d55e2f18a17f3199e6fcaca0caf302b3198fb0e50b7bc0d2a.jpg"/>title: CPXB_BACMB_2_464_0 : Reasonable vina: -11.121</td></tr><tr><td><img src="images/b7358e323c47074e59379ea1fe18e708233394ef737e2dfe50197a02e9f43e39.jpg"/>title: BSD_ASPTE_1_130_0 : Unreasonable vina: -7.492</td><td><img src="images/a1411ce4a9c098d8a78a5cb8d30ffebc948e7ce6de705b9f34ef528c50a6b4a6.jpg"/>title: BSD_ASPTE_1_130_0 : Reasonable vina: -8.786</td></tr><tr><td><img src="images/9b7f7d5be2477cee47d2eaca40dca8c3769b83cfa89cca57d2985f85e7e63627.jpg"/>title: RG1_RAUSE_1_513_0 : Unreasonable vina: -10.06</td><td><img src="images/79ed8695ac9cbc1e3d3612138521e5627f721cb2dc0c3a60b8d99269fdabc9d4.jpg"/>title: RG1_RAUSE_1_513_0 : Reasonable vina: -11.978</td></tr><tr><td><img src="images/32f4eb650c38960d8621a667868993f2940a8aa09d352fce644ecc011a822a51.jpg"/>title: QPCT_HUMAN_33_361_0 : Unreasonable vina: -7.531</td><td><img src="images/8a1535043126219fbc6d873c17e312c723b91528e33cc6e06b3a40402872dc5b.jpg"/>title: QPCT_HUMAN_33_361_0 : Reasonable vina: -8.356</td></tr><tr><td><img src="images/3ff94ef6765caf0e19f1d98ec27466649ad267225b63825b698f5c25b668fce5.jpg"/>title: GUX1_HYPJE_18_451_0 : Unreasonable vina: -7.25</td><td><img src="images/848e0ff1aab7452fe732e3af420c0ea3c71707b00a439f4476f40aef8fc2f857.jpg"/>title: GUX1_HYPJE_18_451_0 : Reasonable vina: -8.375</td></tr><tr><td><img src="images/2018962ce0f1bc4844154d16a7ee1962383f7532c15c94c375df42bf85abf692.jpg"/>title: UPPS_ECOLI_1_253_0 : Unreasonable vina: -7.288</td><td><img src="images/7ebe0628112571e7479ab6c909a3956f3c0ee87369aab649655d446315b72315.jpg"/>title: UPPS_ECOLI_1_253_0 : Reasonable vina: -8.315</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/d433808810eef89f99e1064b221bdb09d9a25a45e4c2cbb5cf8efcc0bb2b9b12.jpg"/>title: CAT_ECOLX_1_219_0 : Unreasonable vina: -9.836</td><td><img src="images/9addb47789af0802d6d8cf62431733e1f5799de0fd81dc43cf02ff661125eebe.jpg"/>title: CAT_ECOLX_1_219_0 : Reasonable vina: -11.246</td></tr><tr><td><img src="images/843ad94b4c9fdf6ae49537ee2515c669fb560850e5a672802c5dd52e9326ef6f.jpg"/>title: NOS2_HUMAN_78_505_0 : Unreasonable vina: -10.504</td><td><img src="images/2f5d8a5737ff63900d585e352456599ce510f0d45fbdd71d3f76ffad39d49aa3.jpg"/>title: NOS2_HUMAN_78_505_0 : Reasonable vina: -11.006</td></tr><tr><td><img src="images/f06f74b914b762b43a43e1c23d75c6333cb920e3d0fe54bef54cec877e9a764e.jpg"/>title: BTRN_BACCI_2_250_0 : Unreasonable vina: -4.306</td><td><img src="images/51a6a8abfcc1cd766a5d00df50bf11daccf27ba988cf80bebfd705d13ae1b1a9.jpg"/>title: BTRN_BACCI_2_250_0 : Reasonable vina: -11.729</td></tr><tr><td><img src="images/368f35cf07397bd9cdee2fa9ef0b3099288089657b81fee91b1ab5997a817d83.jpg"/>title: ACE_HUMAN_650_1230_0 : Unreasonable vina: -9.498</td><td><img src="images/53468b0056444a744e1a100f203690cfaa5deaf82e52d0c22d0880ec7c85982a.jpg"/>title: ACE_HUMAN_650_1230_0 : Reasonable vina: -10.987</td></tr><tr><td><img src="images/a9f53d43b495517abe499225acfce882e4c49c94923c2439147a61d456c1f100.jpg"/>title: AKT1_HUMAN_1_137_0 : Unreasonable vina: -11.185</td><td><img src="images/e5b30536e7a3cd47102e128b2eb7752a9b16b1ba4c181323583746590ed21f83.jpg"/>title: AKT1_HUMAN_1_137_0 : Reasonable vina: -11.293</td></tr><tr><td><img src="images/ff4b7f7dc9b68b844a893df104c613fb7fe16c81b254f67a9c15db9af7354bd1.jpg"/>title: BAPA_SPHXN_30_402_0 : Unreasonable vina: -7.681</td><td><img src="images/f543a6f7769cd6316c0f381475374749cea9cd8f3c6c2591336297a25ed77046.jpg"/>title: BAPA_SPHXN_30_402_0 : Reasonable vina: -8.683</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/bf4070bb283c486e4ab34729c63443ba64f9fe56e8f10a72eecabb82d0eed93c.jpg"/>title: ATS5_HUMAN_262_480_0: Unreasonable vina: -8.133</td><td><img src="images/d8387ffeeccddbae0f543d1162b5fa8efb70613503321fe48e5eb9c5a213d9b4.jpg"/>title: ATS5_HUMAN_262_480_0: Reasonable vina: -8.863</td></tr><tr><td><img src="images/4962bbb7aab234cc0f3f4d61568fd164a9b3fb124ff19f258f279fa11bc7ca7a.jpg"/>title: NOS2_HUMAN_78_505_0: Unreasonable vina: -10.76</td><td><img src="images/41ae41d42fc1e0b94c677b3b64a94404e4b4c972b49c95dc69531c3570b5b38e.jpg"/>title: NOS2_HUMAN_78_505_0: Reasonable vina: -12.037</td></tr><tr><td><img src="images/8a9ed73f4f6264f2619be904e05a83e7257ad23db7952060e268de538694a74d.jpg"/>title: ACE_HUMAN_650_1230_0: Unreasonable vina: -8.564</td><td><img src="images/f30cda7c399cab48516920282d46f2cf55d891f2785b9b1203536dc60715849a.jpg"/>title: ACE_HUMAN_650_1230_0: Reasonable vina: -10.503</td></tr><tr><td><img src="images/01c670a87e07487b917b8f83df4d5e72246e45724c6aba4ea17d7c6ef8e523e8.jpg"/>title: ACE_HUMAN_650_1230_0: Unreasonable vina: -8.69</td><td><img src="images/3ba6049e7834b97b36dc80e23a8c24dc8878eb46506fd6bec3b7f54d49860f67.jpg"/>title: ACE_HUMAN_650_1230_0: Reasonable vina: -8.905</td></tr><tr><td><img src="images/60133b530832ff46a34357800b601db8b454f3ac6b192f24f97e8889f6a1792a.jpg"/>title: TBK1_HUMAN_1_303_0: Unreasonable vina: -7.693</td><td><img src="images/b8a59babbcd0d9a6ce4770d3e49069fb62b4f6b34e422e4c7e53c316f2817bb0.jpg"/>title: TBK1_HUMAN_1_303_0: Reasonable vina: -8.868</td></tr><tr><td><img src="images/fdc3751b7051a58f3cc4a9daf28c824fd044a7b065e491c1e596557cef8e4bb7.jpg"/>title: BAPA_SPHXN_30_402_0: Unreasonable vina: -7.794</td><td><img src="images/b7d5a6f7c7ba284d0c78c06862f86b5f6e2ab6b8e346ffe25787116efbbad9eb.jpg"/>title: BAPA_SPHXN_30_402_0: Reasonable vina: -8.198</td></tr></table>

Supporting moleculeCIDD output 

<table><tr><td><img src="images/b5e1c09dcdaf551a288cd4bbf8b515e7467e3c180941779ae1eb12ee2f7e5500.jpg"/>title:PHKG1_RABIT_6_296_ATPsite_0:Unreasonablevina: -8.922</td><td><img src="images/81e353f4070306734ed21aa3d749d2f7cb6671a279a02a9b924acf920e735e8f.jpg"/>title:PHKG1_RABIT_6_296_ATPsite_0:Reasonablevina: -9.205</td></tr><tr><td><img src="images/06d57230062ea870563562cd1d5e19751c52930fe100ca2d8aeffdaa3cd7cdbd.jpg"/>title: RG1_RAUSE_1_513_0:Unreasonablevina: -10.484</td><td><img src="images/be3498b2acd307e1e85aca6d4fb68fc42a20c45d14bb3c9c29040385426efc29.jpg"/>title: RG1_RAUSE_1_513_0:Reasonablevina: -11.024</td></tr><tr><td><img src="images/0dbaac942b1fcb40fea3b77ef253eefdaed37af75994b6e0acc161f563a36e78.jpg"/>title: CD38_HUMAN_44_300_0:Unreasonablevina: -8.72</td><td><img src="images/788a9bf5cd7a7ea64fb43950b3a8c9d706645f0af322d2288e1c2718ea2d0353.jpg"/>title: CD38_HUMAN_44_300_0:Reasonablevina: -9.327</td></tr><tr><td><img src="images/409e7402e80dc5c6a5771de5ae9ee01468d8fb621e8a954e76316cef5747a12e.jpg"/>title: XANLY_BACGL_26_777_0:Unreasonablevina: -9.053</td><td><img src="images/4ba0598ebc0511f95bfce12b842063e186461fa5ac1d0fc6fe717e942e1d27aa.jpg"/>title: XANLY_BACGL_26_777_0:Reasonablevina: -9.483</td></tr><tr><td><img src="images/88978a36b25a4540616255cf96bc4f4be81b0cf3c7af1a47751dc3f306a65ec0.jpg"/>title: PPIA_HUMAN_1_165_0:Unreasonablevina: -8.023</td><td><img src="images/fb36235347f8dce4a71fa1705fefa80dc3aa9e49b0affe3b52d376b2d1c18903.jpg"/>title: PPIA_HUMAN_1_165_0:Reasonablevina: -8.605</td></tr><tr><td><img src="images/039079549d0d7c776ccef69e9bd857b95d0402a168b8f9d42b52096e9833c011.jpg"/> <img src="images/2f4a55005199178084b13e76b0bc89854bb9b8a5c7126d1e0fbf9e6fb0071bac.jpg"/>title: SQHC_ALIAD_1_631_0:Unreasonablevina: -11.51</td><td><img src="images/2f4a55005199178084b13e76b0bc89854bb9b8a5c7126d1e0fbf9e6fb0071bac.jpg"/>title: SQHC_ALIAD_1_631_0:Reasonablevina: -14.292</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/dc9bf91f743de317de28f53c5e561eb00538ba2b6f1d42d8d152abe4c08c5d6a.jpg"/>title: BGL07_ORYSJ_25_504_0 : Unreasonable vina: -10.446</td><td><img src="images/5a040625cf8f23d28d4efb1d20a27c47f44e1227dde4715dc8bba615fe3a2278.jpg"/>title: BGL07_ORYSJ_25_504_0 : Reasonable vina: -10.592</td></tr><tr><td><img src="images/0729c6d8f06a4dc78d4eedef7852e3e9c173462ee3bb200ff8a68896bae6904a.jpg"/>title: DPP2_HUMAN_27_492_0 : Unreasonable vina: -9.855</td><td><img src="images/cfc2940f272ba1d40fa6181ee0758fe44619c80a5a909c372c63eb57578786c2.jpg"/>title: DPP2_HUMAN_27_492_0 : Reasonable vina: -11.224</td></tr><tr><td><img src="images/e7cf82b89aa5ccfd9196b22ee1053a6c245882e7bef235bff135c7d9bd25ff10.jpg"/>—title: PTGIS_HUMAN_20_500_0 : Unreasonable vina: -8.318</td><td><img src="images/84b60d8d3c0d6611aa7e1ee30097f69b84afc880d3417ad913c5290787fa0283.jpg"/>—title: PTGIS_HUMAN_20_500_0 : Reasonable vina: -9.448</td></tr><tr><td><img src="images/a1a4f83e20e8c53ae57f6c181d397d2ba0c1c094a505202c5737bf9d3d3893a6.jpg"/>title: PPIA_HUMAN_1_165_0 : Unreasonable vina: -8.777</td><td><img src="images/fa8d30c6cee964cac40b202a307ae747f5df149a9f7642568ebdfcfacee1f30e.jpg"/>title: PPIA_HUMAN_1_165_0 : Reasonable vina: -10.083</td></tr><tr><td><img src="images/18caf96dd25ff637accd8e669f607d623d9d3b854c381f37d4827a8d4f84446d.jpg"/>title: HMD_METJA_1_358_0 : Unreasonable vina: -8.349</td><td><img src="images/41f893fcd0d8cd676f5bfd8e7bfb313af4e1ff4cab5ee26c8b10e04f5c9040d2.jpg"/>—title: HMD_METJA_1_358_0 : Reasonable vina: -9.593</td></tr><tr><td><img src="images/87b960d2b5ed2b1b6bb89ce4fdf54756f31cfdad8017f48815be3808ba0998ef.jpg"/>title: KS6A3_HUMAN_41_357_0 : Unreasonable vina: -8.967</td><td><img src="images/403107dc2d4cd23784dc5f465bb61c5481c6dbaccb0ffe2e08a17d10bfadcf43.jpg"/>title: KS6A3_HUMAN_41_357_0 : Reasonable vina: -11.101</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/53b2bab7ba176efb9ed3f3af7d7a20c98c9938443261a2c813657e8726488620.jpg"/>title: KS6A3_HUMAN_41_357_0 : Unreasonable vina: -9.414</td><td><img src="images/17db68af3f879b1fa749b09097d81da74ec4516b4492b286679d5b11fe823f4d.jpg"/>title: KS6A3_HUMAN_41_357_0 : Reasonable vina: -9.746</td></tr><tr><td><img src="images/c35f6f1ab1e783bec884a6523ae5d38fdb1e5ac84b46e3b44e1bcf12d6418c08.jpg"/>title: NR1H4_HUMAN_258_486_0 : Unreasonable vina: -3.528</td><td><img src="images/8e893586970ac598e1835b8638e140f830b2694ecb5a5307f943c14ea4e469ae.jpg"/>title: NR1H4_HUMAN_258_486_0 : Reasonable vina: -14.043</td></tr><tr><td><img src="images/fc6287d8aa5a23763d21f7df3693fddc2dc698cd2cb6dce73be4e173b91e68ac.jpg"/>title: SDIA_ECOLI_1_171_0 : Unreasonable vina: -10.997</td><td><img src="images/e8d177f0d04a95651aa4d2db13a674dc2c873745c4b399564f8c179c3bec1d33.jpg"/>title: SDIA_ECOLI_1_171_0 : Reasonable vina: -13.15</td></tr><tr><td><img src="images/04a73c47ab2b271f2d6952d4ed2bc63bb86d4a19c676ea15cc88a8bf19171946.jpg"/>title: HDHA_ECOLI_1_255_0 : Unreasonable vina: -9.845</td><td><img src="images/427e236161624f54ad2a48a8ff6802e87385443688907ffd2e263b3b9abbda29.jpg"/>title: HDHA_ECOLI_1_255_0 : Reasonable vina: -9.957</td></tr><tr><td><img src="images/c599584a74440c492adeb1b5661f3e6ada0cb182525c91863f4360674a130f4c.jpg"/>title: IDHP_HUMAN_40_452_0 : Unreasonable vina: -8.034</td><td><img src="images/33bf6d920e352f8e7a949ae738968d0a0da5d64e69e131c1c412c1378fd2f0ec.jpg"/>title: IDHP_HUMAN_40_452_0 : Reasonable vina: -10.368</td></tr><tr><td><img src="images/8d51cdb2637469055e769856aedf040b4ecb296886d92961b40fa300b2737505.jpg"/>title: AKT1_HUMAN_1_137_0 : Unreasonable vina: -10.124</td><td><img src="images/33b2a9ea4f2c4a41c5360a7baf5c4ae1ac40fdf3269923a995888ec3e2d75ecb.jpg"/>title: AKT1_HUMAN_1_137_0 : Reasonable vina: -10.13</td></tr></table>

Supporting moleculeCIDD output 

<table><tr><td><img src="images/7a5de8345d4e7ee9a8b0b950dc6960e0cebbad723690c4c9432d0c4e359363e1.jpg"/>title: DYRK2_HUMAN_145_550_0 : Unreasonable vina: -6.725</td><td><img src="images/525d834afb52c9524bec85764f6ebb2acfdf9150bbec36244b0c4ec5b3a18a69.jpg"/>title: DYRK2_HUMAN_145_550_0 : Reasonable vina: -9.337</td></tr><tr><td><img src="images/7c9eaf1442a56f8aae4bc1c8a8bb0d4ea9da198095310fbd152b4496e48d1b22.jpg"/>title: BACE2_HUMAN_76_460_0 : Unreasonable vina: -9.145</td><td><img src="images/aa4ee559438e311e2d93336832d1b8a1f920c2041d82c7719177b4fd6bf3c59c.jpg"/>title: BACE2_HUMAN_76_460_0 : Reasonable vina: -9.806</td></tr><tr><td><img src="images/20f8231eda4810665231e580b3a1ab17eec263b450028e6c9f8462efc4a95430.jpg"/>title: TRAR_RHIRD_1_234_0 : Unreasonable vina: -8.935</td><td><img src="images/9d0e9c74d2e5c7729732e0bc4388e84ebf49f5299482497e6ad65571beb2cca9.jpg"/>title: TRAR_RHIRD_1_234_0 : Reasonable vina: -12.018</td></tr><tr><td><img src="images/9d4ef36bb9c369b98dabdda92fdc22107888a66b2a51d462bc3f8ab0d51e7874.jpg"/>title: UPPS_ECOLI_1_253_0 : Unreasonable vina: -7.717</td><td><img src="images/a2e16db5db6878762356b5bfdff3f1f8b4a0a95320800bfc659a68cda1c6892d.jpg"/>title: UPPS_ECOLI_1_253_0 : Reasonable vina: -10.031</td></tr><tr><td><img src="images/5a86f798bde39c33d61c5a1fca5ec98181bfab8d8e605cf1636abde4ffaf4a0e.jpg"/>title: ABL2_HUMAN_274_551_0 : Unreasonable vina: -10.488</td><td><img src="images/180a717d4035bd0e4324c0b620cce67a4b5fa9c95789e97cfe7f0c8090af7281.jpg"/>title: ABL2_HUMAN_274_551_0 : Reasonable vina: -10.776</td></tr><tr><td><img src="images/1bd1f9173ae17478c5b71f4821c5bc962d29644c6de65d84366e7588ff96593f.jpg"/>title: : Unreasonable vina: -10.487</td><td><img src="images/ae27265659a043b9deea72e6ad22f458b52d105bcbcce15743effebde1cc4775.jpg"/>title: : Reasonable vina: -10.893</td></tr></table>

Supporting molecule CIDD output 

<table><tr><td><img src="images/9bd331273501f61c339aeaddb3d7508877377a64647a8ad702091fee264808ab.jpg"/>title:MURA_ECOLI_1_419_catalytic_0:Unreasonablevina: -8.295</td><td><img src="images/25591b9b0e59fa81badb934f071626671abf0095a8b144964401c1453c24f000.jpg"/>title:MURA_ECOLI_1_419_catalytic_0:Reasonablevina: -9.241</td></tr><tr><td><img src="images/95e5edd385551b8251c08921155d1fd1f1995b0c4c0c1c84469126cdcbddc47d.jpg"/>title:BGL07_ORYSJ_25_504_0:Unreasonablevina: -8.028</td><td><img src="images/1d65b2b7120259749bfa032f6dccf977a8fb9d66b17732e4ead5bf5d562bf9de.jpg"/>title:BGL07_ORYSJ_25_504_0:Reasonablevina: -9.632</td></tr><tr><td><img src="images/a6931fe01642ee7cbfae30bd407eee4946ac570848d0678af7c2d84ca5603e7a.jpg"/>title:PAC_ECOLX_27_846_0:Unreasonablevina: -9.538</td><td><img src="images/411d39425b6af0fe78b70f49ef46066cf2588b5aea19ba00e94b741e7c727a2e.jpg"/>title:PAC_ECOLX_27_846_0:Reasonablevina: -10.042</td></tr><tr><td><img src="images/c30166c5be4dbce3dce349a846994cf9935606160a544ea51baa4977a180607c.jpg"/>title:EXG1_CANAL_41_438_0:Unreasonablevina: -9.965</td><td><img src="images/282f568039f0ef9ef7aa19e35f4f2c635d55836299aed88ad392c1ae709aaee9.jpg"/>title:EXG1_CANAL_41_438_0:Reasonablevina: -10.569</td></tr><tr><td><img src="images/26bd06dead453e36c3db366161da0846e047e778a8b0c9a2bf52be9c366ac737.jpg"/>title:CHIB_SERMA_1_499_0:Unreasonablevina: -9.972</td><td><img src="images/fc48d4a5b0966a6dd3bd67a6a122e24e2ff958de2001c71744e667f70f545bd0.jpg"/>title:CHIB_SERMA_1_499_0:Reasonablevina: -10.354</td></tr><tr><td><img src="images/c93b67e3d2d6eac998b94fda10f78cd244bf28853ff06806e7ae6231658728e8.jpg"/>title:SDIA_ECOLI_1_171_0:Unreasonablevina: -10.933</td><td><img src="images/ff9d8328998e21a8182e81c0b273ceb1557f8183f348344305d097b9468033e0.jpg"/>title:SDIA_ECOLI_1_171_0:Reasonablevina: -11.339</td></tr></table>

![](images/6333a45cb9d8c9d35f8bc5ccade537e6247f97b65c2f5be67abbb93ad8c6c38c.jpg)

![](images/9fe5ce753e33b99f6abf3e37ecf7b0470148f4d3844675eef4cfa5deb89c7e1b.jpg)

![](images/7e3f811b7d1b7fa5c1aeaba21155cee329757c009fa1ef744c05d2d1c625fb92.jpg)

![](images/e1a687b02a7deb23786ec2c36c3609eaa33a3517c0af063f2edfd8eb00d837bc.jpg)

![](images/19d6a7309485386b766efa81cb4ab37b4e0a06391aedd8ca5c0753007c3bd155.jpg)

![](images/d4ff187e051344a82b17ba81a87e8281cb985026b8c993156978e8af703ee20a.jpg)

![](images/60c1cf8d01d1e10ee725116e16283f4abe9169abebd6801e11ee5fd5ff3a0a7d.jpg)

![](images/c24f98776acd2d2098c8714a43954910992989715021594f82dd87fb3aa307db.jpg)

![](images/ea62adbe697fdde5991ada308073a54d617622d63c6b84f3f19d552cda4af2f2.jpg)

![](images/55b8742855b7ec0712cafc352597a5cc064b60dcb7af890c4ce66426bc56c023.jpg)

![](images/915b17359918c906194eff47cb094012e8b01b6fa1849e9c1faf9abc5bbd7398.jpg)

![](images/3986e615bbafca3364c80248bef4cb0cffc4f3fbed4eb3b90b45d1955da1d076.jpg)

Supporting moleculeCIDD output 

<table><tr><td><img src="images/effdc1b20ec7865b0c0b6dee9cc442c47512a41e5bc805da3c30ed757e1c72d0.jpg"/>title: HDHA_ECOLI_1_255_0 : Unreasonable vina: -8.511</td><td><img src="images/0e0db2485fbc1e295e722bed17f89663ad58a591ce70abc06cadae4753514ba3.jpg"/>title: HDHA_ECOLI_1_255_0 : Reasonable vina: -9.995</td></tr><tr><td><img src="images/419166a6ad43096623aaf347fcef2becdd474357eda6354474dd00a37e592ed7.jpg"/>title: IDHP_HUMAN_40_452_0 : Unreasonable vina: -8.039</td><td><img src="images/4787ed2e90bbf9c80cb742e6c973e2c54cff24ee61cf0dcf51ce0f5340538659.jpg"/>title: IDHP_HUMAN_40_452_0 : Reasonable vina: -9.819</td></tr><tr><td><img src="images/e243e51c9495d43aca08df0ef646fd3e1cd2279d641f11efa2c46a4a1a24cfbd.jpg"/>title: NOS1_HUMAN_302_723_0 : Unreasonable vina: -9.495</td><td><img src="images/6ff6c77eedc6b6f5def67afb219b4f1d5dc3cc3ee490b21afe6cdc7e8a41ad80.jpg"/>title: NOS1_HUMAN_302_723_0 : Reasonable vina: -9.579</td></tr><tr><td><img src="images/5c25b9c370a778bbb9081125778c975b099124b66ed1d2a84ad8da8e2f1ee023.jpg"/>title: CAT_ECOLX_1_219_0 : Unreasonable vina: -9.2</td><td><img src="images/c1cd4ccd6a6d24d2058d0453dc4d6a661cb42495f1f7afc9cec26c467c136dff.jpg"/>title: CAT_ECOLX_1_219_0 : Reasonable vina: -13.057</td></tr><tr><td><img src="images/a28edd46dcba4afc96c77cfa11fa002dd25848d7c6185c007dff22ab81bc9c63.jpg"/>title: ABL2_HUMAN_274_551_0 : Unreasonable vina: -10.702</td><td><img src="images/6682b825bb443abdb3fc6fcaa9155afd29957323002dc526f85c462a4a038f0c.jpg"/>title: ABL2_HUMAN_274_551_0 : Reasonable vina: -11.583</td></tr><tr><td><img src="images/2925196b6a0c07d02c6c7834413688a0f4d315236225e5bdc1068fe9c1da8fdb.jpg"/>title: BTRN_BACCI_2_250_0 : Unreasonable vina: -8.786</td><td><img src="images/c9ef825d0c6c90733f6fcfb9065b774617c2d15cdc6d035f0abd5a123c55b48e.jpg"/>title: BTRN_BACCI_2_250_0 : Reasonable vina: -8.951</td></tr><tr><td><img src="images/6a232b4c54fcbcb691d45f635d8020154ad4afd77ea7163b6554b7cd788417ab.jpg"/>title: AKT1_HUMAN_1_137_0 : Unreasonable vina: -10.1</td><td><img src="images/790e93f7b617f04338a35d6bec16e44b970d83a56876cb41336ba4b6827928d6.jpg"/>title: AKT1_HUMAN_1_137_0 : Reasonable vina: -11.478</td></tr></table>

![](images/7226d7bbe198004b05f73d8da3f386844cba684c91aa7583a0ec63bc4041a46c.jpg)

![](images/49728e74502af043afe5cf15cedce050e19d0a9c73a0409985dd345378bd97c7.jpg)

![](images/ce5d6003cb024130626bf5e0475ab943ca1b9a354fb2c9ab35dff31723541b49.jpg)

![](images/ac8b6d3f69091631a0e21d2ce84ccb3e185fe851f6fc00882173ec714f1bd254.jpg)

![](images/5ce96a3a01df3e89370276f4dcdb61f478777464493e3bd254d80bf2c7b348bc.jpg)

![](images/17fd9a48cbefe6d2200acc2ca480610c394dd374b20bd2fa81f08bc74d8d95f8.jpg)

![](images/ed309ee68e52bc292242fbea7f5b5d3d49290586e9f3340e0319800062f17c74.jpg)

![](images/70d200ea25feb7bc532ca5562f94112e0cba96ac28cba2db864ba3521ee5a14e.jpg)

![](images/a32364e92fa3e1e3c37f71ec13efc07f80b38c880768adc228fb4eb7277bd63c.jpg)

![](images/fcd87f39dbfc814f9fd4962327f6e044601ce340294827f537d5fd30a8558bff.jpg)

![](images/09821579394a414510b6c7a84486c6d352d72ac5b6c549e412b908a221ba39d7.jpg)

![](images/ff357f23b328f1cc4b23261a31b8a281be76df5af259c9ce77a4ee84172569f8.jpg)

![](images/e99c47bcd82de77e57fc1538d60884dbb1fbf1f20921a681b015887cebe15513.jpg)

![](images/1cac5ad782883a0db1d3bd1915a4369107efffc5bf1fd3c7b9a3ae5ec9ab89b4.jpg)

Supporting molecule CIDD output 

<table><tr><td><img src="images/8eb1d19a5dd44b1077ba1150c7ff927df99dc8f8a324a913d25b31e6faa716b9.jpg"/>title: PA21B_PIG_23_146_0: Unreasonable vina: -8.391</td><td><img src="images/f9778e1da9b11e5e30e22df443935f009f8f8311c10a04b37b4833873774f3e7.jpg"/>title: PA21B_PIG_23_146_0: Reasonable vina: -10.029</td></tr><tr><td><img src="images/6934871fe06146213fa0e8d3183b3cd8e7a8620461a221fe556173032ab09c7e.jpg"/>title: M3K14_HUMAN_321_678_0: Unreasonable vina: -8.948</td><td><img src="images/04c6841ee267c29dccc6ccaa2de2d5200176a7c550e57844f9902cf2d93ae8a9.jpg"/>title: M3K14_HUMAN_321_678_0: Reasonable vina: -9.001</td></tr><tr><td><img src="images/d556e9ccec2335d250ba3642ad310779e378e74a7b96d0998abbfe6052b5f527.jpg"/>title: PTGIS_HUMAN_20_500_0: Unreasonable vina: -7.955</td><td><img src="images/2a17f6219265b7f56662aaa63ae09e3b4c7c2f46cb9196bda38690c431f0fdc2.jpg"/>title: PTGIS_HUMAN_20_500_0: Reasonable vina: -9.193</td></tr><tr><td><img src="images/704202b170dbd9f9b0920c5a612a5829411f18f67b002bec9eb75968e1abf1e9.jpg"/>title: PAC_ECOLX_27_846_0: Unreasonable vina: -9.272</td><td><img src="images/7e2dd7e97b0dcae3b369990e96e12e7f8325f35e85812b85b6486aa888d4d6d9.jpg"/>title: PAC_ECOLX_27_846_0: Reasonable vina: -9.421</td></tr><tr><td><img src="images/777f51c46280c02a82af4910fd9e242bebfd2fdf8eab54d683aa22c1504f1e10.jpg"/>title: XANLY_BACGL_26_777_0: Unreasonable vina: -6.991</td><td><img src="images/b4d5edfde8a1373e1f8b7195c562e7d900b9695c0cf4dd60b1cea07d449c6069.jpg"/>title: XANLY_BACGL_26_777_0: Reasonable vina: -8.994</td></tr><tr><td><img src="images/6f8e07dfd060c48543d030c996ca59a2c0f8a0ae0149c541769a5adc22c08ed4.jpg"/>title: PPIA_HUMAN_1_165_0: Unreasonable vina: -7.765</td><td><img src="images/fd61b3b5fc72edb6d6e8fc6052be64e0576aec5722019b10dea4cf678d547e38.jpg"/>title: PPIA_HUMAN_1_165_0: Reasonable vina: -8.447</td></tr></table>

![](images/9cc4c68d4ecbc8306e37600edbfe204070e085b3b0444a3b7265cc3c4ff9285e.jpg)

![](images/d9a5c342b8b2f1a92ad34f2eac80dc064f35195f0d5ba4fe2e63a2e0d9c449a9.jpg)

![](images/71373cbc308221c4c822c6b26eb3c0c329d552191561b04f246d6ea8b3fbcb2b.jpg)

![](images/5712313ff84ce03c337b6f9a4c00deee8650738efe0a83e37dd43568e44802a0.jpg)

![](images/239f4eb25ff9f26c5750b1c678654434898edb98187c646c8f4b6a8f93c78133.jpg)

![](images/00ea02e8f8fffa407638a8eae160299c94d2a08a6184ef89dc22f5b2ddbebd6c.jpg)

![](images/7f8c597ff2edd4ca94f01b0d513647c8e969f8f9bdc805b39bada743b504a67e.jpg)

![](images/7a99f7570c6ae51537bd82b4fc39182c2546b29e12992b29aa2eab9df7763745.jpg)

![](images/1f1ccf4c1361173c11030f6ace78ff75721bf36a38dab2e7d07243f57841b1dd.jpg)

![](images/ad9674bfdc808126d89479470458aa00508f59d2dec0131bca82b60cbf441964.jpg)

![](images/5cb27a94cc63444ab385def89f93da753e4ba565687c257229bcc0b949bc5287.jpg)

![](images/522e50e98996c31779448c65f1f50ddb4162f7b775ff4f130e43454e877bc525.jpg)

Supporting moleculeCIDD output 

<table><tr><td><img src="images/fc8255edd231257295eeeb8eeba68c5ab4fdfc1e1f8331f6c7f2c3bc772463ec.jpg"/></td><td><img src="images/65f9e457292f7ca2d4c8c214e4fbdd8aaa8c215c790c82054b8d0948bd3e32d5.jpg"/></td></tr><tr><td>title: P2Y12_HUMAN_1_342_0 : Unreasonable vina: -8.31</td><td>title: P2Y12_HUMAN_1_342_0 : Reasonable vina: -9.509</td></tr><tr><td><img src="images/2dd48a5dbc62a51ce1c427bfbc6889f4bc49fbcf1edb21be56fc457b82dc57c4.jpg"/></td><td><img src="images/f76a132c2a4187f5ebb42118f6711096b34d2cab6987bd7a74d2ad93331511db.jpg"/></td></tr><tr><td>title: MENE_BACSU_2_486_0 : Unreasonable vina: -8.029</td><td>title: MENE_BACSU_2_486_0 : Reasonable vina: -8.629</td></tr><tr><td><img src="images/1c8ec86adfb058dffd229e15575ef47d157d3db43f62a4d350d45da6f2f35c01.jpg"/></td><td><img src="images/297334651e5f061f8d6f98799938a4b444a16d787a7313d3d67c3be98f3b8dee.jpg"/></td></tr><tr><td>title: CHIB_SERMA_1_499_0 : Unreasonable vina: -7.389</td><td>title: CHIB_SERMA_1_499_0 : Reasonable vina: -9.388</td></tr><tr><td><img src="images/47cd7dc55e479b0204ee20a7ce90deedec5b9dc33e296346efcbe61912c2c941.jpg"/></td><td><img src="images/0b34f75f012abd7d6d2d9ceeac3791ca29e2a775a144392abb16873bb5218c1b.jpg"/></td></tr><tr><td>title: DYRK2_HUMAN_145_550_0 : Unreasonable vina: -7.898</td><td>title: DYRK2_HUMAN_145_550_0 : Reasonable vina: -9.098</td></tr><tr><td><img src="images/51edb3f0127ccd458710d355467ca1eab750a8111aec52040f35a89f61fbd71b.jpg"/></td><td><img src="images/03bab2c426ecfdb35d0a69ad3c05fa97da808c958faaa0753d95e3ebb44c7ae3.jpg"/></td></tr><tr><td>title: NR1H4_HUMAN_258_486_0 : Unreasonable vina: -8.974</td><td>title: NR1H4_HUMAN_258_486_0 : Reasonable vina: -9.969</td></tr><tr><td><img src="images/44631a1a74136ce06deeaf38ee5fb220d14e32cef1b3eb81ff02f7a1426610e5.jpg"/></td><td><img src="images/0063f11476fc44302ec10c3c0c8ad21ae0a3a34adccdedaed3359f2559d9158f.jpg"/></td></tr><tr><td>title: BACE2_HUMAN_76_460_0 : Unreasonable vina: -9.473</td><td>title: BACE2_HUMAN_76_460_0 : Reasonable vina: -9.828</td></tr><tr><td><img src="images/744253c4c07b9968c09c31fc8db1e59a8f4ba6ca4256eb8232e2f75abb12101d.jpg"/></td><td><img src="images/e3e8fce2af4745f83482ee0f475f17d31f947fb53e32cd931d824ce876f8beca.jpg"/></td></tr><tr><td>title: TRAR_RHIRD_1_234_0 : Unreasonable vina: -10.182</td><td>title: TRAR_RHIRD_1_234_0 : Reasonable vina: -13.112</td></tr></table>

Supporting moleculeCIDD output 

<table><tr><td><img src="images/92f8d71069e88f9744f222a77da2be1244b0256c299fa1f9ce7285ead23e2dc5.jpg"/></td><td><img src="images/94d9097f53fa26594d3045bdf7f8642a141ffe95a2f5bf1acf9f7fbfea4cbdc7.jpg"/></td></tr><tr><td>title: EXG1_CANAL_41_438_0 : Unreasonable vina: -10.072</td><td>title: EXG1_CANAL_41_438_0 : Reasonable vina: -10.17</td></tr><tr><td><img src="images/67e46eb18e944bb2ed25be862a79c6648018fb09983f4a5b8bcd87c8d0ada39b.jpg"/></td><td><img src="images/09ce400e1b2d62fac22dcffe6d452346f9f11e0401aff34abf30023a18135994.jpg"/></td></tr><tr><td>title: SQHC_ALIAD_1_631_0 : Unreasonable vina: -9.519</td><td>title: SQHC_ALIAD_1_631_0 : Reasonable vina: -12.291</td></tr><tr><td><img src="images/1f744fa297f628af5fda5e2c6e7554c730366433beb80444658276090869ba4f.jpg"/></td><td><img src="images/d8ea032cb0e3f4908b89214a3d33884bf3590edb903ca0931bcfc2f8339f1100.jpg"/></td></tr><tr><td>title: SIR3_HUMAN_117_398_0 : Unreasonable vina: -10.258</td><td>title: SIR3_HUMAN_117_398_0 : Reasonable vina: -10.419</td></tr><tr><td><img src="images/be6dbbf0b017a24266328daa77592381e1c4117ca563cdb63b948941213c9c28.jpg"/></td><td><img src="images/da443f1a199cab3b90eba2cf1be06f28a91407b25dfb7ff27d9eeffbd59669ed.jpg"/></td></tr><tr><td>title: NOS3_HUMAN_65_480_0 : Unreasonable vina: -9.821</td><td>title: NOS3_HUMAN_65_480_0 : Reasonable vina: -10.535</td></tr><tr><td><img src="images/ff3f41f888b15a87b6123f0c1aae6823d4b60dfe31b657e92bead32fd459da8f.jpg"/></td><td><img src="images/fb0862dde5c78e1998396b37ae536fd436bca36850c990194f11a0be7c4ab4aa.jpg"/></td></tr><tr><td>title: BACE2_HUMAN_76_460_0 : Unreasonable vina: -9.302</td><td>title: BACE2_HUMAN_76_460_0 : Reasonable vina: -9.947</td></tr><tr><td><img src="images/f88e2d829c7ad9c7b21bcd97412c439dd55ffd369028171e835664aba46a9550.jpg"/></td><td><img src="images/03587d930c7000e291f75e22d4bfd40945afff2cf99a899c563dde522d0c0f7f.jpg"/></td></tr><tr><td>title: SDIA_ECOLI_1_171_0 : Unreasonable vina: -8.889</td><td>title: SDIA_ECOLI_1_171_0 : Reasonable vina: -13.779</td></tr><tr><td><img src="images/098208d834f456e63791cbfd4bf1fc003218d6eefdc67caefdd87feac04389bf.jpg"/></td><td><img src="images/de74fe00df766b1cf1a6096057985899d92e9d5b2a2326dc581c6761eafa47c3.jpg"/></td></tr><tr><td>title: TRAR_RHIRD_1_234_0 : Unreasonable vina: -9.69</td><td>title: TRAR_RHIRD_1_234_0 : Reasonable vina: -15.856</td></tr></table>

Supporting moleculeCIDD output 

<table><tr><td>title: POL_FOAMV_861_1060_0
: Unreasonable
vina: -7.797</td><td>title: POL_FOAMV_861_1060_0
: Reasonable
vina: -8.475</td></tr></table>

Supporting moleculeCIDD output 

<table><tr><td>title: HDHA_ECOLI_1_255_0
: Unreasonable
vina: -8.698</td><td>title: HDHA_ECOLI_1_255_0
: Reasonable
vina: -9.535</td></tr></table>

# I Limitation on Computational Cost and Scalability

We acknowledge that our framework introduces additional computational steps due to the use of LLMbased modules. Below, we provide a detailed discussion of the computational overhead, empirical runtime, and justification for its practicality in the context of drug discovery.

Computational Overhead of LLM Pipelines. The runtime and token-related costs associated with repeated LLM invocations—such as scaffold analysis, molecule generation, self-reflection, and candidate selection—can introduce non-trivial computational overhead. However, several factors mitigate this concern:

LLM Inference Efficiency Is Rapidly Improving. Recent advances in model quantization, prompt batching, and optimized inference are dramatically reducing the cost of multi-step reasoning. For example, DeepSeek-V3/R1 achieves approximately 2.19M output tokens per dollar, reflecting a 60–70% cost reduction compared to GPT-4 in 2023. Frameworks such as vLLM [18], vTensor [36], and Splitwiser [1] further improve efficiency: vLLM enables up to 24× throughput; vTensor achieves 2× speedups with 70% less GPU memory; and Splitwiser reduces latency by 1.7× through prompt colocation. Hardware accelerators like TensorRT-LLM also support highly scalable domain-specific pipelines. These trends suggest that the cost of multi-step reasoning is unlikely to remain a long-term bottleneck.

Empirical Runtime of Our Pipeline. To provide a more quantitative view, we report the empirical runtime of our full pipeline. Based on our experiments with the MolCraft model (used as the SBIG module in our method), under the setting of 100 sampling steps, it takes approximately 300 seconds to generate 100 molecules. For competitive baselines, previous work reports that the autoregressive method Pocket2Mol requires around 2827 seconds to generate the same number of molecules, and diffusion-based methods such as TargetDiff and DecompDiff require approximately 3428 seconds and 6189 seconds, respectively.

As our method builds upon base SBDD models as the SBIG module, we only consider the additional time introduced by the LEDD module. With parallel LLM API requests, the total time required for generating 100 molecules is approximately 15 minutes in our experiments. Importantly, this added cost does not change the order of magnitude of the overall runtime.

The majority of this overhead stems from LLM inference latency, which is common across recent works that utilize LLMs. Nevertheless, this is unlikely to remain a bottleneck as inference efficiency continues to improve. For instance, recent advances in Diffusion-LLMs [31] have demonstrated inference speeds exceeding 2000 tokens per second, suggesting the potential for up to a 20× acceleration of our pipeline in the near future.

Molecule Design Is Not a Real-Time Task. Unlike latency-sensitive domains such as recommendation systems or autonomous control, molecule design prioritizes quality over speed. Drug discovery workflows are inherently iterative and require careful validation. While LLM-agent pipelines incur additional compute, their ability to generate higher-quality candidates with stronger binding plausibility aligns with the broader goal of improving experimental success rates, rather than immediate response times.

Relative Cost Compared to Wet-Lab Validation. In the broader context of drug development—which routinely spans several years and billions of dollars—LLM-related inference costs are marginal. The true bottlenecks lie in experimental synthesis, biochemical testing, and preclinical validation. Even modest improvements in in silico candidate quality can translate to significant downstream savings. Thus, the human-effort and resource reductions enabled by automated multi-step reasoning justify the modest computational overhead.

In summary, while our method introduces additional computational cost, it remains within a practical and acceptable range and does not diminish the significance, effectiveness, or applicability of our contributions. These tradeoffs will continue to improve as inference efficiency advances.

# J Results on more targets

we tested CIDD on additional targets: 1sa1, 1t8i and 7rpz, all known for their structural complexity and variability in ligand scaffolds. For 1sa1, Tubulin presents a challenging drug target because its binding sites are highly dynamic, involving extensive protein–protein interfaces; furthermore, the ligand in this complex, podophyllotoxin, is a complex natural product scaffold[28]. For 1t8i, Human DNA Topoisomerase I presents a challenging drug target because its catalytic mechanism involves a highly dynamic binding site that accommodates DNA; moreover, the ligand in this initial complex is camptothecin, a natural product scaffold rather than a traditionally rationally designed small molecule[32]. For 7rpz, KRASG12D is difficult to inhibit due to its high GDP/GTP affinity and absence of a nucleophilic residue near the switch II pocket, which hampers covalent strategies and limits prior chemotypes. The ligand uniquely overcomes these barriers with a pyrido[4,3-d]pyrimidine scaffold, fully engages the pocket, and achieves picomolar noncovalent inhibition with strong in vivo efficacy[35].

Table 5: Comparison between MolCRAFT and CIDD on different targets 

<table><tr><td>Target</td><td>Method</td><td>Success Ratio ↑</td><td>Vina Score ↓</td><td>QED ↑</td><td>SA ↑</td><td>MRR ↑</td></tr><tr><td>1sa1</td><td>MolCRAFT</td><td>27.78%</td><td>-9.78</td><td>0.56</td><td>0.66</td><td>35.56%</td></tr><tr><td>1sa1</td><td>CIDD</td><td>54.44%</td><td>-10.47</td><td>0.60</td><td>0.71</td><td>62.22%</td></tr><tr><td>1t8i</td><td>MolCRAFT</td><td>9.64%</td><td>-7.96</td><td>0.37</td><td>0.57</td><td>60.24%</td></tr><tr><td>1t8i</td><td>CIDD</td><td>27.71%</td><td>-8.38</td><td>0.39</td><td>0.62</td><td>68.67%</td></tr><tr><td>7rpz</td><td>MolCRAFT</td><td>1.35%</td><td>-9.71</td><td>0.27</td><td>0.57</td><td>1.35%</td></tr><tr><td>7rpz</td><td>CIDD</td><td>14.86%</td><td>-10.35</td><td>0.32</td><td>0.61</td><td>14.86%</td></tr></table>

# K Ablation Study: Reasoning Design vs. Simple Prompting

To investigate the source of our framework’s effectiveness, we conducted an ablation study comparing different prompting strategies. Specifically, we replaced our original chain-of-thought (CoT), domaininformed prompt with a simplified instruction: “Based on the pocket and interaction analysis, modify the original molecule.”

This experiment isolates the effect of prompt engineering by using the same underlying LLM and tools, but with varying reasoning structure.

Table 6: Ablation results comparing the impact of prompt complexity on model performance. 

<table><tr><td>Method</td><td>SA ↑</td><td>MRR ↑</td><td>Success ↑</td></tr><tr><td>MolCRAFT (baseline)</td><td>0.685</td><td>58.47%</td><td>13.72%</td></tr><tr><td>CIDD (simple prompt)</td><td>0.678</td><td>63.69%</td><td>19.76%</td></tr><tr><td>CIDD (CoT prompt, ours)</td><td>0.735</td><td>81.74%</td><td>34.59%</td></tr></table>

Despite using the same LLM and external tools, the simplified prompting strategy performs significantly worse than our CoT-guided approach, and only marginally better than the MolCRAFT baseline. This highlights that the primary gains of our method stem from structured, domain-informed reasoning embedded in the prompt design, rather than from tool integration alone.

# L Extension: Applicability to Hit-to-Lead Optimization

While the CIDD framework was not originally designed for hit-to-lead optimization, it can be readily adapted to such scenarios. To explore this possibility, we initialized the generation process—and the input to the LEDD module—using ground-truth ligands from the CrossDocked test set.

Despite these ligands already demonstrating strong synthetic accessibility and structural quality, CIDD was able to generate new molecules that exhibited further improvements in potency (as measured by docking score), synthesizability (QED and SA), and overall reasonability (MRR and success ratio).

Table 7: Evaluation of hit-to-lead potential by initializing CIDD with known binders from the CrossDocked test set. 

<table><tr><td>Method</td><td>Vina Score ↓</td><td>QED ↑</td><td>SA ↑</td><td>MRR ↑</td><td>Success Ratio ↑</td></tr><tr><td>Original Ligands</td><td>-7.53</td><td>0.473</td><td>0.738</td><td>0.8272</td><td>22.22%</td></tr><tr><td>CIDD (generated)</td><td>-8.22</td><td>0.528</td><td>0.752</td><td>0.9136</td><td>37.04%</td></tr></table>

These results demonstrate that, even when starting from already high-quality ligands, our framework is capable of discovering improved candidates through domain-aware multi-agent reasoning.

We note that fully supporting hit-to-lead tasks would require adapting the pipeline structure, modifying the chain-of-thought prompts, and refining the integration of design tools to better align with lead optimization objectives. Nonetheless, the observed performance underscores the broader applicability of our framework and the potential of structured LLM reasoning in more advanced drug development stages.

We plan to incorporate support for hit-to-lead optimization more formally in future work.

# M Effect of Re-Docking SBIG-Generated Molecules

To ensure molecular stability and structural correctness, our pipeline includes a re-docking step following initial molecule generation. The rationale behind this design choice is that conformations directly produced by generative models may suffer from issues such as atomic clashes or physically unstable geometries, which can negatively affect downstream interaction analysis and overall pipeline reliability. This concern has also been discussed in recent work [? ]. Re-docking provides a more stable and physically reasonable starting point for the LEDD module.

To evaluate whether this re-docking step is necessary, we conducted an ablation study comparing the performance of our pipeline with and without re-docking. Specifically, we initialized the LEDD module with either (1) re-docked poses or (2) the original generated conformations. All experiments used DeepSeek-V3 as the LLM.

Table 8: Ablation study evaluating the effect of re-docking versus directly using generated conformations. 

<table><tr><td>Method</td><td>Vina Score ↓</td><td>QED ↑</td><td>SA ↑</td><td>MRR ↑</td><td>Success Ratio ↑</td></tr><tr><td>Re-docking</td><td>-8.49</td><td>0.565</td><td>0.714</td><td>76.00%</td><td>29.66%</td></tr><tr><td>Original conformation</td><td>-8.403</td><td>0.575</td><td>0.721</td><td>76.09%</td><td>28.03%</td></tr></table>

As shown in the table, both variants achieve comparable results, with re-docking offering slight improvements in docking score and success ratio, while direct usage of the original conformation shows marginally better QED and SA. Overall, this suggests that our framework is robust to this design decision.

While re-docking provides additional geometric stability, the small performance gap indicates that either choice is acceptable in practice, depending on computational tradeoffs. This flexibility may be useful in settings where runtime is more constrained. .

# NeurIPS Paper Checklist

# 1. Claims

Question: Do the main claims made in the abstract and introduction accurately reflect the paper’s contributions and scope?

Answer: [Yes]

Justification: The main claims made in the abstract and introduction accurately reflect the paper’s contributions and scope.

Guidelines:

• The answer NA means that the abstract and introduction do not include the claims made in the paper.   
• The abstract and/or introduction should clearly state the claims made, including the contributions made in the paper and important assumptions and limitations. A No or NA answer to this question will not be perceived well by the reviewers.   
• The claims made should match theoretical and experimental results, and reflect how much the results can be expected to generalize to other settings.   
• It is fine to include aspirational goals as motivation as long as it is clear that these goals are not attained by the paper.

# 2. Limitations

Question: Does the paper discuss the limitations of the work performed by the authors?

Answer: [Yes]

Justification: Limitations are described in the appendix.

Guidelines:

• The answer NA means that the paper has no limitation while the answer No means that the paper has limitations, but those are not discussed in the paper.   
• The authors are encouraged to create a separate "Limitations" section in their paper.   
• The paper should point out any strong assumptions and how robust the results are to violations of these assumptions (e.g., independence assumptions, noiseless settings, model well-specification, asymptotic approximations only holding locally). The authors should reflect on how these assumptions might be violated in practice and what the implications would be.   
• The authors should reflect on the scope of the claims made, e.g., if the approach was only tested on a few datasets or with a few runs. In general, empirical results often depend on implicit assumptions, which should be articulated.   
• The authors should reflect on the factors that influence the performance of the approach. For example, a facial recognition algorithm may perform poorly when image resolution is low or images are taken in low lighting. Or a speech-to-text system might not be used reliably to provide closed captions for online lectures because it fails to handle technical jargon.   
• The authors should discuss the computational efficiency of the proposed algorithms and how they scale with dataset size.   
• If applicable, the authors should discuss possible limitations of their approach to address problems of privacy and fairness.   
• While the authors might fear that complete honesty about limitations might be used by reviewers as grounds for rejection, a worse outcome might be that reviewers discover limitations that aren’t acknowledged in the paper. The authors should use their best judgment and recognize that individual actions in favor of transparency play an important role in developing norms that preserve the integrity of the community. Reviewers will be specifically instructed to not penalize honesty concerning limitations.

# 3. Theory assumptions and proofs

Question: For each theoretical result, does the paper provide the full set of assumptions and a complete (and correct) proof?

Answer: [NA]

Justification: Our paper does not include theoretical results.

# Guidelines:

• The answer NA means that the paper does not include theoretical results.   
• All the theorems, formulas, and proofs in the paper should be numbered and crossreferenced.   
• All assumptions should be clearly stated or referenced in the statement of any theorems.   
• The proofs can either appear in the main paper or the supplemental material, but if they appear in the supplemental material, the authors are encouraged to provide a short proof sketch to provide intuition.   
• Inversely, any informal proof provided in the core of the paper should be complemented by formal proofs provided in appendix or supplemental material.   
• Theorems and Lemmas that the proof relies upon should be properly referenced.

# 4. Experimental result reproducibility

Question: Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions of the paper (regardless of whether the code and data are provided or not)?

Answer: [Yes]

Justification: We describe the information in the experiment setting section.

# Guidelines:

• The answer NA means that the paper does not include experiments.   
• If the paper includes experiments, a No answer to this question will not be perceived well by the reviewers: Making the paper reproducible is important, regardless of whether the code and data are provided or not.   
• If the contribution is a dataset and/or model, the authors should describe the steps taken to make their results reproducible or verifiable.   
• Depending on the contribution, reproducibility can be accomplished in various ways. For example, if the contribution is a novel architecture, describing the architecture fully might suffice, or if the contribution is a specific model and empirical evaluation, it may be necessary to either make it possible for others to replicate the model with the same dataset, or provide access to the model. In general. releasing code and data is often one good way to accomplish this, but reproducibility can also be provided via detailed instructions for how to replicate the results, access to a hosted model (e.g., in the case of a large language model), releasing of a model checkpoint, or other means that are appropriate to the research performed.   
• While NeurIPS does not require releasing code, the conference does require all submissions to provide some reasonable avenue for reproducibility, which may depend on the nature of the contribution. For example   
(a) If the contribution is primarily a new algorithm, the paper should make it clear how to reproduce that algorithm.   
(b) If the contribution is primarily a new model architecture, the paper should describe the architecture clearly and fully.   
(c) If the contribution is a new model (e.g., a large language model), then there should either be a way to access this model for reproducing the results or a way to reproduce the model (e.g., with an open-source dataset or instructions for how to construct the dataset).   
(d) We recognize that reproducibility may be tricky in some cases, in which case authors are welcome to describe the particular way they provide for reproducibility. In the case of closed-source models, it may be that access to the model is limited in some way (e.g., to registered users), but it should be possible for other researchers to have some path to reproducing or verifying the results.

# 5. Open access to data and code

Question: Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental material?

# Answer: [No]

Justification: Codes will be released once the paper is accepted.

# Guidelines:

• The answer NA means that paper does not include experiments requiring code.   
• Please see the NeurIPS code and data submission guidelines (https://nips.cc/ public/guides/CodeSubmissionPolicy) for more details.   
• While we encourage the release of code and data, we understand that this might not be possible, so “No” is an acceptable answer. Papers cannot be rejected simply for not including code, unless this is central to the contribution (e.g., for a new open-source benchmark).   
• The instructions should contain the exact command and environment needed to run to reproduce the results. See the NeurIPS code and data submission guidelines (https: //nips.cc/public/guides/CodeSubmissionPolicy) for more details.   
• The authors should provide instructions on data access and preparation, including how to access the raw data, preprocessed data, intermediate data, and generated data, etc.   
• The authors should provide scripts to reproduce all experimental results for the new proposed method and baselines. If only a subset of experiments are reproducible, they should state which ones are omitted from the script and why.   
• At submission time, to preserve anonymity, the authors should release anonymized versions (if applicable).   
• Providing as much information as possible in supplemental material (appended to the paper) is recommended, but including URLs to data and code is permitted.

# 6. Experimental setting/details

Question: Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the results?

# Answer: [Yes]

Justification: We describe the details in the experiment setting section.

# Guidelines:

• The answer NA means that the paper does not include experiments.   
• The experimental setting should be presented in the core of the paper to a level of detail that is necessary to appreciate the results and make sense of them.   
• The full details can be provided either with the code, in appendix, or as supplemental material.

# 7. Experiment statistical significance

Question: Does the paper report error bars suitably and correctly defined or other appropriate information about the statistical significance of the experiments?

# Answer: [No]

Justification: The baseline methods do not have error bars reported.

# Guidelines:

• The answer NA means that the paper does not include experiments.   
• The authors should answer "Yes" if the results are accompanied by error bars, confidence intervals, or statistical significance tests, at least for the experiments that support the main claims of the paper.   
• The factors of variability that the error bars are capturing should be clearly stated (for example, train/test split, initialization, random drawing of some parameter, or overall run with given experimental conditions).   
• The method for calculating the error bars should be explained (closed form formula, call to a library function, bootstrap, etc.)   
• The assumptions made should be given (e.g., Normally distributed errors).   
• It should be clear whether the error bar is the standard deviation or the standard error of the mean.

• It is OK to report 1-sigma error bars, but one should state it. The authors should preferably report a 2-sigma error bar than state that they have a 96% CI, if the hypothesis of Normality of errors is not verified.   
• For asymmetric distributions, the authors should be careful not to show in tables or figures symmetric error bars that would yield results that are out of range (e.g. negative error rates).   
• If error bars are reported in tables or plots, The authors should explain in the text how they were calculated and reference the corresponding figures or tables in the text.

# 8. Experiments compute resources

Question: For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?

Answer: [Yes]

Justification: We provide the information in supplementary material.

# Guidelines:

• The answer NA means that the paper does not include experiments.   
• The paper should indicate the type of compute workers CPU or GPU, internal cluster, or cloud provider, including relevant memory and storage.   
• The paper should provide the amount of compute required for each of the individual experimental runs as well as estimate the total compute.   
• The paper should disclose whether the full research project required more compute than the experiments reported in the paper (e.g., preliminary or failed experiments that didn’t make it into the paper).

# 9. Code of ethics

Question: Does the research conducted in the paper conform, in every respect, with the NeurIPS Code of Ethics https://neurips.cc/public/EthicsGuidelines?

Answer: [Yes]

Justification: The research conforms with the NeurIPS Code of Ethics.

# Guidelines:

• The answer NA means that the authors have not reviewed the NeurIPS Code of Ethics.   
• If the authors answer No, they should explain the special circumstances that require a deviation from the Code of Ethics.   
• The authors should make sure to preserve anonymity (e.g., if there is a special consideration due to laws or regulations in their jurisdiction).

# 10. Broader impacts

Question: Does the paper discuss both potential positive societal impacts and negative societal impacts of the work performed?

Answer: [NA]

Justification: The proposed research does not pose any foreseeable societal risks, including those related to misinformation, bias or fairness, data privacy, or security.

# Guidelines:

• The answer NA means that there is no societal impact of the work performed.   
• If the authors answer NA or No, they should explain why their work has no societal impact or why the paper does not address societal impact.   
• Examples of negative societal impacts include potential malicious or unintended uses (e.g., disinformation, generating fake profiles, surveillance), fairness considerations (e.g., deployment of technologies that could make decisions that unfairly impact specific groups), privacy considerations, and security considerations.

• The conference expects that many papers will be foundational research and not tied to particular applications, let alone deployments. However, if there is a direct path to any negative applications, the authors should point it out. For example, it is legitimate to point out that an improvement in the quality of generative models could be used to generate deepfakes for disinformation. On the other hand, it is not needed to point out that a generic algorithm for optimizing neural networks could enable people to train models that generate Deepfakes faster.   
• The authors should consider possible harms that could arise when the technology is being used as intended and functioning correctly, harms that could arise when the technology is being used as intended but gives incorrect results, and harms following from (intentional or unintentional) misuse of the technology.   
• If there are negative societal impacts, the authors could also discuss possible mitigation strategies (e.g., gated release of models, providing defenses in addition to attacks, mechanisms for monitoring misuse, mechanisms to monitor how a system learns from feedback over time, improving the efficiency and accessibility of ML).

# 11. Safeguards

Question: Does the paper describe safeguards that have been put in place for responsible release of data or models that have a high risk for misuse (e.g., pretrained language models, image generators, or scraped datasets)?

Answer: [NA]

Justification: Our paper poses no such risks.

Guidelines:

• The answer NA means that the paper poses no such risks.   
• Released models that have a high risk for misuse or dual-use should be released with necessary safeguards to allow for controlled use of the model, for example by requiring that users adhere to usage guidelines or restrictions to access the model or implementing safety filters.   
• Datasets that have been scraped from the Internet could pose safety risks. The authors should describe how they avoided releasing unsafe images.   
• We recognize that providing effective safeguards is challenging, and many papers do not require this, but we encourage authors to take this into account and make a best faith effort.

# 12. Licenses for existing assets

Question: Are the creators or original owners of assets (e.g., code, data, models), used in the paper, properly credited and are the license and terms of use explicitly mentioned and properly respected?

Answer: [Yes]

Justification: Our paper properly cite all relevant assets.

Guidelines:

• The answer NA means that the paper does not use existing assets.   
• The authors should cite the original paper that produced the code package or dataset.   
• The authors should state which version of the asset is used and, if possible, include a URL.   
• The name of the license (e.g., CC-BY 4.0) should be included for each asset.   
• For scraped data from a particular source (e.g., website), the copyright and terms of service of that source should be provided.   
• If assets are released, the license, copyright information, and terms of use in the package should be provided. For popular datasets, paperswithcode.com/datasets has curated licenses for some datasets. Their licensing guide can help determine the license of a dataset.   
• For existing datasets that are re-packaged, both the original license and the license of the derived asset (if it has changed) should be provided.

• If this information is not available online, the authors are encouraged to reach out to the asset’s creators.

# 13. New assets

Question: Are new assets introduced in the paper well documented and is the documentation provided alongside the assets?

Answer: [NA]

Justification: Our paper does not release new assets.

Guidelines:

• The answer NA means that the paper does not release new assets.   
• Researchers should communicate the details of the dataset/code/model as part of their submissions via structured templates. This includes details about training, license, limitations, etc.   
• The paper should discuss whether and how consent was obtained from people whose asset is used.   
• At submission time, remember to anonymize your assets (if applicable). You can either create an anonymized URL or include an anonymized zip file.

# 14. Crowdsourcing and research with human subjects

Question: For crowdsourcing experiments and research with human subjects, does the paper include the full text of instructions given to participants and screenshots, if applicable, as well as details about compensation (if any)?

Answer: [NA]

Justification: Our paper does not involve crowdsourcing nor research with human subjects.

Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.   
• Including this information in the supplemental material is fine, but if the main contribution of the paper involves human subjects, then as much detail as possible should be included in the main paper.   
• According to the NeurIPS Code of Ethics, workers involved in data collection, curation, or other labor should be paid at least the minimum wage in the country of the data collector.

# 15. Institutional review board (IRB) approvals or equivalent for research with human subjects

Question: Does the paper describe potential risks incurred by study participants, whether such risks were disclosed to the subjects, and whether Institutional Review Board (IRB) approvals (or an equivalent approval/review based on the requirements of your country or institution) were obtained?

Answer: [NA]

Justification: Our paper does not involve crowdsourcing nor research with human subjects.

Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.   
• Depending on the country in which research is conducted, IRB approval (or equivalent) may be required for any human subjects research. If you obtained IRB approval, you should clearly state this in the paper.   
• We recognize that the procedures for this may vary significantly between institutions and locations, and we expect authors to adhere to the NeurIPS Code of Ethics and the guidelines for their institution.   
• For initial submissions, do not include any information that would break anonymity (if applicable), such as the institution conducting the review.

# 16. Declaration of LLM usage

Question: Does the paper describe the usage of LLMs if it is an important, original, or non-standard component of the core methods in this research? Note that if the LLM is used only for writing, editing, or formatting purposes and does not impact the core methodology, scientific rigorousness, or originality of the research, declaration is not required.

Answer: [Yes]

Justification: Our paper describes the usage of LLMs to do drug design.

# Guidelines:

• The answer NA means that the core method development in this research does not involve LLMs as any important, original, or non-standard components.

• Please refer to our LLM policy (https://neurips.cc/Conferences/2025/LLM) for what should or should not be described.