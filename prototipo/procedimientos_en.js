// =====================================================================
// PROCEDURES (English version used by tripulacion.html; sample content, protocol citation pending)
// The Spanish original lives in plantilla.html. Keywords include English and Spanish words.
// =====================================================================
const PROC = {
  lesion:{ titulo:'Limb injury', claves:'arm leg hit bump injury injured fracture broken sprain twisted swelling swollen limb hand foot fall brazo pierna golpe lesion fractura esguince',
    pasos:x=>['Stop the activity and support the limb in a comfortable position.',
      `Check the color, temperature and sensation of the ${x==='pierna'?'foot':'hand'}, and the pulse at the ${x==='pierna'?'ankle':'wrist'}.`,
      'Immobilize it with the splint and secure it with the bandage without tightening.','Apply cold for 15 to 20 minutes, wrapped in cloth.','Record pain and mobility again in 2 hours.'],
    escalar:'Contact the flight surgeon if there is deformity, numbness, cold or pale skin, or if the pain does not go down.',
    items:x=>['Moldable splint','Elastic bandage','Cold pack', x==='pierna'?'Restraint strap':'Arm sling','Blunt-tip scissors','Painkiller from the medical kit (with medical authorization)'] },
  fiebre:{ titulo:'Fever', claves:'fever temperature hot chills shivering infection fiebre temperatura escalofrios infeccion',
    pasos:()=>['Repeat the measurement in 15 minutes to confirm.','Record pulse, breathing and oxygen saturation.','Drink fluids and skip today\'s exercise.','Wear a mask and reduce close contact with the crew.','Take your temperature every 4 hours and note any new symptoms.'],
    escalar:'Contact the flight surgeon if you reach 39 °C, saturation drops below 94 %, there is confusion, or the fever lasts more than 24 hours.',
    items:()=>['Thermometer','Pulse oximeter','Drink bag','Face mask','Fever reducer from the medical kit (with medical authorization)'] },
  co2:{ titulo:'High CO₂ in the cabin', claves:'co2 carbon dioxide air ventilation cabin breathe breathing scrubber environment stuffy aire ventilacion cabina',
    pasos:()=>['Move to a module with better ventilation.','Measure CO₂ in the other modules.','Check the CO₂ scrubber and clear any blocked vents.','Avoid exercising in this module until the reading drops.','Measure CO₂ and symptoms again in 30 minutes.'],
    escalar:'Contact mission control if CO₂ does not go down, or if confusion or difficulty breathing appears.',
    items:()=>['Portable CO₂ meter','Portable fan','Spare scrubber cartridge','Pulse oximeter'] },
  sueno:{ titulo:'Lack of sleep', claves:'sleep sleeping insomnia tired tiredness fatigue awake sleepless sueno dormir insomnio cansado',
    pasos:()=>['Tell the crew before critical tasks and ask for a second check.','Reschedule anything that is not urgent.','Take a 20 to 30 minute nap if today\'s plan allows it.','Avoid caffeine 6 hours before bed and dim the lights an hour before.'],
    escalar:'Contact the flight surgeon if you sleep less than 6 hours three nights in a row.',
    items:()=>['Eye mask','Earplugs','Sleep log'] },
  atencion:{ titulo:'Reduced attention', claves:'attention focus concentration reaction slow test errors mistakes distracted atencion concentracion',
    pasos:()=>['Do not do critical tasks alone today: ask for a double check.','Rest for 20 to 30 minutes.','Repeat the attention test after resting.','Check how much you slept the last three nights.'],
    escalar:'Contact the flight surgeon if the result stays low after a good night\'s sleep.',
    items:()=>['Task checklist','Crewmate for double check'] },
  animo:{ titulo:'Low mood or high stress', claves:'mood sad sadness stress stressed anxiety anxious alone lonely loneliness isolation family nervous overwhelmed animo triste estres ansiedad soledad',
    pasos:()=>['Tell a crewmate how you feel today.','Schedule a message or a call with your family.','Keep your exercise routine and your sleep schedule.','Spend 30 minutes on something you enjoy.','Repeat the check-in tomorrow.'],
    escalar:'Ask for a private conference with the psychological support team if this lasts 3 days or more.',
    items:()=>['Free time in today\'s plan','Communication channel with family','Personal journal'] },
  radiacion:{ titulo:'Solar radiation event', claves:'radiation solar storm flare dose dosimeter shelter protons sun radiacion tormenta',
    pasos:()=>['Go to the shelter: the most shielded area of the spacecraft.','Suspend activities outside the shelter.','Read your personal dosimeter every hour and log it.','Stay in the shelter until the dose returns to its usual value.'],
    escalar:'Report the received dose to mission control. Contact the flight surgeon if there is nausea or vomiting.',
    items:()=>['Personal dosimeter','Water and food for 24 hours','Medical kit','Dose log'] },
  pulso:{ titulo:'Pulse outside your range', claves:'pulse heart heartbeat beats palpitations tachycardia heart rate high fast racing pulso corazon latidos palpitaciones',
    pasos:()=>['Repeat the measurement after 10 minutes of rest, seated and without talking.','Record temperature, oxygen saturation and breathing.','Hydrate and avoid intense exercise today.','Review how you slept and how much exercise you did in the last 2 days.','Measure again tomorrow when you wake up.'],
    escalar:'Contact the flight surgeon if it persists for 2 days or there are palpitations, dizziness, chest pain or shortness of breath.',
    items:()=>['Pulse oximeter','Thermometer','Blood pressure monitor','Drink bag','Exercise and sleep log'] },
  fatiga:{ titulo:'Fatigue or low readiness', claves:'fatigue exhausted exhaustion energy readiness weak drained performance worn fatiga agotado energia debil',
    pasos:()=>['Lower the intensity of today\'s exercise.','Finish the planned meals and hydration.','Take the attention test before a critical task.','Go to bed at the scheduled time.','Repeat the check-in tomorrow.'],
    escalar:'Contact the flight surgeon if it lasts 3 days or more, or if fever or a pulse outside your range is added.',
    items:()=>['Today\'s exercise plan','Drink bag','Full daily ration','Sleep log'] },
  muscular:{ titulo:'Muscle pain', claves:'muscle muscular sore soreness aching overload overuse cramp stretch stiff musculo agujetas',
    pasos:()=>['Lower the exercise load on the affected area.','Gently stretch the area for 5 to 10 minutes.','If the pain is recent, apply cold for 15 minutes, wrapped in cloth.','Record the pain again tomorrow.'],
    escalar:'Contact the flight surgeon if the pain is intense, lasts more than 3 days, or there is swelling or loss of mobility.',
    items:()=>['Cold pack','Elastic band for stretching','Adjusted exercise plan','Painkiller from the medical kit (with medical authorization)'] },
  dolor:{ titulo:'Localized pain', claves:'pain hurts hurt ache discomfort chest abdomen stomach head dolor duele molestia',
    pasos:()=>['Describe the pain: when it started, what it feels like and how strong it is.','Record all vital signs now.','Repeat the record in 1 hour.'],
    escalar:'Contact the flight surgeon if the pain increases or other symptoms appear. Chest pain: contact them immediately.',
    items:()=>['Blood pressure monitor','Pulse oximeter','Thermometer'] },
};
const fold = s => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const DIAGNOSTICO = /(what do i have|do i have an? (infection|fracture|disease|illness|tumou?r)|diagnos|what disease|am i sick|medicat|pill|dose of|dosage|prescri|should i take|what (should|can) i take)/;
function responder(q){
  const f = fold(q.slice(0,200));
  if (!f.trim()) return {tipo:'vacio'};
  if (DIAGNOSTICO.test(f)) return {tipo:'negativa'};
  const palabras = f.split(/[^a-z0-9]+/).filter(w => w.length > 2);
  let mejor = null, puntos = 0;
  for (const k in PROC){
    const claves = (PROC[k].claves + ' ' + fold(PROC[k].titulo)).split(' ');
    const p = palabras.filter(w => claves.includes(w)).length;
    if (p > puntos){ puntos = p; mejor = k; }
  }
  return mejor ? {tipo:'proc', proc:mejor} : {tipo:'nada'};
}
