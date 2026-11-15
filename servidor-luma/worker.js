// Intermediario de Luma para Cloudflare Workers (plan gratuito).
// La página pública le envía la conversación; el Worker añade la clave secreta y consulta a Groq.
// La clave nunca está en la página: se guarda como secreto GROQ_API_KEY en Cloudflare.
//
// Variables (Settings → Variables and Secrets):
//   GROQ_API_KEY  (secreto, obligatorio)  clave creada en console.groq.com
//   MODELO        (texto, opcional)       por defecto llama-3.3-70b-versatile
//   ORIGENES      (texto, opcional)       sitios que pueden usarlo, separados por coma

const ORIGENES_DEFECTO = 'https://elchocapic.github.io,http://localhost:8000,http://127.0.0.1:8000';
const MAX_MENSAJES = 14, MAX_CARACTERES = 16000, MAX_RESPUESTA = 450;

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
    if (peticion.method !== 'POST') return responde({ error: 'metodo', mensaje: 'Solo POST.' }, 405, cab);
    if (!permitido) return responde({ error: 'origen', mensaje: 'Este sitio no puede usar el asistente.' }, 403, cab);
    if (!env.GROQ_API_KEY) return responde({ error: 'config', mensaje: 'Falta el secreto GROQ_API_KEY en el Worker.' }, 500, cab);

    let datos;
    try { datos = await peticion.json(); } catch (e) { return responde({ error: 'formato', mensaje: 'El cuerpo no es JSON.' }, 400, cab); }
    const mensajes = Array.isArray(datos && datos.messages) ? datos.messages : null;
    if (!mensajes || !mensajes.length || mensajes.length > MAX_MENSAJES) return responde({ error: 'formato', mensaje: 'Lista de mensajes vacía o demasiado larga.' }, 400, cab);
    let total = 0;
    for (const m of mensajes) {
      if (!m || !['system', 'user', 'assistant'].includes(m.role) || typeof m.content !== 'string') return responde({ error: 'formato', mensaje: 'Mensaje con forma incorrecta.' }, 400, cab);
      total += m.content.length;
    }
    if (total > MAX_CARACTERES) return responde({ error: 'tamano', mensaje: 'Conversación demasiado larga.' }, 413, cab);

    let r;
    try {
      r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + env.GROQ_API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: env.MODELO || 'llama-3.3-70b-versatile', messages: mensajes, temperature: 0.4, max_tokens: MAX_RESPUESTA }),
      });
    } catch (e) { return responde({ error: 'red', mensaje: 'No se pudo contactar con el modelo.' }, 502, cab); }

    if (r.status === 429) return responde({ error: 'limite', mensaje: 'Se alcanzó el límite gratuito; espera un minuto.' }, 429, cab);
    if (!r.ok) { let detalle = ''; try { detalle = (await r.json()).error.message; } catch (e) {} return responde({ error: 'modelo', mensaje: detalle || 'El modelo devolvió un error.', estado: r.status }, 502, cab); }
    const j = await r.json();
    const texto = j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
    if (!texto) return responde({ error: 'vacio', mensaje: 'El modelo no devolvió texto.' }, 502, cab);
    return responde({ text: texto }, 200, cab);
  },
};
