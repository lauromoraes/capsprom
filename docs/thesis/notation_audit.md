# Thesis Notation Audit

Date: 2026-11-04. Status: approved and applied on 2026-11-04 (thesis, drafts, figures and `specs/academic_writing_spec.md`).

## Scope and method

All mathematical expressions were extracted from the thesis sources
(`chapters/`, `appendices/`, `dataset_processing_latex.tex`,
`data_acquisition_provenance.tex`), the drafts in `drafts/sections/`, and the
classifier-comparison draft with its TikZ figures: 798 expressions in total.
Each symbol was mapped to its meaning and location. The notation was then
compared with the references listed below, and with the content that the
specifications and roadmap still plan to add (capsule routing and losses,
attention fusion, training, calibration, statistics, explainability, homology
grouping).

Reference conventions checked against primary text:

| Source | Conventions confirmed |
| --- | --- |
| Goodfellow, Bengio and Courville, *Deep Learning*, notation page | scalars italic, vectors bold lowercase, matrices bold uppercase; sets blackboard ($\mathbb{A}$); example $\boldsymbol{x}^{(i)}$, target $y^{(i)}$; model $f(\boldsymbol{x};\boldsymbol{\theta})$; data distribution $p_{\text{data}}$; indicator $\mathbf{1}_{\text{condition}}$; sigmoid $\sigma(x)$; $\lVert\boldsymbol{x}\rVert$ for the $L^2$ norm |
| Sabour, Frosst and Hinton (2017), *Dynamic Routing Between Capsules* | primary output $\mathbf{u}_i$, weights $\mathbf{W}_{ij}$, prediction $\hat{\mathbf{u}}_{j\mid i}$, coupling $c_{ij}=\operatorname{softmax}(b_{ij})$, total input $\mathbf{s}_j$, output $\mathbf{v}_j=\operatorname{squash}(\mathbf{s}_j)$; routing procedure with $r$ iterations and layer $l$; margin loss $L_k$ with $T_k$, $m^{+}=0.9$, $m^{-}=0.1$, down-weighting $\lambda=0.5$; reconstruction loss scaled by $0.0005$ |
| Chen et al. (2013), iRSpot-PseDNC (text only; equations are images) | correlation factors $\theta_j$ of tier $j=1,\dots,\lambda$; highest tier $\lambda$; weight factor in $[0,1]$; correlation function $\Theta$ |
| Dietterich (1998); Alpaydin (1999); Nadeau and Bengio (2003); Bouckaert and Frank (2004) | as recorded in `drafts/comparacao_classificadores/referencias.bib` |

Conventions stated from the standard literature but not re-read here:
Vaswani et al. (2017) attention ($\mathbf{Q},\mathbf{K},\mathbf{V}$, $d_k$, $h$
heads); Guo et al. (2017) calibration ($M$ bins $B_m$); Demšar (2006)
($N$ data sets, $k$ classifiers, Wilcoxon $T$, Friedman $\chi^2_F$);
Lundberg and Lee (2017) Shapley values $\phi_i$; Efron's bootstrap ($B$
resamples). They should be confirmed before the corresponding text is written.

## Collisions found

