# Academic Paper: Dual-Process AI Agents (Preprint Source) 📄

This folder contains the complete academic research paper written in standard **IEEE / ACM two-column LaTeX format**, ready for submission to **arXiv (cs.AI / cs.SE)**, **TechRxiv**, or academic conferences.

---

## 📑 Paper Details

- **Title:** *Dual-Process AI Agents: A Declarative System 1 Decision DSL and Empirical Evaluation of Cross-Lingual Decision Models*
- **Author:** Anusorn Chaikaew
- **Target Category:** Computer Science - Artificial Intelligence (`cs.AI`), Software Engineering (`cs.SE`)
- **Key Artifact:** [github.com/anusornc/jev-decision-engine](https://github.com/anusornc/jev-decision-engine)

---

## 📂 File Structure

```text
paper/
├── main.tex         # Main LaTeX source document (IEEE twocolumn article style)
├── references.bib   # BibTeX bibliographic citations
└── README.md        # Compilation guide and paper overview
```

---

## 🛠️ How to Compile to PDF

### Method 1: Compile Online with Overleaf (Recommended)
1. Go to [Overleaf.com](https://www.overleaf.com).
2. Click **New Project** $\to$ **Upload Project**.
3. Upload the `paper/` folder (or zip `main.tex` and `references.bib`).
4. Overleaf will automatically compile the document to a two-column PDF.

### Method 2: Compile Locally using TeX Live / MacTeX
If you have MacTeX or TeX Live installed on your machine:
```bash
cd paper/

# Standard pdflatex + bibtex compilation sequence
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# View generated PDF
open main.pdf
```

---

## 🎯 Key Contributions Documented in the Paper

1. **Dual-Process Architecture for Autonomous Agents:** Theoretical and practical decoupling of heavy System 2 generation (LLMs) from sub-250ms System 1 decisions.
2. **Type-Safe Host-Language DSL:** Declarative compilation of multi-primitive questions (`choice`, `score`, `noul`) with `.gate()`, `.require()`, and deterministic `.mock()`.
3. **First Cross-Lingual Empirical Benchmark:** Real-world side-by-side evaluation between global commercial endpoints (*TypeSafe Jev 1.13*) and regional models (*iApp OpenThai-SystemOne*), proving that localized models are essential for regional consumer protection and fraud prevention.
