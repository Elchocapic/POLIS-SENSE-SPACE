# Intermediario de Luma (IA gratuita para el sitio público)

En el sitio público Luma no tiene a Claude, así que conversa a través de este intermediario:

    página (GitHub Pages)  →  Cloudflare Worker (guarda la clave)  →  Groq (modelo abierto, nivel gratuito)

La clave nunca va en la página. Si el intermediario no está configurado, falla o se agota la cuota, Luma
sigue funcionando en modo a bordo y lo avisa. Las emergencias no dependen de la IA.

## Puesta en marcha (unos 10 minutos, sin tarjeta)

1. **Clave de Groq.** Crear cuenta en https://console.groq.com → *API Keys* → *Create API Key*. Copiarla.
2. **Worker.** Crear cuenta en https://dash.cloudflare.com → *Workers & Pages* → *Create* → *Worker* →
   ponerle nombre `luma` → *Deploy*. Luego *Edit code*, borrar lo que hay, pegar el contenido de
   `worker.js` y *Deploy*.
3. **Secreto.** En el Worker: *Settings* → *Variables and Secrets* → *Add* → tipo *Secret*, nombre
   `GROQ_API_KEY`, valor: la clave del paso 1 → *Deploy*.
4. **Conectar la página.** Copiar la dirección del Worker (termina en `.workers.dev`) y pegarla en
   `prototipo/luma-config.js`:

       window.LUMA_API = 'https://luma.TU-CUENTA.workers.dev';

   Guardar el cambio en `main`. En uno o dos minutos el sitio muestra "Conversación con IA".

## Ajustes opcionales (variables de texto del Worker)

| Variable | Para qué | Por defecto |
|---|---|---|
| `MODELO` | Modelo de Groq a usar | `openai/gpt-oss-120b` |
| `ORIGENES` | Sitios que pueden usar el Worker, separados por coma | `https://elchocapic.github.io` y `localhost:8000` |

Si el sitio se publica en otra dirección, hay que añadirla a `ORIGENES` o el Worker responderá 403.

## Límites y cuidados

- El nivel gratuito de Groq tiene topes por minuto y por día; los valores de la cuenta se ven en
  https://console.groq.com/settings/limits. La página envía un contexto corto (unos 6 000 caracteres) para
  no agotarlos. Al llegar al tope, Luma avisa y vuelve a intentarlo al minuto.
- El Worker solo acepta peticiones del sitio del equipo, limita el tamaño de la conversación y la
  longitud de la respuesta. La comprobación de origen frena el uso casual, no a alguien decidido: si la
  clave se filtra o se abusa, se revoca en la consola de Groq y se crea otra.
- El modelo es abierto y menos preciso que Claude. Luma no diagnostica ni indica dosis.