| Symbol | Current or planned meanings | Locations |
| --- | --- | --- |
| $s$ | positive-class score $s(x)$; source study $s\in\mathcal{S}$, $\mathcal{D}_s$, $c_s$; seed in $\Delta_{d,s}$; planned capsule input $\mathbf{s}_j$ | Ch. 2, 6; Ch. 4; Ch. 7; planned Ch. 6 |
| $r$ | seed in the experiment tuple; property index $\rho_r$; window start $x_{i,r:r+h-1}$; exclusion radius; CV repetition; planned routing iterations | Ch. 7; Ch. 5; Ch. 5; draft `control_exclusion_radius`; comparison draft; planned Ch. 6 |
| $\theta$ | hyperparameters (Ch. 4 tuple); model parameters (Ch. 2, 7); PseKNC correlation factors $\theta_{i,d}^{(k)}$ | Ch. 4, 2, 7, 5 |
| $d$ | PseKNC lag; dataset index $\Delta_{d,s}$; embedding size $d_B$; CV differences $d_{rj}$; planned Hamming distance, attention $d_k$ | Ch. 5, 7, 5; comparison draft; planned |
| $k$ | k-mer length; dataset index in $\mathcal{D}_{s,k}$; planned margin-loss class $L_k$, $T_k$, attention $d_k$ and $\mathbf{K}$ | Ch. 5, 4; planned |
| $K$ | number of CV folds; planned attention keys | comparison draft; planned |
| $h$ | classifier; local window width | Ch. 2; Ch. 5 |
| $j$ | nucleotide position $x_{ij}$; feature family $\phi_j$, $z_{ij}$; CV fold $d_{rj}$; planned output capsule $j$ | Ch. 2, 5; comparison draft; planned |
| $J$ | number of feature blocks; number of CV estimates $J=RK$ | Ch. 5; comparison draft |
| $m$ | number of physicochemical properties; raw source size $m_s$; exclusion margin; planned $m^{\pm}$ | Ch. 5, 4; draft; planned |
| $\lambda$ | PseKNC highest tier; planned margin down-weighting $\lambda=0.5$ | Ch. 5; planned |
| $z$ | raw source sequence $z_i$; feature output $z_{ij}$ | Ch. 4; Ch. 5 |
| $c$ | cropping $c_s$; planned coupling coefficients $c_{ij}$ | Ch. 4; planned |
| $b$ | nucleotide in $N_b(x_i)$; planned routing logits $b_{ij}$ | Ch. 5; planned |
| $B$ | BERT embedding $B_i$; model $B$ in comparisons; planned bootstrap resamples; ECE bins $B_m$ | Ch. 5; Ch. 7; planned |
| $L$ | window length; planned margin loss $L_k$; Goodfellow per-example loss $L$ | Ch. 2; planned |
| $P$, $p$ | distribution $P$; $P_s(X,Y)$; positive counts $P_c$; physicochemical profile $P_i^{(k)}$; property labels $p_1,\dots$; $p$-values | Ch. 2, 4, appendix, Ch. 5, 8 |
| $N$ | nucleotide counts $N_b$; negative counts $N_c$; planned number of data sets (Demšar) | Ch. 5, appendix |
| $M$ | metric $M^{A}_{rj}$ and $\chi^2_5$ variable $M$ inside the same comparison draft; planned ECE bin count | comparison draft; planned |
| $\mu$ | estimand $\mu_{n_{\mathrm{tr}}}$; PseDNC property count in some sources | comparison draft; literature |
| $\phi$ | feature mapping $\phi_j$; planned Shapley values $\phi_i$ | Ch. 5; planned |
| $Q$ | PseKNC vector $Q_i^{(k,\lambda,w)}$; planned attention queries | Ch. 5; planned |
| $g$ | fusion branches $g_j$; BERT encoder $g_{\mathrm{BERT}}$; planned homology groups | Ch. 5; planned |
| $\sigma$ | biological sigma factor; sigmoid; standard deviation | draft `tss_class_selection`; planned; comparison draft |
| $F$ | k-mer frequency $F_i^{(k)}$; $F$ test; CV folds $F_{r,j}$ | Ch. 5; comparison draft |
| $(\mathcal{D},\phi,f,\theta,E)$ vs $(\mathcal{D},\Phi,f,\theta,E,r)$ | two experiment tuples with different members and meanings | Ch. 4 vs Ch. 7 |
| alphabet | $\{A,C,G,T\}^{81}$ still written out | `dataset_processing_latex.tex` lines 271, 308 |

## Principles for the resolution

1. Keep Goodfellow's conventions for learning objects ($f(\cdot;\boldsymbol{\theta})$,
   bold vectors and parameters, $p_{\text{data}}$, $\sigma(\cdot)$ for the sigmoid,
   $\mathbf{1}$ for the indicator), as `specs/academic_writing_spec.md` requires.
2. Keep the original authors' symbols for capsule routing (Sabour et al.)
   inside the capsule sections, because readers will compare them with the
   source. Model-internal equations describe one input, so the example index
   $i$ is dropped there and $i,j$ index capsules, as in the source; the
   section states this explicitly.
3. Where a global symbol and a literature symbol collide, rename the local or
   less established one, and record the source symbol in one sentence.
4. Use upright subscripts for labels ($d_{\mathrm{model}}$,
   $n_{\mathrm{boot}}$) and italic subscripts for indices.
5. One letter has one meaning at thesis scope. A letter may be reused only as a
   bound index inside a single displayed formula.

## Proposed resolution

### Problem formulation (Ch. 2)

