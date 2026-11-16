// Intermediario de Luma para Cloudflare Workers (plan gratuito).
// La página pública le envía la conversación; el Worker añade la clave secreta y consulta a Groq.
// La clave nunca está en la página: se guarda como secreto GROQ_API_KEY en Cloudflare.
//
// Variables (Settings → Variables and Secrets):
//   GROQ_API_KEY  (secreto, obligatorio)  clave creada en console.groq.com
//   MODELO        (texto, opcional)       por defecto openai/gpt-oss-120b
//   ORIGENES      (texto, opcional)       sitios que pueden usarlo, separados por coma

const ORIGENES_DEFECTO = 'https://elchocapic.github.io,http://localhost:8000,http://127.0.0.1:8000';
const MODELO_DEFECTO = 'openai/gpt-oss-120b';
// El modelo razona antes de contestar y ese razonamiento cuenta en el tope, por eso el margen es amplio.
const MAX_MENSAJES = 14, MAX_CARACTERES = 16000, MAX_RESPUESTA = 1500;

function cabeceras(origen, permitido) {
  return {
    'Access-Control-Allow-Origin': permitido ? origen : 'null',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
    'Content-Type': 'application/json; charset=utf-8',
  };
}
const responde = (cuerpo, estado, cab) => new Response(JSON.stringify(cuerpo), { status: estado, headers: cab });

export default {
  async fetch(peticion, env) {
    const origen = peticion.headers.get('Origin') || '';
    const lista = (env.ORIGENES || ORIGENES_DEFECTO).split(',').map(s => s.trim()).filter(Boolean);
    const permitido = lista.includes(origen);
    const cab = cabeceras(origen, permitido);

    if (peticion.method === 'OPTIONS') return new Response(null, { status: 204, headers: cab });
    if (peticion.method !== 'POST') return responde({ error: 'method', mensaje: 'POST only.' }, 405, cab);
    if (!permitido) return responde({ error: 'origin', mensaje: 'This site cannot use the assistant.' }, 403, cab);
    if (!env.GROQ_API_KEY) return responde({ error: 'config', mensaje: 'The GROQ_API_KEY secret is missing in the Worker.' }, 500, cab);

    let datos;
    try { datos = await peticion.json(); } catch (e) { return responde({ error: 'format', mensaje: 'The body is not JSON.' }, 400, cab); }
    const mensajes = Array.isArray(datos && datos.messages) ? datos.messages : null;
    if (!mensajes || !mensajes.length || mensajes.length > MAX_MENSAJES) return responde({ error: 'format', mensaje: 'Message list is empty or too long.' }, 400, cab);
    let total = 0;
    for (const m of mensajes) {
      if (!m || !['system', 'user', 'assistant'].includes(m.role) || typeof m.content !== 'string') return responde({ error: 'format', mensaje: 'Malformed message.' }, 400, cab);
      total += m.content.length;
    }
    if (total > MAX_CARACTERES) return responde({ error: 'size', mensaje: 'Conversation too long.' }, 413, cab);

    const pide = extra => fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + env.GROQ_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: env.MODELO || MODELO_DEFECTO, messages: mensajes, temperature: 0.4, max_tokens: MAX_RESPUESTA, ...extra }),
    });
    let r;
    try {
      // Poco razonamiento y sin mostrarlo: respuestas rápidas. Si el modelo no admite esos ajustes, se repite sin ellos.
      r = await pide({ reasoning_effort: 'low', include_reasoning: false });
      if (r.status === 400) r = await pide({});
    } catch (e) { return responde({ error: 'network', mensaje: 'Could not reach the model.' }, 502, cab); }

    if (r.status === 429) return responde({ error: 'limit', mensaje: 'Free tier limit reached; wait a minute.' }, 429, cab);
    if (!r.ok) { let detalle = ''; try { detalle = (await r.json()).error.message; } catch (e) {} return responde({ error: 'model', mensaje: detalle || 'The model returned an error.', estado: r.status }, 502, cab); }
    const j = await r.json();
    const texto = j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
    if (!texto) return responde({ error: 'empty', mensaje: 'The model returned no text.' }, 502, cab);
    return responde({ text: texto }, 200, cab);
  },
};
