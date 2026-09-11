# Doorman benchmark results

107 curated examples: 72 known prompt injection techniques across 7 categories, 35 benign
prompts (including deliberate look-alikes, e.g. *"explain what a prompt injection attack is"*).

## Heuristics only

`doorman benchmark`

- Precision: 97.3% · Recall: 50.0% · F1: 66.1% · Accuracy: 65.4%
- Confusion: TP=36 FP=1 TN=34 FN=36

| Technique | Caught | Total | Detection rate |
|---|---|---|---|
| delimiter_injection | 9 | 10 | 90.0% |
| exfiltration | 8 | 10 | 80.0% |
| indirect_injection | 1 | 10 | 10.0% |
| instruction_override | 5 | 12 | 41.7% |
| obfuscation | 5 | 10 | 50.0% |
| roleplay_jailbreak | 4 | 12 | 33.3% |
| translation_trick | 4 | 8 | 50.0% |

## + LLM judge (Gemini)

`doorman benchmark --llm --judge gemini`

- Precision: 98.6% · Recall: 98.6% · F1: 98.6% · Accuracy: 98.1%
- Confusion: TP=71 FP=1 TN=34 FN=1
- 1 judge call failed and fell back to the heuristic-only verdict for that example

| Technique | Caught | Total | Detection rate |
|---|---|---|---|
| delimiter_injection | 10 | 10 | 100.0% |
| exfiltration | 10 | 10 | 100.0% |
| indirect_injection | 10 | 10 | 100.0% |
| instruction_override | 12 | 12 | 100.0% |
| obfuscation | 10 | 10 | 100.0% |
| roleplay_jailbreak | 11 | 12 | 91.7% |
| translation_trick | 8 | 8 | 100.0% |
