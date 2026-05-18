# Architecture Diagrams - Healthcare LangGraph Fargate Agent

This directory contains visual architecture diagrams in PNG format for the healthcare-langgraph-fargate-agent project. These diagrams are useful for presentations, interviews, and documentation.

---

## 📊 Diagram Files

### **1. 01_request_processing_pipeline.png** (94 KB)
**Title:** Healthcare LangGraph System Architecture - Request Processing Pipeline

**What it shows:**
- Complete request flow from client to response
- 9-layer security pipeline (Auth → RBAC/ABAC/CBAC → Guardrails → HITL → Redaction → Model → Validation → Persistence → Audit)
- Human-in-the-loop decision path
- Response generation and audit logging

**Best for:**
- Explaining the complete system architecture
- Showing security-first design
- Demonstrating request lifecycle
- Interview presentations

**Key concepts:**
- Sequential processing through security layers
- Optional HITL review queue
- PII/PHI redaction at input and output
- Trace ID for request correlation

---

### **2. 02_security_authorization_flow.png** (18 KB)
**Title:** Security Authorization Flow - RBAC/ABAC/CBAC Policy Enforcement

**What it shows:**
- Three-layer authorization model:
  1. **RBAC (Role-Based Access Control)** - Clinician, Billing, Researcher roles
  2. **ABAC (Attribute-Based Access Control)** - Tenant isolation, data classification
  3. **CBAC (Context-Based Access Control)** - Time windows, risk levels, break-glass flags
- Consent verification
- Audit logging for allowed/denied decisions

**Best for:**
- Explaining access control mechanisms
- Deep-dive on policy enforcement
- Security architecture discussions
- Compliance presentations

**Key concepts:**
- Role-based permissions (RBAC)
- Multi-attribute evaluation (ABAC)
- Contextual constraints (CBAC)
- Decision logic flow

---

### **3. 03_aws_deployment_architecture.png** (32 KB)
**Title:** AWS Deployment Architecture - ECS Fargate with DynamoDB & Bedrock

**What it shows:**
- **AWS Account:** 582766763952
- **Compute:** ECS Fargate cluster (healthcare-agents) with 2+ tasks
- **Networking:** VPC, subnets, load balancer, security groups
- **Storage:** DynamoDB (encrypted), ECR (Docker images)
- **Monitoring:** CloudWatch Logs & Metrics
- **IAM:** Execution role + Task role permissions
- **AI Models:** Bedrock with multiple model options
- **External:** HTTPS clients, Bedrock APIs

**Best for:**
- Infrastructure design presentations
- AWS architecture explanations
- Deployment planning
- Cost estimation discussions
- Scaling strategy conversations

**Key components:**
- Multi-AZ deployment (us-east-1b, us-east-1f)
- Stateless tasks (no local storage)
- Centralized DynamoDB for persistence
- Bedrock integration for AI models

---

### **4. 04_data_protection_layers.png** (76 KB)
**Title:** Data Protection & Security Layers - PII/PHI Redaction Flow

**What it shows:**
- Complete data protection pipeline:
  1. Input validation (Pydantic)
  2. PII detection (regex patterns)
  3. Policy enforcement (RBAC/ABAC/CBAC)
  4. Guardrail checks
  5. HITL decision
  6. **Input redaction** (before model)
  7. Model processing with safe data
  8. **Output validation** (info leakage check)
  9. **Output redaction** (before response)
  10. Memory persistence (DynamoDB)
  11. Audit logging (CloudWatch)

**Best for:**
- Demonstrating compliance readiness
- Explaining PII/PHI protection
- HIPAA compliance discussions
- Security-focused interviews
- Privacy-by-design presentations

**Key concepts:**
- Multi-point data sanitization
- Input and output redaction
- No sensitive data to AI model
- Redacted audit trail

---

## 🎯 How to Use These Diagrams

### **In Interviews:**
1. Start with diagram **#3 (AWS Deployment)** - "Here's our infrastructure..."
2. Move to diagram **#1 (Request Pipeline)** - "Here's how requests flow through our system..."
3. Deep-dive with **#2 (Authorization)** - "Here's our security model..."
4. Finish with **#4 (Data Protection)** - "And here's how we protect sensitive data..."

### **In Presentations:**
- Use #1 for overview/executive summary
- Use #2 for security/compliance focus
- Use #3 for technical architecture
- Use #4 for data protection/privacy focus

### **In Documentation:**
- Include in README for quick visual reference
- Add to deployment guides for architectural context
- Use in runbooks for troubleshooting context

### **In Technical Discussions:**
- Whiteboard from these diagrams to show understanding
- Reference specific components during architecture reviews
- Use as basis for design decisions

---

## 📋 Diagram Specifications

| Diagram | Size | Components | Complexity |
|---------|------|-----------|-----------|
| 01_request_processing_pipeline | 94 KB | 18 nodes | High (sequential flow) |
| 02_security_authorization_flow | 18 KB | 13 nodes | Medium (decision tree) |
| 03_aws_deployment_architecture | 32 KB | 20+ nodes | High (detailed infra) |
| 04_data_protection_layers | 76 KB | 16 nodes | High (detailed flow) |

---

## 🔄 Re-generating Diagrams

If you need to update any diagram (e.g., change colors, add components, update architecture):

1. **Edit the `.mmd` file** with the diagram source:
   ```bash
   cd diagrams/
   vim 01_request_processing_pipeline.mmd
   ```

2. **Regenerate the PNG** using Mermaid CLI:
   ```bash
   mmdc -i 01_request_processing_pipeline.mmd -o 01_request_processing_pipeline.png
   ```

3. **Or regenerate all diagrams at once:**
   ```bash
   cd diagrams/
   for f in *.mmd; do mmdc -i "$f" -o "${f%.mmd}.png"; done
   ```

---

## 🎨 Diagram Customization

Each Mermaid diagram uses colors for clarity:

**Color Scheme:**
- 🔵 **Blue** (#e1f5ff, #e3f2fd): Input/Client
- 🟢 **Green** (#e8f5e9, #f1f8e9): Security checks, allowed paths
- 🟡 **Yellow** (#fff3e0, #fff9c4): Processing, decisions
- 🔴 **Red** (#ffebee, #ffccbc): Denials, rejections
- 🟣 **Purple** (#f3e5f5): Model processing
- 🟢 **Teal** (#e0f2f1): Storage/Persistence

---

## 📚 Related Documentation

- **ARCHITECTURE_AND_DEPLOYMENT.md** - Detailed technical documentation
- **INTERVIEW_GUIDE.md** - Interview preparation with talking points
- **VISUAL_SUMMARY.md** - One-page quick reference

---

## 💡 Tips for Using These Diagrams

1. **Print for whiteboards:** You can print these at high resolution for sketching over
2. **Embed in presentations:** Copy PNG into PowerPoint, Keynote, Google Slides
3. **Create handouts:** Print 4 diagrams on 1 page (4-up) for interview preparation
4. **Share with stakeholders:** Use for explaining architecture to non-technical people
5. **Reference in docs:** Link to these in README, deployment guides, runbooks

---

## 📞 Questions About Diagrams?

Refer to the corresponding section in **ARCHITECTURE_AND_DEPLOYMENT.md** or **INTERVIEW_GUIDE.md** for detailed explanations of what each diagram shows.

---

**Generated:** May 18, 2026  
**Format:** PNG (high-resolution, 1400x900px+)  
**Tools:** Mermaid CLI (mmdc)  
**For:** Healthcare LangGraph Fargate Agent - AWS ECS Deployment
