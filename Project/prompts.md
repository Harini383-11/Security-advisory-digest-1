# Security Advisory Digest - LLM Prompts

This document contains the prompts used for AI-powered analysis of security advisories using Ollama and llama3.

## Prompts

### 1. Executive Summary Prompt

**Purpose**: Generate a concise, high-level summary of a security advisory for executive stakeholders.

**Template**:
```
You are a cybersecurity analyst. Provide a concise executive summary (2-3 sentences) of this security advisory:

Title: {title}
Severity: {severity}
Vendor: {vendor}
Product: {product}

Description:
{description}

Provide only the summary, no additional text.
```

**System Prompt**:
```
You are a cybersecurity expert. Provide clear, actionable security analysis.
```

**Output**: 2-3 sentence summary suitable for C-level executives

**Examples**:
- "A critical vulnerability in Apache HTTP Server CVE-2024-XXXXX allows remote attackers to execute arbitrary code through a specially crafted request. This vulnerability affects Apache 2.4.x versions before the security patch. Immediate patching is required for all affected systems."

### 2. Business Impact Prompt

**Purpose**: Analyze and communicate the business implications of a security vulnerability.

**Template**:
```
As a security consultant, analyze the business impact of this advisory:

Title: {title}
Severity: {severity}
Vendor: {vendor}
Product: {product}

Description:
{description}

Explain in 3-4 sentences:
1. What systems/services could be affected
2. Potential business consequences
3. Urgency level

Provide only the analysis, no additional text.
```

**System Prompt**:
```
You are a security business consultant. Focus on business impact and risk.
```

**Output**: 3-4 sentences explaining business impact, affected systems, and consequences

**Examples**:
- "This vulnerability could affect all web applications hosted on Apache servers, potentially leading to data breaches and service interruptions. Business consequences include loss of customer trust, regulatory penalties under GDPR/HIPAA, and operational downtime. Given the critical nature of web application infrastructure, this requires urgent remediation within 48-72 hours."

### 3. Remediation Advice Prompt

**Purpose**: Provide specific, actionable remediation steps for security teams.

**Template**:
```
As a security operations expert, provide remediation steps for this advisory:

Title: {title}
Vendor: {vendor}
Product: {product}

Description:
{description}

Provide 3-5 specific remediation steps:
1. Immediate actions
2. Short-term fixes
3. Long-term solutions

Provide only the steps, no additional text.
```

**System Prompt**:
```
You are a security operations expert. Provide specific, actionable remediation steps.
```

**Output**: 3-5 numbered remediation steps with timeframes

**Examples**:
- "1. IMMEDIATE: Apply security patches from Apache to all affected servers. 2. SHORT-TERM: Implement WAF rules to block malicious payloads targeting this vulnerability. 3. LONG-TERM: Establish a patch management policy with automated testing and deployment. 4. VERIFICATION: Conduct penetration testing to confirm vulnerability is resolved."

## Configuration

- **Model**: llama3
- **Base URL**: http://localhost:11434 (configurable)
- **Temperature**: 0.7 (balanced between deterministic and creative)
- **Top P**: 0.9 (nucleus sampling)
- **Max Tokens**: 1024

## Usage

These prompts are automatically used by the `LLMService` class in `llm/llm_service.py`:

```python
from llm.llm_service import LLMService
from models import AdvisoryDB

llm_service = LLMService()
advisory = AdvisoryDB(...)
summary = llm_service.generate_summary(advisory)

print(summary.executive_summary)
print(summary.business_impact)
print(summary.remediation_advice)
```

## Customization

To modify prompts, edit the methods in `llm/llm_service.py`:
- `_generate_executive_summary()`
- `_generate_business_impact()`
- `_generate_remediation_advice()`

## Performance Considerations

- Each prompt typically takes 10-30 seconds to generate on standard hardware
- Ollama must be running with the llama3 model pulled
- For bulk analysis, advisories are limited to the first 5 per scan
- Implement caching to avoid regenerating summaries for duplicate advisories
