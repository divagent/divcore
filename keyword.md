Core ReAct loop keywords (must-know)

These four are the big ones:

Thought
Internal reasoning / planning step
(sometimes implicit or hidden)

Action
Selecting a tool or operation to execute

Observation
Result returned from the environment or tool

Final Answer
Agent decides it’s done and returns output

👉 Canonical sequence:

Thought → Action → Observation → Thought → … → Final Answer

Common synonyms interviewers also use

You should recognize these as the same concepts:

Thought

Reasoning

Planning

Deliberation

Decision step

Next-action selection

Action

Tool call

Function call

Environment interaction

Act step

Observation

Tool result

Environment feedback

Execution result

World state update

Final

Termination

Finish condition

Agent stop

Answer synthesis

Agent loop / architecture keywords

Drop these if they ask about “design”:

Agent loop

Turn-based reasoning

Bounded iterations (max turns)

Stateful messages

Prompt template + evolving context

Deterministic control flow

Tool routing

Schema validation / structured output

Prompt & state management keywords

Very interview-safe:

Fixed prompt, evolving state

Message history as memory

System prompt invariance

Context accumulation

Observation injection

Conversation as world model

Tooling / safety / robustness keywords

These make you sound senior:

Tool whitelist

Tool grounding

Invalid tool rejection

Retry / fallback logic

Error-aware observations

Hallucination containment

Guardrails

Advanced / bonus keywords (use sparingly)

If the interviewer is strong:

Phase-based prompting

Planner–executor pattern

Reflection / self-critique

Memory summarization

Hidden chain-of-thought

ReAct vs Toolformer

Agentic orchestration

One clean interview sentence you can memorize

“This follows a ReAct-style agent loop: the model reasons over the current state, selects an action, observes the tool output, updates its context, and iterates until a termination condition is met — using a fixed prompt and evolving message history.”

If you want, tell me:

backend / infra interview or ML research?

FAANG / startup / open-source?

At that point the agent just continues the Thought → Action → Observation loop, updating state until it hits the termination condition.
Keyword-only expansions that sound intentional

You can slightly reshuffle the same words and it still lands:

“It’s a standard ReAct loop with bounded turns.”

“We keep a fixed prompt and evolving message state.”

“Tool calls are followed by observations injected back into context.”

“Once the model emits a final answer, the loop terminates.”

You’re not adding content — you’re showing correct framing.

The interviewer signal you’re actually sending

Repeating the keywords (calmly) signals:

✅ you recognize the pattern

✅ you’re not overfitting to one implementation

✅ you understand this as an architecture, not a trick

✅ you won’t build a prompt spaghetti monster

Most interviewers are listening for recognition, not novelty.

Nothing special happens there — it’s just another ReAct iteration with updated observations until the finish condition is met.