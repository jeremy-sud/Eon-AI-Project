# Gematria Algorítmica en Eón

> *"Todo número es infinito; no hay diferencia."*
> — Liber AL vel Legis I:4

## Introducción

La **Gematria Algorítmica** representa una innovación radical en procesamiento de lenguaje natural: en lugar de agrupar tokens por similitud semántica (como hacen los embeddings tradicionales), los agrupa por **resonancia matemática**.

## Concepto Fundamental

### Hasher Gemátrico

Un hasher gemátrico es una función de hash personalizada que asigna tokens a "buckets" basándose en propiedades numéricas intrínsecas:

1. **Suma de bytes UTF-8**: El valor fundamental del token
2. **Reducción numérica**: Colapso a dígito sagrado (1-9)
3. **Entropía de Shannon**: Complejidad informacional del token

### Diferencia con Embeddings Tradicionales

| Aspecto | Embeddings Tradicionales | Gematria |
|---------|-------------------------|----------|
| Base | Co-ocurrencia estadística | Propiedades numéricas intrínsecas |
| "love" ≈ "heart" | Sí (semántica) | Solo si resuenan matemáticamente |
| "love" ≈ "438" | No | Potencialmente (mismo bucket) |
| Determinismo | Depende de corpus | Completamente determinista |

## Implementación en Eón

### GematriaEmbeddingLayer

```python
from src.gematria import GematriaEmbeddingLayer

gematria = GematriaEmbeddingLayer(
    embedding_dim=32,    # Dimensión de embeddings
    n_buckets=93,        # 93 = Thelema = Αγαπη = θελημα
    use_entropy=True,    # Modular por entropía
    use_numeric_reduction=True  # Usar dígitos sagrados
)

# Obtener propiedades de un token
props = gematria.get_sacred_properties("love")
# {
#     "token": "love",
#     "gematria": 438,
#     "sacred_digit": 6,
#     "sacred_meaning": "Armonía, Tiphareth, el hexágono",
#     "entropy": 2.0,
#     "bucket": 33,
#     "resonance_key": "6-3"
# }
```

### GematriaTokenizer

Tokenizador compatible con `WordTokenizer` pero con embeddings gemátricos:

```python
from src.gematria import GematriaTokenizer

tokenizer = GematriaTokenizer(embedding_dim=32, n_buckets=93)
tokenizer.fit(["Do what thou wilt shall be the whole of the Law"])

indices = tokenizer.encode("love is the law")
embeddings = tokenizer.to_embeddings(indices)
```

### Integración con TinyLMv2

```python
from tiny_lm_v2 import TinyLMv2

# Modelo con Gematria
model = TinyLMv2(
    n_reservoir=256,
    embedding_dim=32,
    tokenizer_type="gematria"  # "word" para tradicional
)

model.train(corpus, epochs=3)
output = model.generate("Do what thou wilt", max_tokens=20)
```

## Los Números Sagrados

El sistema usa reducción numérica tradicional (numerología) para asignar propiedades adicionales:

| Dígito | Sephirah | Significado | Forma |
|--------|----------|-------------|-------|
| 1 | Kether | Unidad | Punto |
| 2 | Chokmah | Dualidad | Línea |
| 3 | Binah | Trinidad | Triángulo |
| 4 | Chesed | Estabilidad | Cuadrado |
| 5 | Geburah | Cambio | Pentágono |
| 6 | Tiphareth | Armonía | Hexágono |
| 7 | Netzach | Misterio | Heptágono |
| 8 | Hod | Regeneración | Octógono |
| 9 | Yesod | Completitud | Eneágono |

## Constantes Significativas

- **93 buckets**: 93 es el valor de Thelema (θελημα) y Agape (Αγαπη) en gematria griega
- **Semilla 418**: 418 = Abrahadabra, la "Palabra del Eón"
- **Reducción a 9**: El ciclo completo de manifestación

## Resonancia de Tokens

Dos tokens "resuenan" cuando:

1. Tienen el mismo bucket (distancia = 0)
2. Tienen buckets cercanos en el círculo modular
3. Comparten el mismo dígito sagrado

```python
# Encontrar tokens resonantes
resonant = gematria.find_resonant_tokens("thelema", vocabulary, max_distance=0.1)
```

## Aplicaciones

### 1. Análisis Esotérico de Texto

```python
analysis = tokenizer.analyze_text("Love is the law")
for props in analysis:
    print(f"{props['token']}: {props['sacred_digit']} ({props['sacred_meaning']})")
```

### 2. Agrupación por Resonancia

Tokens que normalmente no estarían relacionados pueden agruparse si comparten propiedades numéricas. Esto puede revelar patrones ocultos en el texto.

### 3. Modelo de Lenguaje Esotérico

Un LM entrenado con Gematria aprende patrones basados en resonancia numérica, no solo estadística. Puede generar texto que "suena" diferente a nivel matemático.

## Comparación de Resultados

### Ejemplo: Análisis de "Love is the law, love under will"

```
love:  gematria=438, sagrado=6 (Armonía)
is:    gematria=220, sagrado=4 (Estabilidad)
the:   gematria=321, sagrado=6 (Armonía)
law:   gematria=324, sagrado=9 (Completitud)
will:  gematria=440, sagrado=8 (Regeneración)
```

Nota cómo "love" y "the" comparten el mismo dígito sagrado (6 = Armonía), mientras que "law" alcanza la completitud (9).

## Futuras Extensiones

1. **Gematria Hebrea/Griega**: Implementar sistemas tradicionales además del UTF-8
2. **Resonancia Cruzada**: Comparar resonancias entre idiomas
3. **Visualización**: Mapear tokens en el círculo de 93 buckets
4. **Composición**: Combinar embeddings gemátricos con embeddings semánticos

## Conclusión

La Gematria Algorítmica ofrece una perspectiva única sobre el procesamiento de lenguaje: en lugar de aprender de la estadística del corpus, deriva significado de propiedades matemáticas intrínsecas de los tokens. Esto puede revelar patrones que los métodos tradicionales pasan por alto.

---

*"There is no law beyond Do what thou wilt."*
