# Doorman benchmark results

- Examples: 107 (72 injection, 35 benign)
- Precision: 97.3%
- Recall: 50.0%
- F1: 66.1%
- Accuracy: 65.4%
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
