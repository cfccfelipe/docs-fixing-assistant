---
tags: [tokens, embeddings, vectors]
---
---
created_date: 2026-04-02
title: 2026-04-02 - Daily
moc: daily/2026/04
status:
  - open
tags:
  - daily
---

## 1. Tokens: The "Currency" of Language

Tokens are the smallest unit of measurement for an LLM. Before a model "reads" a sentence, it chops it into these pieces.

- **The Concept:** Models don't see words; they see numbers representing pieces of words.
    
- **The Efficiency:** Breaking text into tokens allows the model to handle "run", "running", and "runner" as related items (sharing the "run" token) rather than three entirely unique concepts.
    
- **The Numbers:** In common models, **1,000 tokens** is roughly equal to **750 words**.
    

---

## 2. Embeddings and Vectors: The "Mental Map"

Once text is tokenized, it must be turned into something a computer can calculate: **Numbers.**

- **Vectors:** Every token is assigned a **Vector** (a long list of numbers, like `[0.12, -0.59, 0.88...]`). Think of this as a set of "coordinates" in a massive multi-dimensional map.
    
- **Embeddings:** These are the actual values within the vector that represent meaning.
    
    - **Semantic Proximity:** If two tokens have similar meanings (e.g., "Cat" and "Kitten"), their coordinates (vectors) will be very close to each other in this mathematical space.
        
    - **Relationship Mapping:** The model understands analogies (Puppy is to Dog as Kitten is to Cat) because the "distance" and "direction" between the puppy/dog vectors are nearly identical to the kitten/cat vectors.
        

---

## 3. Why This Matters (The 80% Result)

By mastering these two concepts, you understand how the model "thinks":

1. **Input:** Your text is broken into **Tokens**.
    
2. **Processing:** Those tokens are converted into **Vectors** (Embeddings).
    
3. **Calculation:** The model uses math (geometry) to predict which vector (token) should come next based on how close it is to the context of your prompt.
    
4. **Output:** The predicted vectors are turned back into human-readable tokens.
    

### Key Comparison Table

|**Concept**|**Simple Definition**|**Role in LLMs**|
|---|---|---|
|**Token**|A piece of a word or punctuation.|Standardizes input so the model can "count" and "read."|
|**Vector**|A list of numbers (coordinates).|Turns language into a format computers can do math with.|
|**Embedding**|The numerical representation of meaning.|Allows the model to find relationships between words without being told.|
## 1. The Success Metrics (The 20% that proves Value)

When deploying a model (like your LangSmith/Langfuse experiments), these three metrics usually generate 80% of the stakeholder interest:

- **Conversion Rate:** Does the AI actually make the user take action (a purchase, a sign-up, or a click)?
    
- **User Satisfaction:** Qualitative feedback (thumbs up/down) that assesses if the AI-generated content is actually helpful.
    
- **Efficiency:** Does the model scale? This measures computation time and resource utilization vs. the value produced.
    

---

## 2. Responsible AI: The "Guardrails"

Since you are working on a pipeline for LLM metrics (latency, quality), you are essentially building a **Veracity and Robustness** check. Here are the core pillars:

### The "Big Three" Risks

1. **Hallucinations:** Plausible-sounding but factually incorrect claims (e.g., fake citations).
    
2. **Toxicity:** Generating offensive or inappropriate content.
    
3. **Intellectual Property:** Ensuring the model doesn't verbatim reproduce its training data (code or text).
    

### The "Transparency" Split

Understanding the _internal_ vs. _external_ logic of your model:

- **Interpretability (Internal):** Can a human see the "weights" and math to understand _how_ the decision was made? (High transparency, often lower performance).
    
- **Explainability (External):** Can the model explain its behavior in "human terms"? (High performance, used for "Black Box" models).
    

---

## 3. AWS Tools for Your Pipeline (The "Expedia" Stack)

Since you are integrating this into a pipeline, these are the specific AWS services that provide the 80% of governance you need:

|**Service**|**Primary Function (The 80/20)**|
|---|---|
|**Amazon Bedrock Evaluation**|Quickly compares FMs using automatic (toxicity/accuracy) or human metrics.|
|**SageMaker AI Clarify**|Provides "Feature Importance" scores—explaining which part of the input caused the output.|
|**SageMaker Model Cards**|A "single source of truth" for documentation (intended use, risk ratings, training details).|
|**Amazon A2I**|Handles the "Human-in-the-loop" workflow for when the AI is unsure and needs a human review.|

---

## 4. Balancing Your Data (The "Curation" 20%)

To prevent bias (like your example of a model only knowing middle-aged people), the most effective 20% of work is:

1. **Inclusive Collection:** Ensuring diverse demographics in the initial dataset.
    
2. **Data Augmentation:** Creating synthetic "instances" for underrepresented groups to balance the scales.
    
3. **Regular Auditing:** Using tools like **SageMaker Data Wrangler** to check for feature drift or bias over time.
    

### Summary for your Team

As you move to LangSmith, your "Regression Test" stage is effectively a **Governance** tool. By capturing **Latency, Quality, and Toxicity**, you are covering the primary risks that the GenAI Platform team cares about.

Does this summary help you categorize the "Metrics" you mentioned in your Slack message?

### 📊 Especificaciones Estimadas (Arquitectura MoE)

A diferencia de los modelos densos antiguos, la familia Flash utiliza **Mixture of Experts (MoE)**. Esto significa que el modelo tiene un total de parámetros "en disco", pero solo activa una fracción para cada respuesta.

|**Atributo**|**Estimación Técnica (Consenso 2026)**|
|---|---|
|**Parámetros Totales**|**~8B a 10B** (8 mil millones)|
|**Parámetros Activos**|**~1B a 2B** por token|
|**Ventana de Contexto**|**1M de tokens**|
|**Latencia (TTFT)**|< 100ms (Extremadamente rápido)|

### 🔍 ¿Por qué es el modelo ideal para tu sistema de Obsidian?

Para tu proyecto de organizar notas, el número de parámetros es menos importante que la **eficiencia del razonamiento**. He aquí el 20/80 de por qué el Flash-Lite (de unos 8B) es mejor que un modelo de 70B para ti:

1. **Densidad de Información:** Aunque tenga "pocos" parámetros comparado con un modelo Pro, está entrenado con técnicas de **destilación de conocimiento** de Gemini 3 Ultra. Esto le permite entender conceptos complejos de Zettelkasten sin ocupar mucha memoria.
    
2. **Costo de Inferencia:** Al ser un modelo pequeño, Google puede ofrecerlo casi gratis o a precios de $0.10 por millón de tokens, porque procesarlo en sus TPUs les cuesta muy poco.
    
3. **Velocidad de Agentes:** En un sistema multiagente, la latencia se acumula. Si tienes 3 agentes y cada uno tarda 5 segundos, tu sistema es lento. Con el Flash-Lite (8B), las respuestas son casi instantáneas, lo que hace que la organización de tus carpetas de Obsidian se sienta fluida.