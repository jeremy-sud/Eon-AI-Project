# Fase 3: Integración Web (Javascript)

Esta fase lleva el motor Eón al navegador, permitiendo inteligencia artificial descentralizada y visualizaciones interactivas.

## Contenido

- **`aeon.js`**: Librería Core portada a ES6. Sin dependencias. ~10KB.
- **`demos/`**: Ejemplos de uso.
  - **`dream.html`**: "Eón Dream" - Visualización artística de estados neuronales.
  - _(Otros demos anteriores)_

## Uso de `aeon.js`

```javascript
const aeon = new Aeon({
  reservoirSize: 100,
  inputSize: 1,
  outputSize: 1,
});

// Entrenar
aeon.train(inputs, outputs);

// Predecir
const result = aeon.predict([0.5]);
```

## Eón Dream (Demo)

Una experiencia de "Generative Art" que visualiza el cerebro de la IA.

1.  Abrir `demos/dream.html` en un navegador.
2.  Escribir texto para "alimentar" pensamientos al reservoir.
3.  Observar cómo las activaciones neuronales crean patrones de color y movimiento.
