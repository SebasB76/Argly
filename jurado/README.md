# 🎯 Gemelos Digitales del Jurado — hackIAthon 2026

Preparación para el **Pitch Day (5 de junio de 2026)** · Proyecto **Argly** · Reto **Aseguradora del Sur**.

> **Formato del pitch:** 5 min de presentación + **5 min de Q&A** del jurado = 10 min totales.
> El Q&A es donde se gana o se pierde. Estos gemelos digitales sirven para **anticipar y ensayar** ese Q&A.

---

## 📁 Los gemelos
| # | Jurado | Cargo | Su lente | Archivo |
|---|---|---|---|---|
| 1 | **Johanna Barragán** | Consultora IA & Automatización · **Viamatica** (organizadora) | Ingeniería seria + integración | [`01-johanna-barragan.md`](01-johanna-barragan.md) |
| 2 | **Washington Arellano** | Founder/CEO Futuro Casa de Valores · ex-regulador | ROI en $ + riesgo + cumplimiento | [`02-washington-arellano.md`](02-washington-arellano.md) |
| 3 | **Iván Vera** | CEO Royaltic (BI/Big Data) · VP Clúster | Datos + KPIs + adopción | [`03-ivan-vera.md`](03-ivan-vera.md) |
| 4 | **Fernando Araujo** | Magíster IA · Director Sistemas SOLCA | Implementable + seguro + humano | [`04-fernando-araujo.md`](04-fernando-araujo.md) |

> ⚠️ **Quinto evaluador "fantasma": Aseguradora del Sur.** Las bases dicen que el panel incluye *"representantes del sponsor que plantea el reto"*. Es muy probable que haya alguien de la aseguradora preguntando lo **más específico del dominio** (¿cubre nuestros tipos de fraude?, ¿se integra con nuestro core?, ¿cuándo vemos ROI?). Prepárate para el dueño del reto, no solo para los 4 nombrados.

---

## 🧭 Mapa rápido: una frase y una pregunta por juez

| Juez | Dale esto (su gancho) | Te preguntará (lo más probable) |
|---|---|---|
| **Johanna** (ingeniera) | "90 tests, Docker, desplegado; el LLM no inventa cifras, hay fallback" | "¿Es desplegable de verdad o demo? ¿Y si el LLM se cae?" |
| **Washington** (finanzas/regulador) | "Ahorro en $ + **alerta ≠ acusación** + pasa auditoría" | "¿Cuánto ahorra en dólares? ¿Y un falso positivo?" |
| **Iván** (datos) | "5 motores suben AUC 0.83→0.92; degrada con gracia; KPIs claros" | "¿Calidad de datos que necesitas? ¿IA real o dashboard?" |
| **Fernando** (implementador salud) | "Se despliega en semanas, 100% sintético, humano decide" | "¿Cómo lo pongo en producción? ¿Seguridad de datos?" |

> **Regla de oro:** mira quién pregunta y **responde en su idioma**. La misma fortaleza de Argly se vende distinto a cada uno:
> - A **Washington**: el ahorro **en dólares** y el control del falso positivo.
> - A **Iván**: el **KPI** que mueve y la calidad de dato que exige.
> - A **Johanna**: la **arquitectura** (tests, fallback, versionado).
> - A **Fernando**: el **camino a producción** seguro y el humano al mando.

---

## 💛 Qué le ENCANTARÍA escuchar a cada uno (en una línea)
Cada gemelo trae la lista completa; el titular de cada uno:
- **Washington:** "el fraude lo pagan los asegurados honestos; Argly los defiende" + "score de riesgo auditable, como un buró pero para siniestros".
- **Iván:** "empezamos por el dato y el proceso, no por el modelo" + Pareto de proveedores + "el KPI es negocio, no el AUC".
- **Johanna:** "no corre en mi laptop: 90 tests, Docker, desplegado" + "agente real con tool-use, no un prompt".
- **Fernando:** "como en oncología: la IA detecta, el humano decide" + "desplegable en semanas y sostenible".

### 🌟 La gran idea que conquista al panel completo
> **Argly no es "otro detector de fraude con IA". Es un _score de riesgo explicable_ que protege al cliente honesto y respeta al analista humano.**

Esa sola frase toca a los cuatro a la vez: inclusión/justicia (Washington), explicabilidad sobre datos (Iván), ingeniería seria (Johanna), humano al mando (Fernando). Apóyala en un segundo gancho transversal: **demuestra que entiendes de SEGUROS, no solo de IA.** Usa el vocabulario del dominio (siniestro, ramo, prima, reserva, suscripción, ajustador, deducible) para que no suene a proyecto genérico de IA con "seguros" pegado encima. Eso es lo que separa al ganador del resto ante este panel.

### ❌ Qué NO decir (le chirría a este jurado)
- **"Detectamos el 100% del fraude."** → Washington (ex-regulador) y Fernando saben que es mentira; pierdes credibilidad al instante.
- **"Reemplaza al analista."** → Fernando lo castiga y contradice tu propio framing ("alerta, no acusa").
- **Presumir el AUC como meta final.** → para Iván el KPI es de negocio (dinero recuperado), no una métrica de modelo.
- **Vender el LLM como la estrella.** → Iván y Johanna lo leen como hype decorativo; la estrella son los datos y la ingeniería.
- **Ignorar el costo de llevarlo a producción.** → Fernando lo nota de inmediato; ten el plan de despliegue listo.