| Current | Proposed | Reason |
| --- | --- | --- |
| $s(x)=f(\Phi(x);\theta)$ | drop $s$; $\hat y=h(x)=\mathbf{1}\bigl[f(\Phi(x);\boldsymbol{\theta})\ge t^{\star}\bigr]$, with $f$ returning the positive-class score | Goodfellow writes the output as $f(\boldsymbol{x};\boldsymbol{\theta})$; frees $s$ for sources and capsule inputs |
| $\theta$ | $\boldsymbol{\theta}$ (bold) | Goodfellow |
| $P$ | $p_{\text{data}}$; per source $p_{\text{data},s}$ (replaces $P_s(X,Y)$ in Ch. 4) | Goodfellow; removes the clash with counts and profiles |
| $x_i=(x_{i1},\dots,x_{iL})$ | $x_i=(x_{i1},\dots,x_{iL})$ with generic position $t$ ($x_{it}$) | $t$ is already the position index in $u_{it}^{(k)}$; frees $j$ |
| $\mathcal{X}_L$, $\mathcal{Y}$, $\mathcal{D}$, $h$, $t^{\star}$ | unchanged | caligraphic sets follow learning-theory usage; deviation from Goodfellow's blackboard sets is recorded in the spec |
| $x_i$ as subscript-indexed example | unchanged, not $x^{(i)}$ | superscript parentheses already mean k-mer length |

### Data (Ch. 4 and appendices)

| Current | Proposed |
| --- | --- |
| raw sequence $z_i$, $\mathcal{D}^0_s=\{(z_i,y_i)\}_{i=1}^{m_s}$ | $\tilde x_i$, $\mathcal{D}^0_s=\{(\tilde x_i,y_i)\}_{i=1}^{\tilde n_s}$ |
| cropping $c_s$ | $\operatorname{crop}_s$ |
| filter operator $q$ | predicate $\operatorname{keep}(x_i,y_i)$ |
| dataset index $k$ in $\mathcal{D}_{s,k}$, $\mathcal{P}_{s,k}$, $\mathcal{N}_{s,k}$, $\mathcal{C}_{s,k}$ | $d$, as in Ch. 7 ($\mathcal{D}_{s,d}$, …) |
| $\{A,C,G,T\}^{81}$ (lines 271, 308) | $\Sigma_{\mathrm{DNA}}^{81}$ |
| appendix counts $P_c,N_c,\dots$ | $n^{+}_{c},n^{-}_{c},\dots$ (positives and negatives per stage) |
| Ch. 4 tuple $(\mathcal{D},\phi,f,\theta,E)$ | remove, and refer to the Ch. 7 tuple |

### Features (Ch. 5)

| Current | Proposed |
| --- | --- |
| $\phi_j$, $z_{ij}$, $\Phi$, $J$ | unchanged; $\mathbf{z}_{ij}$ and $\Phi(x_i)$ bold when they are real vectors |
| nucleotide $b$ in $N_b(x_i)$ | $\nu\in\Sigma_{\mathrm{DNA}}$, $N_\nu(x_i)$ |
| window $x_{i,r:r+h-1}$ of width $h$ | $x_{i,t:t+\omega-1}$ of width $\omega$ |
| property count $m$, index $r$ in $\rho_r^{(k)}$ and $P_{i,t,r}^{(k)}$ | count $n_\rho$, index $q$ |
| TikZ labels $p_1,p_2,p_m$ | $\rho_1,\rho_2,\rho_{n_\rho}$ |
| PseKNC lag index $d$ | $\delta=1,\dots,\lambda$ |
| PseKNC correlations $\theta_{i,d}^{(k)}$ | $\gamma_{i,\delta}^{(k)}$, with a sentence that Chen et al. write $\theta_j$ |
| $\lambda$, $w$, $Q_i^{(k,\lambda,w)}$, $O_i^{(k)}$, $F_i^{(k)}$ | unchanged |
| BERT encoder $g_{\mathrm{BERT}}$, embedding $B_i\in\mathbb{R}^{d_B}$ | $\operatorname{enc}_{\mathrm{BERT}}$, $\mathbf{e}_i\in\mathbb{R}^{d_{\mathrm{emb}}}$ |
| fusion branches $g_j$ | $\psi_j$ (frees $g$ for homology groups) |

### Models (Ch. 6, current and planned)

