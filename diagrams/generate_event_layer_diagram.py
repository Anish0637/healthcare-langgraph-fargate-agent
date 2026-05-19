"""
Generate: 06_event_layer_step_functions.png
Architecture diagram showing:
  - ECS Fargate agent emitting 7 audit events
  - EventBridge bus with routing rules
  - SQS queues (HITL FIFO, Audit Durable, Compliance, Safety Review)
  - AWS Step Functions HITL state machine
  - Downstream consumers (Lambda, CloudWatch, SNS, DynamoDB)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

# ── Colour palette ─────────────────────────────────────────────────────────
C = {
    "ecs":      "#FF9900",   # AWS orange
    "eb":       "#E7157B",   # EventBridge pink
    "sqs":      "#FF4F8B",   # SQS pink-red
    "sfn":      "#C7131F",   # Step Functions red
    "lambda":   "#FF9900",   # Lambda orange
    "cw":       "#FF4F8B",   # CloudWatch
    "ddb":      "#4AB197",   # DynamoDB teal
    "sns":      "#E7157B",   # SNS
    "bg_dark":  "#0D1117",   # background
    "bg_card":  "#161B22",   # card
    "bg_card2": "#1C2128",   # lighter card
    "border":   "#30363D",
    "text":     "#E6EDF3",
    "muted":    "#8B949E",
    "green":    "#3FB950",
    "red":      "#F85149",
    "yellow":   "#D29922",
    "blue":     "#58A6FF",
    "purple":   "#BC8CFF",
}

fig, ax = plt.subplots(figsize=(24, 18))
fig.patch.set_facecolor(C["bg_dark"])
ax.set_facecolor(C["bg_dark"])
ax.set_xlim(0, 24)
ax.set_ylim(0, 18)
ax.axis("off")

# ── Helper functions ────────────────────────────────────────────────────────

def box(ax, x, y, w, h, color, alpha=0.15, radius=0.25, lw=1.5, zorder=2):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw,
        edgecolor=color,
        facecolor=color,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(rect)
    return rect

def label(ax, x, y, text, size=9, color=C["text"], weight="normal",
          ha="center", va="center", zorder=5):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder,
            fontfamily="monospace" if "`" in text else "sans-serif")

def icon_label(ax, x, y, icon, text, isize=13, tsize=8,
               icolor=C["text"], tcolor=C["muted"]):
    ax.text(x, y + 0.18, icon, fontsize=isize, color=icolor,
            ha="center", va="center", zorder=5)
    ax.text(x, y - 0.22, text, fontsize=tsize, color=tcolor,
            ha="center", va="center", zorder=5)

def arrow(ax, x0, y0, x1, y1, color=C["muted"], lw=1.2,
          style="->", zorder=3, label_text=None, label_size=7):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle=style,
            color=color,
            lw=lw,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=zorder,
    )
    if label_text:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(mx + 0.1, my, label_text, fontsize=label_size,
                color=color, ha="left", va="center", zorder=6)

# ═══════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════
ax.text(12, 17.5, "Healthcare LangGraph Agent — Event Layer & Step Functions Architecture",
        fontsize=14, color=C["text"], fontweight="bold", ha="center", va="center")
ax.text(12, 17.1, "ECS Fargate  ·  EventBridge  ·  SQS  ·  AWS Step Functions  ·  Lambda  ·  DynamoDB  ·  CloudWatch",
        fontsize=9, color=C["muted"], ha="center", va="center")

# ═══════════════════════════════════════════════════════════════════════════
# COLUMN 1 — ECS FARGATE AGENT  (x: 0.3 – 5.2)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 0.3, 1.0, 4.9, 15.5, C["ecs"], alpha=0.08, lw=2)
label(ax, 2.75, 16.1, "ECS FARGATE  ·  healthcare-agents", size=9,
      color=C["ecs"], weight="bold")
label(ax, 2.75, 15.75, "FastAPI  ·  LangGraph  ·  Python 3.12", size=8, color=C["muted"])

# Agent box
box(ax, 0.6, 13.0, 4.2, 2.4, C["blue"], alpha=0.12, lw=1.5)
label(ax, 2.7, 14.75, "LangGraph Agent (graph.py)", size=9, color=C["blue"], weight="bold")
label(ax, 2.7, 14.35, "assistant node  →  Bedrock LLM", size=8, color=C["muted"])
label(ax, 2.7, 13.95, "RAG context injection (Bedrock KB)", size=8, color=C["muted"])
label(ax, 2.7, 13.55, "_invoke_with_fallback()  ·  FallbackModel", size=7.5, color=C["muted"])
label(ax, 2.7, 13.15, "metadata: selected_model · strategy · rag_used", size=7, color=C["muted"])

# 9-layer pipeline
box(ax, 0.6, 5.0, 4.2, 7.6, C["purple"], alpha=0.08, lw=1.2)
label(ax, 2.7, 12.3, "9-Layer Security Pipeline (main.py)", size=9,
      color=C["purple"], weight="bold")

layers = [
    ("1", "auth_denied",              C["red"],    "JWT Validation  →  auth.py"),
    ("2", "request_invalid",          C["yellow"], "Schema / Rate Limit  →  security.py"),
    ("3", "policy_denied",            C["red"],    "RBAC / ABAC / CBAC  →  security.py"),
    ("4", "guardrail_blocked",        C["red"],    "Prompt Injection Guard  →  governance.py"),
    ("5", "human_review_requested",   C["blue"],   "HITL Check  →  hitl.py"),
    ("6", "—",                        C["green"],  "PII/PHI Redact  →  pii.py"),
    ("7", "—",                        C["green"],  "LangGraph invoke  →  graph.py"),
    ("8", "invoke_success",           C["green"],  "Output Validation + Persist  →  memory.py"),
    ("9", "human_review_rejected",    C["yellow"], "HITL Reject Path  →  hitl.py"),
]

for i, (num, evt, clr, desc) in enumerate(layers):
    y = 11.6 - i * 0.72
    box(ax, 0.7, y - 0.28, 4.0, 0.62, clr, alpha=0.10, lw=1.0)
    label(ax, 1.05, y + 0.07, f"[{num}]", size=7.5, color=clr, weight="bold", ha="left")
    label(ax, 2.7, y + 0.07, desc, size=7.5, color=C["text"], ha="center")
    if evt != "—":
        label(ax, 2.7, y - 0.18, f"emit → {evt}", size=6.8, color=clr, ha="center")

# Audit logger
box(ax, 0.6, 1.2, 4.2, 1.5, C["cw"], alpha=0.12, lw=1.2)
label(ax, 2.7, 2.3, "audit.py  →  audit_event()", size=9, color=C["cw"], weight="bold")
label(ax, 2.7, 1.9, "PII auto-redact  →  logger.info(json.dumps(record))", size=7.5, color=C["muted"])
label(ax, 2.7, 1.55, "CloudWatch Logs: /ecs/healthcare-langgraph-agent", size=7.5, color=C["muted"])
label(ax, 2.7, 1.25, "Fields: event_type · trace_id · tenant_id · timestamp", size=7, color=C["muted"])

arrow(ax, 2.7, 4.95, 2.7, 2.75, color=C["cw"], lw=1.5,
      label_text="7 event types", label_size=7)

# ═══════════════════════════════════════════════════════════════════════════
# COLUMN 2 — EVENTBRIDGE  (x: 5.6 – 10.5)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 5.6, 1.0, 5.2, 15.5, C["eb"], alpha=0.07, lw=2)
label(ax, 8.2, 16.1, "Amazon EventBridge", size=9, color=C["eb"], weight="bold")
label(ax, 8.2, 15.75, "healthcare-agent-bus  ·  fan-out routing", size=8, color=C["muted"])

eb_bus_events = [
    ("auth_denied",            C["red"],    "source: healthcare.agent.security",   "WAF block + CloudWatch alarm + SNS alert"),
    ("policy_denied",          C["red"],    "source: healthcare.agent.governance",  "SIEM + Compliance Queue + Audit DB"),
    ("guardrail_blocked",      C["red"],    "source: healthcare.agent.safety",      "Safety metrics + model re-tune trigger"),
    ("human_review_requested", C["blue"],   "source: healthcare.agent.hitl",        "HITL Queue + SLA watchdog Lambda"),
    ("invoke_success",         C["green"],  "source: healthcare.agent.invoke",      "Usage analytics + billing ledger"),
    ("request_invalid",        C["yellow"], "source: healthcare.agent.validation",  "Rate-limit monitor + DDoS alert"),
    ("human_review_rejected",  C["yellow"], "source: healthcare.agent.hitl",        "Escalation Lambda + compliance log"),
]

for i, (evt, clr, src, targets) in enumerate(eb_bus_events):
    y = 14.8 - i * 1.85
    box(ax, 5.7, y - 0.7, 5.0, 1.55, clr, alpha=0.09, lw=1.0)
    label(ax, 8.2, y + 0.6,  evt,     size=8.5, color=clr, weight="bold")
    label(ax, 8.2, y + 0.25, src,     size=7,   color=C["muted"])
    label(ax, 8.2, y - 0.1,  "DetailType: " + evt, size=6.8, color=C["text"])
    label(ax, 8.2, y - 0.45, f"→ {targets}", size=6.8, color=C["muted"])

# Arrow from ECS to EventBridge
arrow(ax, 5.2, 8.25, 5.7, 8.25, color=C["eb"], lw=2.0,
      label_text="put_events()", label_size=8)

# ═══════════════════════════════════════════════════════════════════════════
# COLUMN 3 — SQS QUEUES  (x: 11.1 – 15.8)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 11.1, 1.0, 5.0, 15.5, C["sqs"], alpha=0.07, lw=2)
label(ax, 13.6, 16.1, "Amazon SQS  ·  Queues", size=9, color=C["sqs"], weight="bold")
label(ax, 13.6, 15.75, "guaranteed delivery  ·  DLQ  ·  backpressure", size=8, color=C["muted"])

sqs_queues = [
    ("HITL-Review-Queue.fifo",     C["blue"],   "FIFO · MessageGroupId=tenant_id",   "human_review_requested",  "Reviewer Lambda consumer\nDLQ → escalation after 3 retries"),
    ("Audit-Ingestion-Queue",      C["green"],  "Standard · long retention (7d)",    "invoke_success",           "HIPAA audit writer Lambda\nDLQ → manual reprocess"),
    ("Compliance-Queue",           C["red"],    "Standard · visibility=30s",         "policy_denied / auth_denied","Compliance processor Lambda\nDLQ → security team alert"),
    ("Safety-Review-Queue",        C["yellow"], "Standard · high priority",          "guardrail_blocked",        "Safety analyst Lambda\nDLQ → model review pipeline"),
]

for i, (qname, clr, props, trigger, consumer) in enumerate(sqs_queues):
    y = 14.0 - i * 3.3
    box(ax, 11.2, y - 1.7, 4.8, 3.1, clr, alpha=0.10, lw=1.2)
    label(ax, 13.6, y + 1.1,  qname,   size=8.5, color=clr, weight="bold")
    label(ax, 13.6, y + 0.7,  props,   size=7,   color=C["muted"])
    label(ax, 13.6, y + 0.3,  f"trigger: {trigger}", size=7, color=C["text"])
    # consumer lines
    for j, cline in enumerate(consumer.split("\n")):
        label(ax, 13.6, y - 0.1 - j * 0.4, cline, size=6.8, color=C["muted"])
    # DLQ badge
    box(ax, 13.1, y - 1.45, 1.0, 0.4, clr, alpha=0.25, lw=0.8)
    label(ax, 13.6, y - 1.25, "DLQ", size=7, color=clr, weight="bold")

# Arrow from EventBridge to SQS
arrow(ax, 10.8, 8.25, 11.1, 8.25, color=C["sqs"], lw=2.0,
      label_text="rule target", label_size=8)

# ═══════════════════════════════════════════════════════════════════════════
# COLUMN 4 — STEP FUNCTIONS  (x: 16.4 – 23.7)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 16.4, 1.0, 7.3, 15.5, C["sfn"], alpha=0.07, lw=2)
label(ax, 20.05, 16.1, "AWS Step Functions  ·  State Machines", size=9,
      color=C["sfn"], weight="bold")
label(ax, 20.05, 15.75, "Standard (HITL)  ·  Express (Ingestion)  ·  durable orchestration",
      size=8, color=C["muted"])

# ── State Machine 1: HITL ──────────────────────────────────────────────────
box(ax, 16.6, 7.8, 6.9, 7.7, C["blue"], alpha=0.10, lw=1.5)
label(ax, 20.05, 15.2, "SM-1: HITL Review Workflow  [Standard, up to 72h]",
      size=8.5, color=C["blue"], weight="bold")

hitl_states = [
    ("START",                  C["green"],  16.85, 14.5,  0.9, 0.45),
    ("ValidateRequest",        C["blue"],   16.85, 13.65, 1.7, 0.45),
    ("InvokeAgent",            C["blue"],   16.85, 12.8,  1.7, 0.45),
    ("GuardrailCheck",         C["yellow"], 16.85, 11.95, 1.7, 0.45),
    ("PolicyEnforce",          C["yellow"], 16.85, 11.1,  1.7, 0.45),
    ("NeedsHITL?",             C["purple"], 16.85, 10.25, 1.7, 0.45),
    ("SendToHITL\n(SQS+Token)",C["blue"],   16.85, 9.4,   1.7, 0.45),
    ("WaitForCallback\n[wait 72h]", C["sfn"],   16.85, 8.55,  1.7, 0.45),
    ("Decision?",              C["purple"], 19.15, 10.25, 1.5, 0.45),
    ("ReturnResponse",         C["green"],  19.15, 9.4,   1.7, 0.45),
    ("AuditAndEnd",            C["red"],    19.15, 8.55,  1.7, 0.45),
    ("END",                    C["green"],  19.15, 7.95,  0.9, 0.45),
]

for sname, clr, sx, sy, sw, sh in hitl_states:
    box(ax, sx, sy - sh/2, sw, sh, clr, alpha=0.20, lw=1.0)
    label(ax, sx + sw/2, sy, sname, size=7, color=clr, weight="bold")

# Arrows for HITL flow
flow = [
    (17.30, 14.50, 17.30, 13.87),
    (17.30, 13.43, 17.30, 13.02),
    (17.30, 12.57, 17.30, 11.77),  # GuardrailCheck skips PolicyEnforce label
    (17.30, 11.73, 17.30, 10.47),
    (17.30, 10.03, 17.30, 9.62),
    (17.30, 9.18,  17.30, 8.77),
    (18.55, 10.25, 19.15, 10.25),   # branch right → Decision
    (19.90, 10.03, 19.90, 9.62),    # approved
    (19.90, 9.18,  19.90, 8.77),    # rejected
    (19.90, 8.32,  19.90, 8.17),    # END
]
for x0, y0, x1, y1 in flow:
    arrow(ax, x0, y0, x1, y1, color=C["muted"], lw=0.9)

label(ax, 18.2, 10.32, "no HITL", size=6.5, color=C["green"])
label(ax, 19.5, 10.25, "→approved", size=6.5, color=C["green"])
label(ax, 19.5, 9.1,   "→rejected", size=6.5, color=C["red"])
label(ax, 18.0, 9.1,   "WaitForCallback\ntask token", size=6.5, color=C["sfn"])

# Retry annotation
box(ax, 21.0, 11.5, 2.8, 3.8, C["sfn"], alpha=0.08, lw=0.8)
label(ax, 22.4, 15.0,  "Retry / Catch Config",   size=7.5, color=C["sfn"], weight="bold")
label(ax, 22.4, 14.6,  "Retry:",                   size=7,   color=C["muted"])
label(ax, 22.4, 14.25, "maxAttempts: 3",            size=6.8, color=C["text"])
label(ax, 22.4, 13.9,  "backoffRate: 2.0",          size=6.8, color=C["text"])
label(ax, 22.4, 13.55, "intervalSeconds: 1",        size=6.8, color=C["text"])
label(ax, 22.4, 13.15, "Catch:",                    size=7,   color=C["muted"])
label(ax, 22.4, 12.8,  "ThrottlingException",       size=6.8, color=C["yellow"])
label(ax, 22.4, 12.45, "  → FallbackModel state",  size=6.5, color=C["text"])
label(ax, 22.4, 12.05, "States.ALL",                size=6.8, color=C["red"])
label(ax, 22.4, 11.7,  "  → AuditAndEnd (500)",    size=6.5, color=C["text"])

# ── State Machine 2: Ingestion Express ────────────────────────────────────
box(ax, 16.6, 1.2, 6.9, 6.3, C["green"], alpha=0.09, lw=1.5)
label(ax, 20.05, 7.2,  "SM-2: Document Ingestion Pipeline  [Express, <5min]",
      size=8.5, color=C["green"], weight="bold")

ingest_states = [
    ("S3 Upload (EventBridge trigger)", C["ecs"],    16.85, 6.7,  3.5, 0.4),
    ("ValidateDocument (Lambda)",       C["blue"],   16.85, 6.05, 3.5, 0.4),
    ("PIIDetect (Comprehend Medical)",  C["yellow"], 16.85, 5.4,  3.5, 0.4),
    ("PIIRedact (Lambda)",              C["yellow"], 16.85, 4.75, 3.5, 0.4),
    ("Map: EmbedAllChunks ⟵ parallel",  C["purple"], 16.85, 4.1,  3.5, 0.4),
    ("IndexChunks (OpenSearch)",        C["blue"],   16.85, 3.45, 3.5, 0.4),
    ("UpdateStatus (DynamoDB)",         C["ddb"],    16.85, 2.8,  3.5, 0.4),
    ("NotifyComplete (SNS)",            C["sqs"],    16.85, 2.15, 3.5, 0.4),
    ("END",                             C["green"],  17.85, 1.55, 0.9, 0.4),
]

iy_prev = None
for sname, clr, sx, sy, sw, sh in ingest_states:
    box(ax, sx, sy - sh/2, sw, sh, clr, alpha=0.18, lw=0.9)
    label(ax, sx + sw/2, sy, sname, size=7, color=clr)
    if iy_prev is not None:
        arrow(ax, sx + sw/2, iy_prev - 0.2, sx + sw/2, sy + sh/2, color=C["muted"], lw=0.8)
    iy_prev = sy

# Map state expansion note
box(ax, 21.0, 3.5, 2.8, 2.7, C["purple"], alpha=0.08, lw=0.8)
label(ax, 22.4, 6.0,  "Map State (parallel)",   size=7.5, color=C["purple"], weight="bold")
label(ax, 22.4, 5.65, "Per chunk:",             size=7,   color=C["muted"])
label(ax, 22.4, 5.3,  "  EmbedChunk",           size=6.8, color=C["text"])
label(ax, 22.4, 4.95, "  (Titan Embeddings)",   size=6.8, color=C["muted"])
label(ax, 22.4, 4.6,  "  IndexChunk",           size=6.8, color=C["text"])
label(ax, 22.4, 4.25, "  (OpenSearch AOSS)",    size=6.8, color=C["muted"])
label(ax, 22.4, 3.85, "maxConcurrency: 10",     size=6.8, color=C["yellow"])
label(ax, 22.4, 3.5,  "waits for ALL to finish",size=6.8, color=C["muted"])

# Arrow from SQS to Step Functions (HITL)
arrow(ax, 16.1, 11.05, 16.6, 11.05, color=C["sfn"], lw=2.0,
      label_text="triggers SM", label_size=7)

# ═══════════════════════════════════════════════════════════════════════════
# BOTTOM LEGEND
# ═══════════════════════════════════════════════════════════════════════════
legend_items = [
    (C["ecs"],    "ECS Fargate Agent"),
    (C["eb"],     "EventBridge (fan-out)"),
    (C["sqs"],    "SQS (point-to-point)"),
    (C["sfn"],    "Step Functions"),
    (C["green"],  "Success path"),
    (C["red"],    "Denial/block event"),
    (C["yellow"], "Warning/review event"),
    (C["blue"],   "HITL / async path"),
    (C["purple"], "Choice / Map state"),
]

lx = 1.0
for clr, lbl in legend_items:
    rect = mpatches.Patch(color=clr, alpha=0.55, label=lbl)
    ax.text(lx, 0.55, "■", color=clr, fontsize=12, ha="center", va="center")
    ax.text(lx + 0.2, 0.55, lbl, color=C["muted"], fontsize=7.5, ha="left", va="center")
    lx += 2.5

# ═══════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════
out_path = os.path.join(os.path.dirname(__file__), "06_event_layer_step_functions.png")
plt.tight_layout(pad=0.2)
plt.savefig(out_path, dpi=150, bbox_inches="tight",
            facecolor=C["bg_dark"], edgecolor="none")
plt.close()
print(f"Saved → {out_path}")