---

## 🎤 Guion del pitch (5 min) — qué tocar para cubrir a los 4
El deck actual (`presentation/argly-pitch.html`) ya está bien ordenado. Asegúrate de que en 5 min suene, en este orden, **un gancho para cada juez**:

1. **Problema** (10s) — "pocos siniestros son fraude; revisarlos todos a mano es imposible". → *todos*
2. **Qué hace** (30s) — score 0-100 + semáforo, **alerta no acusación**. → *Washington, Fernando*
3. **El motor** (60s) — 5 señales → un score; **AUC 0.83→0.92**. → *Iván, Johanna*
4. **Explicable y justo** (45s) — desglose + SHAP + contrafactual + **auditoría de sesgo** + 100% sintético. → *Washington, Fernando*
5. **Analista potenciado / agente** (45s) — pregunta en lenguaje natural, **no inventa cifras**, aprende del veredicto. → *Johanna, Iván*
6. **Resultados** (30s) — 0.92 / 0.97 / 90 tests. → *Iván, Johanna*
7. **Impacto** (40s) — **ahorro en $** + Pareto de proveedores + dataset variable. → *Washington, Iván*
8. **Cierre** (20s) — "prioriza, explica, humano al mando". → *todos*

> 💡 **Cierra el loop del sponsor:** di explícitamente "lo construimos para el reto de Aseguradora del Sur" y, si conoces los **14 patrones del reto**, menciona que están cubiertos. Eso le habla al evaluador fantasma y a Johanna (Viamatica).

---

## 🔥 Las 6 preguntas que casi seguro caen en el Q&A (ten la respuesta en la punta de la lengua)
1. **"¿Cuánto ahorra en dólares?"** → cifra de la pantalla de impacto + "escala con volumen, costo marginal ~0". *(Washington / Aseguradora)*
2. **"¿Y un falso positivo? ¿Acusan a un cliente honesto?"** → "alerta ≠ acusación, precisión 0.97, humano decide". *(Washington / Fernando)*
3. **"¿Métricas sobre datos sintéticos — sirven en producción?"** → "el método es real; importas el CSV real y recalcula; degrada a solo-reglas si faltan etiquetas". *(Iván / Johanna)*
4. **"¿El agente es agente o un prompt?"** → "planifica herramienta determinista + redacta con datos reales; fallback sin LLM". *(Johanna / Iván)*
5. **"¿Cómo lo despliego en una aseguradora real?"** → "Docker, API REST, ya en la nube; piloto en semanas". *(Fernando / Aseguradora)*
6. **"¿Seguridad y privacidad de datos?"** → "100% sintético en demo; en prod el dato no sale; bitácora auditable; LLM solo ve agregados". *(Fernando / Washington)*

---

## ⚠️ Puntos débiles de Argly y cómo blindarlos (anticípalos tú antes que ellos)
- **Datos sintéticos.** Es la crítica #1 (Iván sobre todo). Adelántate: *"sabemos que es sintético; por eso el dataset es variable — denos sus datos y lo verán recalculado en minutos"*. Convierte la debilidad en invitación.
- **Dependencia de LLMs externos (DeepSeek/Groq/Gemini).** Tu defensa ya existe: **fallback sin LLM** + "el LLM no decide ni inventa cifras". Dilo proactivamente.
- **"Push al core es mock".** No lo escondas: *"la integración está contratada por API; el push real es el siguiente paso del piloto"*. Honestidad > que te pillen.
- **Es un prototipo de hackathon.** Reencuádralo: *"prototipo, sí, pero con 90 tests, desplegado y reproducible — listo para piloto, no para la basura"*.
- **"25% de la rúbrica = explicabilidad"** (lo dice tu slide 6). ⚠️ **Verifica de dónde salió ese número** — la rúbrica pública del hackIAthon no trae porcentajes; si es de las bases del reto de Aseguradora del Sur, perfecto; si no, suaviza a "uno de los ejes" para no exponerte a un "¿de dónde sacaron ese 25%?".

---

## 🎭 Cómo ensayar con los gemelos (mock Q&A)
Cada archivo trae un **system prompt** para encarnar a ese juez. Dos formas de practicar:

1. **Pídemelo a mí aquí:** "haz de Washington y hazme un Q&A de Argly" → yo encarno al juez, te disparo preguntas y reacciono a tus respuestas. Puedo hacer **panel completo** (los 4 seguidos) o uno a uno.
2. **Copia el system prompt** de un archivo en otra sesión de IA y practica por tu cuenta.

> **Plan sugerido para hoy:** una ronda con cada juez (4 × 3 preguntas), luego un **simulacro cronometrado de 5 min de Q&A con el panel mezclado**. Si fallas una respuesta, vuelve al gemelo y ajústala.

---
*Fuentes completas en cada archivo. Investigación OSINT al 4-jun-2026; identidades de los 4 confirmadas con confianza alta.*
