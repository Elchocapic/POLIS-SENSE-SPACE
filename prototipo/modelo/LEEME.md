# Modelo humano revisado — GLB, CC0

Archivo principal: **cuerpo_humano_A_CC0.glb**. Esta revisión sustituye la geometría anterior.

## Ajuste a las imágenes

Se utilizaron las tres imágenes proporcionadas por el usuario como guía visual para una anatomía masculina adulta: relación entre hombros y pelvis, volumen del tórax, cintura, glúteos, muslos y pantorrillas, y longitud de las extremidades. Se aplicaron formas anatómicas masculinas, musculatura y proporciones de los recursos oficiales de MakeHuman, en lugar de exportar su jaula base sin modificar.

El resultado es una aproximación visual. Las vistas de referencia tienen perspectiva y no permiten recuperar medidas exactas de todas las superficies. No se afirma que este archivo sea la malla original de Cults ni que reproduzca sus dimensiones con exactitud.

Los brazos quedan en una postura A suave, aproximadamente a 22° del torso, para poder separar las zonas del brazo y del tórax en la aplicación. Las piernas tienen una separación pequeña, cercana a una postura de pie natural. La pose está horneada en los vértices y coincide con la pose de reposo del esqueleto: el modelo no depende de una animación para verse así.

## Especificaciones verificadas

| Propiedad | Resultado |
| --- | --- |
| Formato | glTF 2.0 binario, un archivo GLB autónomo |
| Objetos de malla en el GLB | 1 |
| Primitivas / llamadas de dibujo | 1 |
| Vértices del GLB | 54 046, por debajo del límite de 65 000 |
| Triángulos | 108 080 |
| Huesos con nombres | 163 |
| Influencias máximas por vértice | 4, normalizadas |
| Texturas, materiales, UV y colores de vértice | Ninguno |
| Animaciones y morph targets | Ninguno |
| Ropa, pelo y accesorios | Ninguno |
| Altura elegida para el archivo | Aproximadamente 1.78 m; pies en Y=0 |
| Dependencias externas | Ninguna |

La malla contiene una superficie corporal continua y dos superficies oculares, todas dentro del mismo objeto y la misma primitiva. No hay objetos separados para los ojos. Se aplicó una subdivisión para suavizar la superficie sin reducir la malla mediante decimación.

El archivo fue comprobado con el validador oficial de Khronos, versión 2.0.0-dev.3.10: **0 errores y 0 advertencias**. También se comprobaron los índices, normales, pesos, matrices de reposo, bordes y triángulos. Los informes se incluyen en este paquete.

## Huesos y referencias anatómicas

Se conserva el esqueleto oficial de MakeHuman con nombres originales. Ejemplos:

| Zona | Huesos de referencia |
| --- | --- |
| Cabeza | `head` |
| Cuello | `neck01`, `neck02`, `neck03` |
| Tórax y espalda alta | `spine01`, `spine02` |
| Espalda baja | `spine03`, `spine04`, `spine05` |
| Pelvis | `pelvis.L`, `pelvis.R` |
| Brazo | `upperarm01.L/R`, `upperarm02.L/R` |
| Antebrazo | `lowerarm01.L/R`, `lowerarm02.L/R` |
| Mano | `wrist.L/R`, además de huesos de los dedos |
| Muslo | `upperleg01.L/R`, `upperleg02.L/R` |
| Pierna inferior | `lowerleg01.L/R`, `lowerleg02.L/R` |
| Pie | `foot.L/R`, además de huesos de los dedos |

`L` y `R` significan izquierda y derecha anatómicas. `ZONAS_Y_HUESOS.json` contiene una agrupación de referencia. El GLB conserva los 125 marcadores originales transformados en `meshes[0].extras.anatomical_landmarks` y la agrupación de huesos en `meshes[0].extras.bone_regions`.

Estas referencias ayudan a definir zonas, pero la asignación final de zonas de dolor sigue correspondiendo a la aplicación. No se probó el conversor ni la web del equipo porque no se proporcionaron sus archivos o URL.

## Procedencia y licencia

La geometría de partida, las formas anatómicas y el esqueleto proceden de los recursos gráficos oficiales de **MakeHuman**, publicados bajo **CC0 1.0**. Los ojos son superficies geométricas generadas durante esta preparación e integradas en el mismo objeto; también se entregan bajo CC0 1.0.

- [Repositorio oficial](https://github.com/makehumancommunity/makehuman).
- [Licencia de los recursos gráficos, secciones C y D](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.md).
- [Malla original hm08](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/3dobjs/base.obj).
- [Formas anatómicas oficiales](https://github.com/makehumancommunity/makehuman/tree/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/targets).
- [Esqueleto oficial](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/rigs/default.mhskel).

Versión exacta del repositorio: `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`. Consulta y preparación: 15 de noviembre de 2026. `PROCEDENCIA.json` conserva las URL y los SHA-256 de los archivos utilizados. `PARAMETROS_MODELO.json` registra las formas aplicadas y sus valores.

CC0 permite modificar, redistribuir y publicar este GLB, incluido su uso comercial, sin exigir atribución. Se adjuntan el texto completo de CC0 y la declaración de licencia del proyecto.

Las imágenes proporcionadas y el [enlace de Cults indicado por el usuario](https://cults3d.com/es/modelo-3d/variado/i-elcabezon22222) se utilizaron únicamente como referencia visual. No se pudo verificar la licencia de esa ficha; no se descargó ni incorporó geometría de Cults y no se atribuye CC0 a ese modelo externo.

## Coordenadas y previsualización

Unidades glTF: metros. Y hacia arriba, Z hacia la parte anterior del cuerpo y X positivo hacia su izquierda anatómica. La altura de 1.78 m es una elección de escala para este archivo, no una medida obtenida de las fotografías.

`vista_del_modelo_glb.png` es un render de la geometría del GLB desde delante, detrás y de lado. La iluminación y el material gris usados para visualizarlo no forman parte del GLB. La aplicación puede asignarle sus propios materiales y colores.