| Object | Proposed notation |
| --- | --- |
| capsule routing | Sabour et al. symbols: $\mathbf{u}_i$, $\mathbf{W}_{ij}$, $\hat{\mathbf{u}}_{j\mid i}$, $b_{ij}$, $c_{ij}$, $\mathbf{s}_j$, $\mathbf{v}_j$, $\operatorname{squash}$, with the per-input convention of principle 2 |
| CapsProm score | $f(\Phi(x);\boldsymbol{\theta})=\lVert\mathbf{v}_1\rVert/(\lVert\mathbf{v}_0\rVert+\lVert\mathbf{v}_1\rVert)$ |
| routing iterations | $n_{\mathrm{iter}}$ (not $r$) |
| margin loss | $\mathcal{L}_{y'}=T_{y'}\max(0,m^{+}-\lVert\mathbf{v}_{y'}\rVert)^2+\beta(1-T_{y'})\max(0,\lVert\mathbf{v}_{y'}\rVert-m^{-})^2$, class $y'\in\mathcal{Y}$, $T_{y'}=\mathbf{1}[y=y']$; $\beta$ replaces Sabour's $\lambda$ (taken by PseKNC) |
| reconstruction weight | $\beta_{\mathrm{rec}}=0.0005$ |
| losses | calligraphic $\mathcal{L}$ for every loss and objective, never $L$ |
| attention fusion | bold $\mathbf{Q}_{\mathrm{att}},\mathbf{K}_{\mathrm{att}},\mathbf{V}_{\mathrm{att}}$, key size $d_{\mathrm{key}}$, heads $n_{\mathrm{heads}}$ |

### Training, protocol and statistics (Ch. 7, 8)

| Object | Proposed notation |
| --- | --- |
| experiment tuple | $(\mathcal{D},\Phi,f,\boldsymbol{\theta},\boldsymbol{\xi},E,r)$, with hyperparameter configuration $\boldsymbol{\xi}\in\Xi$ separated from learned parameters |
| seed | $r$ everywhere; $\Delta_{d,r}$, $\Delta_d=\operatorname{median}_r(\Delta_{d,r})$ |
| learning rate | $\epsilon$ (Goodfellow) |
| batch size, epochs | $n_{\mathrm{batch}}$, $n_{\mathrm{epoch}}$ |
| paired difference | $\Delta$ throughout (thesis and comparison draft) |
| models compared | $A$, $B$ (italic), never confused with upright nucleotides $\mathrm{A}$ |
| bootstrap and permutation counts | $n_{\mathrm{boot}}$, $n_{\mathrm{perm}}$ |
| significance, $p$-value | $\alpha$, $p$ |
| Wilcoxon and Friedman | $T$, $\chi^2_F$; number of datasets or clusters $n_{\mathcal{D}}$, number of models $n_{\mathrm{mod}}$ |
| confusion matrix, metrics | upright $\mathrm{TP},\mathrm{TN},\mathrm{FP},\mathrm{FN}$, $\operatorname{MCC}$, $\operatorname{AUC}$ |
| calibration | bins $\mathcal{B}_b$, $b=1,\dots,n_{\mathrm{bin}}$; $\operatorname{ECE}$, $\operatorname{Brier}$ |
| homology groups | $\mathcal{G}$, group $g$; Hamming distance $d_{\mathrm{H}}(x,x')$ |
| attributions | $\operatorname{IG}_{t}(x)$, $\operatorname{SHAP}_{a}(x)$ (not $\phi$) |

### Comparison draft and other drafts

| Current | Proposed |
| --- | --- |
| repetition index $r$ | $\ell=1,\dots,R$ |
| differences $d_{rj}$ | $\Delta_{\ell j}$ |
| folds $F_{r,j}$ | $\mathcal{F}_{\ell j}$ |
| $J=RK$ | write $RK$ |
| generic metric $M$ and Alpaydin's $N,M$ | metric $M$; Alpaydin's variables $C_1,C_2$ |
| estimand $\mu_{n_{\mathrm{tr}}}$ | unchanged (Nadeau and Bengio) |
| $P$, $P^{n_{\mathrm{tr}}}$ | $p_{\text{data}}$, $p_{\text{data}}^{n_{\mathrm{tr}}}$ |
| exclusion radius $r$, margin $m$, flanks $U,D$ | $L_{\mathrm{excl}}$, $L_{\mathrm{margin}}$, $L_{\mathrm{up}}$, $L_{\mathrm{down}}$ |
| biological $\sigma$ factor | keep as biological name ($\sigma^{70}$); the sigmoid always carries an argument, $\sigma(\cdot)$ |

## Implementation order

1. Approve or amend this proposal.
2. Record the approved symbols, their defining section, the renamed symbols and
   the deviations from Goodfellow in `specs/academic_writing_spec.md`.
3. Apply the renames chapter by chapter, regenerate TikZ figures, and compile
   the thesis and the drafts.
4. Re-run the expression extraction and confirm that every letter has one
   meaning at thesis scope.
