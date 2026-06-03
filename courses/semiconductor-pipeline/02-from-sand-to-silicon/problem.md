## A wafer is a reusable canvas until it is diced

Semiconductor manufacturing begins with purified silicon, grown into a single
crystal ingot, sliced into wafers, polished, and cleaned. A leading logic wafer
is usually 300 mm in diameter. The wafer is not one chip. It is a round canvas
that will carry many repeated chip patterns, called dies.

![Silicon wafer with repeated die patterns](/courses/semiconductor-pipeline/silicon-wafer.jpg)

*A processed silicon wafer: the repeated rectangular patterns are candidate die.
The wafer is the unit that moves through the fab; only later is it tested,
diced, and turned into individual chips.*

The shiny circular object is the manufacturing unit. Each square or rectangular
region will become a die only after the wafer survives fabrication, inspection,
sort, dicing, and packaging.

![Fab process loop](/courses/semiconductor-pipeline/fab-process-loop.png)

*The core fab loop. Manufacturing is not one linear operation; a wafer cycles
through deposition, lithography, etch, implant, CMP, and inspection again and
again until the transistor and wiring layers are built.*

The fab does not build a transistor in one pass. It repeats loops of film
formation, patterning, material removal, doping, cleaning, measurement, and
planarization until the device layers and wiring stack are complete.

![Semiconductor cleanroom with fabrication equipment](/courses/semiconductor-pipeline/cleanroom-fab.jpg)

*A real cleanroom environment. The tools, airflow, gowning, and material
handling are part of manufacturing economics because tiny particles can ruin
features far smaller than the eye can see.*

The cleanroom is part of the product. Air handling, gowning, chemical delivery,
automation, and tool maintenance all exist to keep microscopic particles and
process drift from turning expensive wafer starts into scrap.

## Front-end and back-end of line

**Front-end of line** (FEOL) builds the transistors themselves: wells, gates,
channels, source/drain regions, isolation, and local structures. This is where
device physics is most visible.

**Middle and back-end of line** build contacts and metal interconnects. Modern
chips contain many wiring layers. The lower layers are tiny and dense; upper
layers are thicker because they carry power and longer-distance signals.

Outside the fab, the wafer goes through wafer sort, dicing, packaging, final
test, and system integration.

## The core process loop

**Deposition** adds a thin film to the wafer. The film might be an insulator,
a conductor, a barrier, or a semiconductor material. Chemical vapor deposition,
physical vapor deposition, and atomic layer deposition are common families.

**Photoresist coating** covers the wafer with a light-sensitive material. The
resist becomes the temporary stencil for the next pattern.

**Lithography** projects a mask pattern onto the resist. The exposed resist is
developed so some regions remain and others are removed. Lithography decides
where the next operation is allowed to act.

**Etch** removes material from exposed regions. Wet etch uses chemistry in
liquid form; dry plasma etch uses reactive gases. Etch must remove the right
material, stop at the right layer, and maintain tiny shapes.

**Implant and doping** introduce atoms that change silicon's electrical
behavior. Doping creates p-type and n-type regions so transistors can switch.
The wafer may later be annealed to repair crystal damage and activate dopants.

**CMP** (chemical mechanical planarization) polishes the wafer flat. Flatness is
not cosmetic. Lithography and multilayer wiring need a controlled surface.

**Metrology and inspection** measure what happened. Critical dimension,
overlay, film thickness, defect maps, and electrical test structures tell the
fab whether the process is drifting. Measurement is part of manufacturing, not
an afterthought.

## Test, dice, package

After wafer fabrication, the fab or test partner probes dies on the wafer. This
is **wafer sort**. Some dies are marked bad; others are binned by speed, power,
or function.

The wafer is then **diced** into individual dies. Good dies move to packaging.
Packaging protects the silicon, connects it to the outside world, spreads heat,
and increasingly integrates multiple dies or memory stacks into one product.

Final test checks the packaged part. A passing packaged chip can then move into
boards, systems, data centers, cars, phones, or industrial equipment.

## Why the loop is hard

The process loop is repeated hundreds of times, and small errors accumulate.
Pattern placement must align to previous layers. Films must be uniform across
the wafer. Etch must preserve shape. Particles must be controlled. Measurements
must be fast enough to guide production without stopping it.

Yield is the scorecard for this entire system. A wafer with many beautifully
processed dies is not economically useful if too few of those dies work.

## Recap

Chip manufacturing is a repeated pattern-transfer and materials-control loop:
deposition, lithography, etch, implant, CMP, metrology, and test. Next, you
will turn that intuition into a tiny capacity and yield model.
