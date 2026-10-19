from manim import *
from manim_slides import Slide
import numpy as np
import manimpango
from pathlib import Path
from render3d import Modelo3D

config.frame_rate = 60
config.background_color = BLACK

VERDE_OSCURO = ManimColor("#0B5D2A")
VERDE = ManimColor("#22B14C")
VERDE_CLARO = ManimColor("#B8F5C8")
# Fuente de 3Blue1Brown: Computer Modern (CMU Serif), cargada desde la carpeta fuentes/
for _f in (Path(__file__).parent / "fuentes").glob("*.otf"):
    manimpango.register_font(str(_f))
FUENTE = "CMU Serif"


def esfera(radio=1.0, capas=24):
    """Círculo con capas concéntricas desplazadas hacia arriba-izquierda para simular volumen."""
    grupo = VGroup()
    for i in range(capas):
        t = i / (capas - 1)
        r = radio * (1 - 0.85 * t)
        color = interpolate_color(VERDE_OSCURO, VERDE, min(1, 2 * t)) if t < 0.5 else interpolate_color(
            VERDE, VERDE_CLARO, (t - 0.5) * 2
        )
        c = Circle(radius=r, stroke_width=0).set_fill(color, 1)
        c.move_to(radio * 0.35 * t * (UL / np.linalg.norm(UL)))
        grupo.add(c)
    return grupo


def fragmento(radio, angulo_inicio, angulo, semilla):
    """Trozo roto de esfera: un pedazo de la superficie curva con bordes de quiebre irregulares.
    Se recorta la esfera sombreada para que conserve la luz y el volumen."""
    rng = np.random.default_rng(semilla)
    a1, a2 = angulo_inicio, angulo_inicio + angulo
    medio = (a1 + a2) / 2
    arco = [1.02 * radio * np.array([np.cos(a), np.sin(a), 0]) for a in np.linspace(a1, a2, 12)]
    vertice = radio * rng.uniform(-0.05, 0.15) * np.array([np.cos(medio), np.sin(medio), 0])

    def quiebre(desde, hasta, n=4):
        d = hasta - desde
        perp = np.array([-d[1], d[0], 0]) / (np.linalg.norm(d) + 1e-9)
        pts = []
        for k in range(1, n):
            t = k / n + rng.uniform(-0.06, 0.06)
            pts.append(desde + t * d + perp * rng.uniform(-0.09, 0.09) * radio)
        return pts

    borde = quiebre(arco[-1], vertice) + [vertice] + quiebre(vertice, arco[0])
    forma = Polygon(*arco, *borde)

    # Canto: la misma forma corrida y oscura detrás, para que el trozo tenga espesor
    canto = forma.copy().shift(0.09 * radio * DR).set_stroke(width=0).set_fill(VERDE_OSCURO, 1)
    pieza = VGroup(canto)
    for capa in esfera(radio):
        trozo = Intersection(capa, forma)
        if len(trozo.points):
            pieza.add(trozo.set_stroke(width=0).set_fill(capa.get_fill_color(), 1))
    # Línea de quiebre un poco más oscura para dar sensación de grieta
    grieta = VMobject().set_points_as_corners([arco[-1], *borde, arco[0]])
    grieta.set_stroke(VERDE_OSCURO, 2.5).set_fill(opacity=0)
    pieza.add(grieta)
    return pieza


def persona(escala=1.0):
    """Monigote: cabeza (círculo) + cuerpo (triángulo con esquinas redondeadas)."""
    cabeza = Circle(radius=0.38, stroke_width=5, color=WHITE).set_fill(BLACK, 1)
    cabeza.move_to([0, 0.55, 0])
    cuerpo = Polygon([0, 0.05, 0], [-0.45, -1.05, 0], [0.45, -1.05, 0], stroke_width=5, color=WHITE)
    cuerpo.round_corners(radius=0.12)
    cuerpo.set_fill(BLACK, 1)
    cuerpo.joint_type = LineJointType.ROUND
    return VGroup(cabeza, cuerpo).scale(escala)


def armar_discusion():
    """Las 6 personas, el globo con colas hacia cada una y los insultos (slides 3 y 5)."""
    xs = [-5, -3, -1, 1, 3, 5]
    personas = VGroup(*[persona().move_to([x, -2.3, 0]) for x in xs])
    centro_globo = [0, 1.7, 0]
    colas = [(TAU - np.arccos(x / 6.2), 0.5, [x * 0.97, -0.95, 0]) for x in xs]
    globo = globo_dialogo(centro_globo, 6.2, 1.75, colas)
    insultos = Text("!@#$%^&*!@#$%", font=FUENTE)
    insultos.scale_to_fit_width(8.5).move_to(centro_globo)
    return personas, globo, insultos


CARPETA = Path(__file__).parent


def cara(nombre, alto):
    """Foto de caras/<nombre>.png recortada a su contorno (el fondo ya es transparente)."""
    from PIL import Image

    img = np.array(Image.open(CARPETA / "caras" / f"{nombre}.png").convert("RGBA"))
    ys, xs = np.nonzero(img[..., 3] > 20)
    img = img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    return ImageMobject(img).set_height(alto)


def poligono_suave(puntos, color, radio=0.06):
    """Polígono relleno con borde blanco y esquinas redondeadas. color=None → solo contorno."""
    p = Polygon(*puntos, stroke_width=5, color=WHITE).round_corners(radius=radio)
    p.joint_type = LineJointType.ROUND
    return p.set_fill(color if color is not None else BLACK, 1)


def triangulo(lado, color):
    h = lado * np.sqrt(3) / 2
    return poligono_suave([[0, 2 * h / 3, 0], [-lado / 2, -h / 3, 0], [lado / 2, -h / 3, 0]], color)


def estrella(radio, color):
    e = Star(6, outer_radius=radio, density=2, stroke_width=5, color=WHITE).round_corners(radius=0.04)
    e.joint_type = LineJointType.ROUND
    return e.set_fill(color, 1)


def circulo_lleno(radio, color):
    return Circle(radius=radio, stroke_width=5, color=WHITE).set_fill(color, 1)


def rect_suave(ancho, alto, centro, radio=0.12, grosor=6):
    """Rectángulo con esquinas redondeadas, borde blanco y relleno negro (sin costura al cerrar)."""
    r = RoundedRectangle(width=ancho, height=alto, corner_radius=radio, stroke_width=grosor, color=WHITE)
    r.set_fill(BLACK, 1).move_to(centro)
    r.joint_type = LineJointType.ROUND
    r.cap_style = CapStyleType.ROUND
    return r


def estrella_5(radio):
    e = Star(5, outer_radius=radio, density=2, stroke_width=4, color=WHITE).round_corners(radius=0.02)
    e.joint_type = LineJointType.ROUND
    return e.set_fill(ManimColor("#FFE500"), 1)


def habitacion(numero, centro, ancho=2.0, alto=3.8):
    """Puerta de habitación: marco (hueco negro), hoja (la puerta en sí, con picaporte) y número."""
    marco = rect_suave(ancho, alto, centro, radio=0.1)
    hoja = VGroup(
        rect_suave(ancho, alto, centro, radio=0.1),
        Circle(radius=0.17, stroke_width=5, color=WHITE).move_to(np.array(centro) + [ancho / 2 - 0.35, -0.1, 0]),
    )
    num = Text(str(numero), font=FUENTE, font_size=48).move_to(np.array(centro) + [0, alto / 2 - 0.5, 0])
    return marco, hoja, num


def reloj_mob(radio):
    """Reloj: esfera, 12 marcas, minutero y horario (ambos apuntando a las 12)."""
    esfera_r = Circle(radius=radio, stroke_width=5, color=WHITE).set_fill(BLACK, 1)
    marcas = VGroup(
        *[
            Line(ORIGIN, 0.13 * radio * UP, stroke_width=3, color=WHITE)
            .move_to(0.8 * radio * np.array([np.sin(a), np.cos(a), 0]))
            .rotate(-a)
            for a in np.arange(0, TAU, TAU / 12)
        ]
    )
    minutero = Line(ORIGIN, 0.72 * radio * UP, stroke_width=5, color=WHITE)
    horario = Line(ORIGIN, 0.45 * radio * RIGHT, stroke_width=6, color=WHITE)
    for l in (minutero, horario, *marcas):
        l.cap_style = CapStyleType.ROUND
    return VGroup(esfera_r, marcas, minutero, horario)


def simbolo_enojo(tam):
    """El típico símbolo de enojo (💢): cuatro arcos rojos gruesos que miran hacia el centro."""
    d, r = 0.55 * tam, 0.42 * tam
    arcos = VGroup()
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        centro = np.array([sx * d, sy * d, 0])
        hacia_centro = np.arctan2(-sy, -sx)
        a = Arc(radius=r, start_angle=hacia_centro - PI / 3.2, angle=2 * PI / 3.2, arc_center=centro)
        a.set_stroke(ManimColor("#D7262E"), 9).set_fill(opacity=0)
        a.cap_style = CapStyleType.ROUND
        arcos.add(a)
    return arcos


def corazon_mob(tam):
    c = ParametricFunction(
        lambda t: np.array(
            [16 * np.sin(t) ** 3, 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t), 0]
        ),
        t_range=[0, TAU, TAU / 200],
    )
    c.close_path()
    c.set_fill(ManimColor("#E8222A"), 1).set_stroke(WHITE, 3)
    c.joint_type = LineJointType.ROUND
    return c.set_height(tam)


def botones_mob():
    """Empleado del hotel: monigote con saco rojo, botones dorados, moñito y gorrito de botones."""
    rojo, dorado = ManimColor("#C0262D"), ManimColor("#F2C230")
    p = persona()
    cabeza, cuerpo = p
    cuerpo.set_fill(rojo, 1)
    gorro = RoundedRectangle(width=0.5, height=0.26, corner_radius=0.07, stroke_width=4, color=WHITE)
    gorro.set_fill(rojo, 1).move_to(cabeza.get_top() + UP * 0.1 + RIGHT * 0.05).rotate(-0.15)
    cinta = Line(gorro.get_corner(DL), gorro.get_corner(DR), stroke_width=5, color=dorado).shift(UP * 0.06)
    cinta.rotate(-0.15).move_to(gorro.get_center() + DOWN * 0.06)
    mono = VGroup(
        poligono_suave([[0, 0.04, 0], [-0.16, 0.12, 0], [-0.16, -0.04, 0]], dorado, radio=0.02),
        poligono_suave([[0, 0.04, 0], [0.16, 0.12, 0], [0.16, -0.04, 0]], dorado, radio=0.02),
    ).set_stroke(width=2).move_to(cuerpo.get_top() + DOWN * 0.08)
    botones = VGroup(
        *[Dot(radius=0.045, color=dorado).move_to(cuerpo.get_center() + DOWN * dy) for dy in (0.05, 0.35)]
    )
    return VGroup(p, gorro, cinta, mono, botones)


def persona_con_cara(nombre, escala):
    """Monigote cuya cabeza es la foto caras/<nombre>.png. Mantiene el orden [cabeza, cuerpo, foto]
    para que el resto del código (que usa p[0] como cabeza) siga funcionando."""
    p = persona().scale(escala)
    cabeza, cuerpo = p
    cabeza.set_stroke(opacity=0).set_fill(opacity=0)  # el círculo queda invisible, solo como referencia
    foto = cara(nombre, cabeza.height * 1.35).move_to(cabeza.get_center() + UP * 0.04 * escala)
    return Group(cabeza, cuerpo, foto)


def persona_feliz(escala):
    """Monigote con un corazoncito arriba a la derecha de la cabeza."""
    p = persona().scale(escala)
    c = corazon_mob(0.36 * escala / 1.3).move_to(p[0].get_center() + 0.36 * escala / 1.3 * np.array([1, 1, 0]))
    return VGroup(p, c)


def saltar_a(grupo, ref, destino, **kw):
    """Como saltar(), pero lleva al monigote `ref` (parte de `grupo`) hasta `destino`."""
    c = grupo.get_center()
    return saltar(grupo, c, c + (np.array(destino) - ref.get_center()), **kw)


def entrar(m):
    """Entra por una puerta: se achica un poco y se desvanece hacia adentro."""
    return FadeOut(m, shift=0.15 * UP, scale=0.8)


def mover_puerta(marco, hoja, num, abrir=True):
    """Abre (o cierra) una puerta: la hoja y su número giran juntos sobre la bisagra izquierda.
    Al abrir guarda la versión cerrada para poder volver exactamente a ella."""
    if abrir:
        hoja.cerrada = (hoja.copy(), num.copy())
        ancho_abierta = 0.16 * marco.width
        destino = VGroup(hoja.copy(), num.copy()).stretch_to_fit_width(ancho_abierta).next_to(marco, LEFT, buff=0)
        h, n = destino
    else:
        h, n = hoja.cerrada[0].copy(), hoja.cerrada[1].copy()
    return [Transform(hoja, h), Transform(num, n)]


def saltar(mob, desde, hasta, saltos=5, altura=0.35):
    """Mueve mob de `desde` a `hasta` dando saltitos (con un leve balanceo al caminar)."""
    desde, hasta = np.array(desde), np.array(hasta)
    original = mob.copy().move_to(desde)

    def update(m, alpha):
        fase = saltos * PI * alpha
        pos = interpolate(desde, hasta, alpha) + UP * altura * abs(np.sin(fase))
        m.become(original.copy().rotate(0.08 * np.sin(2 * fase)).move_to(pos))

    return UpdateFromAlphaFunc(mob, update)


def pos_zoom(m, p, zoom, destino):
    """Dónde queda el centro de m si se hace zoom x`zoom` alrededor de p y p se lleva a destino."""
    return p + zoom * (m.get_center() - p) + (destino - p)


def nube(centro, a, b, bultos=13, alto=0.38, grosor=6):
    """Nube de pensamiento: bultos redondeados hacia afuera de una elipse, con valles suaves (sin picos).
    Los bultos se reparten por longitud de arco para que sean todos del mismo tamaño."""
    c = np.array(centro)
    ts = np.linspace(0, TAU, 2000)
    pts = np.stack([a * np.cos(ts), b * np.sin(ts)], axis=1)
    largo = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    s_de_t = lambda t: np.interp(t, ts, largo) / largo[-1]
    eps = 0.18

    def punto(t):
        e = np.array([a * np.cos(t), b * np.sin(t), 0])
        n = normalize(np.array([b * np.cos(t), a * np.sin(t), 0]))
        sn = np.sin(PI * bultos * s_de_t(t))
        bulto = np.sqrt(sn**2 + eps**2) - eps  # |sin| suavizado: arcos redondos, valles sin punta
        return c + e + alto * bulto * n

    contorno = ParametricFunction(punto, t_range=[0, TAU, TAU / 720])
    contorno.close_path()
    contorno.joint_type = LineJointType.ROUND
    return contorno.set_stroke(WHITE, grosor).set_fill(BLACK, 1)


def globo_dialogo(centro, a, b, colas, grosor=6):
    """Globo de historieta trazado como una sola curva cerrada y suave.
    colas: lista de (angulo_en_elipse, medio_ancho, punta). Las colas salen tangentes a la elipse
    (sin quiebres) y terminan en una punta redondeada."""
    c = np.array(centro)

    def E(t):
        return c + np.array([a * np.cos(t), b * np.sin(t), 0])

    def dE(t):
        return np.array([-a * np.sin(t), b * np.cos(t), 0])

    datos = []
    for t_c, medio_ancho, punta in colas:
        d = medio_ancho / np.linalg.norm(dE(t_c))
        datos.append((t_c - d, t_c + d, np.array(punta)))
    datos.sort(key=lambda x: x[0])

    m = VMobject(joint_type=LineJointType.ROUND)

    def arco(t0, t1):
        n = max(1, int(np.ceil((t1 - t0) / (PI / 8))))
        ts = np.linspace(t0, t1, n + 1)
        for u, v in zip(ts[:-1], ts[1:]):
            k = 4 / 3 * np.tan((v - u) / 4)
            m.add_cubic_bezier_curve_to(E(u) + k * dE(u), E(v) - k * dE(v), E(v))

    inicio = datos[-1][1]
    m.start_new_path(E(inicio))
    arco(inicio, datos[0][0] + TAU)
    for i, (t1, t2, A) in enumerate(datos):
        largo = np.linalg.norm(A - E((t1 + t2) / 2))
        lam = 0.12 * largo
        p = normalize(E(t2) - E(t1))
        rho = 0.07
        m.add_cubic_bezier_curve_to(E(t1) + lam * normalize(dE(t1)), A - rho * p, A)
        m.add_cubic_bezier_curve_to(A + rho * p, E(t2) - lam * normalize(dE(t2)), E(t2))
        if i + 1 < len(datos):
            arco(t2, datos[i + 1][0])

    m.set_stroke(WHITE, grosor).set_fill(BLACK, 1)
    return m


class BanachTarski(Slide):
    def construct(self):
        # ---------- Slide 1: portada ----------
        titulo = Text("BANACH-TARSKI", font=FUENTE, font_size=64)
        autores = Text("Por Maletti, De Lauro y Moyano", font=FUENTE, font_size=34)
        portada = VGroup(titulo, autores).arrange(DOWN, buff=0.45)

        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(autores, shift=0.3 * UP))
        self.next_slide()

        # ---------- Slide 2: la paradoja ----------
        titulo_izq = VGroup(
            Text("Banach", font=FUENTE, font_size=60),
            Text("Tarski", font=FUENTE, font_size=60),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        titulo_izq.to_edge(LEFT, buff=0.8).shift(1.3 * UP)

        self.play(
            FadeOut(autores, shift=0.3 * DOWN),
            ReplacementTransform(titulo, titulo_izq),
            run_time=1.2,
        )

        esfera_arriba = esfera(1.15).move_to([0.6, 2.35, 0])
        self.play(GrowFromCenter(esfera_arriba), run_time=1)

        flecha = CurvedArrow(
            [0.3, 0.95, 0], [0.3, -1.05, 0], angle=-PI / 2.2, color=WHITE, stroke_width=5
        )

        # Fragmentos a la derecha de la flecha (salen de la esfera de arriba)
        fragmentos = VGroup(
            fragmento(0.95, 0.9 * PI, 0.5 * PI, 1).rotate(-1.1).move_to([1.7, -0.05, 0]),
            fragmento(0.9, 0.3 * PI, 0.45 * PI, 2).rotate(2.2).move_to([3.0, 0.8, 0]),
            fragmento(1.0, -0.2 * PI, 0.55 * PI, 3).rotate(-2.4).move_to([4.45, -0.3, 0]),
            fragmento(0.8, 1.35 * PI, 0.4 * PI, 4).rotate(1.3).move_to([3.3, -1.05, 0]),
        )

        self.play(Create(flecha), run_time=1)
        self.play(
            LaggedStart(
                *[
                    FadeIn(f, target_position=esfera_arriba.get_center(), scale=0.4)
                    for f in fragmentos
                ],
                lag_ratio=0.2,
            ),
            run_time=1.6,
        )

        esfera_izq = esfera(1.15).move_to([-0.9, -2.55, 0])
        esfera_der = esfera(1.15).move_to([2.0, -2.55, 0])
        self.play(
            GrowFromCenter(esfera_izq),
            GrowFromCenter(esfera_der),
            run_time=1.2,
        )

        # Movimiento suave de los fragmentos en loop (vuelve al punto inicial)
        self.next_slide(loop=True)
        originales = [f.copy() for f in fragmentos]
        params = [
            (np.array([0.12, 0.10, 0]), 0.10, 0.0),
            (np.array([-0.10, 0.14, 0]), -0.12, 1.3),
            (np.array([0.14, -0.08, 0]), 0.09, 2.6),
            (np.array([-0.08, -0.12, 0]), -0.10, 4.0),
        ]

        def flotar(f, orig, desp, giro, fase):
            def update(mob, alpha):
                s = np.sin(TAU * alpha + fase) - np.sin(fase)
                mob.become(orig.copy().rotate(giro * s).shift(desp * s))

            return UpdateFromAlphaFunc(f, update)

        self.play(
            *[flotar(f, o, *p) for f, o, p in zip(fragmentos, originales, params)],
            run_time=4,
            rate_func=linear,
        )
        self.next_slide()

        # ---------- Slide 3: la discusión ----------
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)

        personas, globo, insultos = armar_discusion()

        self.play(LaggedStart(*[FadeIn(p, shift=0.3 * UP) for p in personas], lag_ratio=0.12), run_time=1.2)
        self.play(FadeIn(globo, scale=0.85), run_time=0.9)
        self.play(Write(insultos), run_time=1)

        self.next_slide(loop=True)
        self.loop_discusion(personas, insultos)
        self.next_slide()

        # Círculo rojo sobre la segunda persona
        elegido = personas[1]
        circulo = Circle(radius=1.35, color=RED, stroke_width=8).move_to(elegido)
        self.play(Create(circulo), run_time=0.8)
        self.next_slide()

        # ---------- Slide 4: zoom a la persona elegida ----------
        destino = np.array([-4.6, -0.6, 0])
        zoom = 3
        p = elegido.get_center()

        resto = [m for i, m in enumerate(personas) if i != 1] + [globo, insultos, circulo]
        self.play(
            elegido.animate.scale(zoom).move_to(destino).set_stroke(width=10),
            *[FadeOut(m, shift=pos_zoom(m, p, zoom, destino) - m.get_center(), scale=zoom) for m in resto],
            run_time=1.6,
        )

        centro4 = [2.3, 1.4, 0]
        globo4 = globo_dialogo(centro4, 3.75, 1.8, [(PI + 0.3, 0.6, [-3.0, 0.6, 0])], grosor=7)
        texto4 = VGroup(
            Text("AXIOMA DE", font=FUENTE, font_size=60),
            Text("ELECCIÓN...", font=FUENTE, font_size=60),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(centro4)

        self.play(FadeIn(globo4, scale=0.85), run_time=0.8)
        self.play(Write(texto4), run_time=1.5)
        self.next_slide()

        # ---------- Slide 5: vuelve la discusión (zoom hacia atrás) ----------
        personas, globo, insultos = armar_discusion()
        p = personas[1].get_center()
        resto = [m for i, m in enumerate(personas) if i != 1] + [globo, insultos]
        self.play(FadeOut(globo4), FadeOut(texto4), run_time=0.5)
        self.play(
            ReplacementTransform(elegido, personas[1]),
            *[FadeIn(m, shift=m.get_center() - pos_zoom(m, p, zoom, destino), scale=zoom) for m in resto],
            run_time=1.6,
        )

        self.next_slide(loop=True)
        self.loop_discusion(personas, insultos)
        self.next_slide()

        # Círculo rojo sobre los dos últimos
        pareja = VGroup(personas[4], personas[5])
        circulo = Ellipse(width=pareja.width + 1.3, height=pareja.height + 0.9, color=RED, stroke_width=8)
        circulo.move_to(pareja)
        self.play(Create(circulo), run_time=0.8)
        self.next_slide()

        # ---------- Slide 6: "No tiene sentido" ----------
        escala6 = 1.3
        destino6 = np.array([-4.9, -2.45, 0])
        p = pareja.get_center()
        resto = [personas[i] for i in range(4)] + [globo, insultos]
        objetivo = pareja.copy().scale(escala6).move_to(destino6)
        self.play(
            pareja.animate.scale(escala6).move_to(destino6),
            FadeOut(circulo, shift=destino6 - p, scale=escala6),
            *[FadeOut(m, shift=pos_zoom(m, p, escala6, destino6) - m.get_center(), scale=escala6) for m in resto],
            run_time=1.6,
        )

        centro6 = np.array([1.0, 1.5, 0])
        pensamiento = nube(centro6, 4.8, 1.85)
        texto6 = Text("No tiene sentido", font=FUENTE, font_size=66).move_to(centro6)
        # Burbujitas que van de las cabezas a la nube
        cabezas_centro = (objetivo[0][0].get_center() + objetivo[1][0].get_center()) / 2
        inicio = cabezas_centro + np.array([0.9, 0.9, 0])
        fin = np.array([-2.4, -0.55, 0])
        burbujas = VGroup(
            *[
                Ellipse(width=w, height=w * 0.6, stroke_width=5, color=WHITE)
                .set_fill(BLACK, 1)
                .move_to(interpolate(inicio, fin, t))
                for w, t in [(0.35, 0.0), (0.55, 0.45), (0.85, 1.0)]
            ]
        )
        self.play(LaggedStart(*[GrowFromCenter(b) for b in burbujas], lag_ratio=0.35), run_time=0.9)
        self.play(GrowFromPoint(pensamiento, fin), run_time=0.9)
        self.play(Write(texto6), run_time=1.2)
        self.next_slide()

        # ---------- Slide 7: los dos de cerca, "BANACH-TARSKI" ----------
        atras, adelante = pareja
        self.play(
            FadeOut(pensamiento, scale=1.2),
            FadeOut(texto6, scale=1.2),
            FadeOut(burbujas),
            atras.animate.scale(3 / escala6).move_to([-5.15, -0.35, 0]).set_stroke(width=10),
            adelante.animate.scale(3 / escala6).move_to([-3.95, -1.0, 0]).set_stroke(width=10),
            run_time=1.6,
        )

        centro7 = [2.5, 1.35, 0]
        globo7 = globo_dialogo(centro7, 4.3, 1.7, [(PI + 0.32, 0.55, [-2.55, 0.5, 0])], grosor=7)
        texto7 = Text("BANACH-TARSKI", font=FUENTE, font_size=62).move_to(centro7)
        self.play(FadeIn(globo7, scale=0.85), run_time=0.8)
        self.play(Write(texto7), run_time=1.4)
        self.next_slide()

        # ---------- Slide 8: Conjuntos ----------
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)

        titulo8 = Text("Conjuntos", font=FUENTE, font_size=80).move_to([0, 2.5, 0])
        xs_caja = [-5.25, -1.75, 1.75, 5.25]
        cajas = VGroup(
            *[
                RoundedRectangle(width=3.1, height=2.3, corner_radius=0.25, stroke_width=6, color=WHITE).move_to(
                    [x, -0.3, 0]
                )
                for x in xs_caja
            ]
        )

        def en_caja(i, mob, dx, dy):
            return mob.move_to(cajas[i].get_center() + np.array([dx, dy, 0]))

        circulos = Group(
            en_caja(0, circulo_lleno(0.4, ManimColor("#E8222A")), -0.8, 0.4),
            en_caja(0, circulo_lleno(0.4, ManimColor("#C5BEE6")), 0.8, 0.45),
            en_caja(0, circulo_lleno(0.4, ManimColor("#B5E61D")), 0.0, -0.5),
        )
        triangulos = Group(
            en_caja(1, triangulo(0.85, ManimColor("#F4A6C0")), -0.85, 0.3),
            en_caja(1, triangulo(0.85, None).rotate(0.6), 0.05, -0.45),
            en_caja(1, triangulo(0.85, ManimColor("#FFE500")).rotate(-0.35), 0.85, 0.35),
        )
        personas8 = Group(
            en_caja(2, cara("luca", 0.9), -0.75, 0.42),
            en_caja(2, cara("moyan", 0.9), -0.6, -0.5),
            en_caja(2, cara("juan", 0.95), 0.8, 0.0),
        )
        variados = Group(
            en_caja(3, estrella(0.5, ManimColor("#99D9EA")), -0.8, 0.35),
            en_caja(
                3,
                poligono_suave(
                    [[-0.55, 0.25, 0], [0.55, -0.2, 0], [-0.1, -0.25, 0]], ManimColor("#FFE500")
                ),
                0.65,
                0.4,
            ),
            en_caja(
                3, poligono_suave([[-0.35, 0.35, 0], [0.4, -0.35, 0], [-0.35, -0.35, 0]], ManimColor("#E8222A")), 0.2, -0.5
            ),
        )
        contenidos = [circulos, triangulos, personas8, variados]

        self.play(Write(titulo8), run_time=1.2)
        self.play(LaggedStart(*[Create(c) for c in cajas], lag_ratio=0.2), run_time=1.4)
        self.play(
            LaggedStart(
                *[LaggedStart(*[FadeIn(e, scale=0.5) for e in grupo], lag_ratio=0.25) for grupo in contenidos],
                lag_ratio=0.3,
            ),
            run_time=2.2,
        )
        self.next_slide()

        # ---------- Slide 9: se elige un elemento de cada caja ----------
        subir = 2.3 * UP + 0.2 * UP
        self.play(
            FadeOut(titulo8, shift=0.5 * UP),
            cajas.animate.shift(subir),
            *[g.animate.shift(subir) for g in contenidos],
            run_time=1.2,
        )

        elegidos = [circulos[1], triangulos[2], personas8[0], variados[0]]
        xs_fila = [-4.2, -1.4, 1.4, 4.2]
        self.play(
            LaggedStart(
                *[
                    e.animate(path_arc=-PI / 4).scale(1.8).move_to([x, -1.9, 0])
                    for e, x in zip(elegidos, xs_fila)
                ],
                lag_ratio=0.3,
            ),
            run_time=2.6,
        )

        # Una caja nueva que encierra a los elegidos (el conjunto que forma el axioma de elección)
        fila = Group(*elegidos)
        caja_nueva = RoundedRectangle(
            width=fila.width + 1.2, height=fila.height + 0.8, corner_radius=0.3, stroke_width=6, color=WHITE
        ).move_to(fila)
        caja_nueva.joint_type = LineJointType.ROUND
        caja_nueva.cap_style = CapStyleType.ROUND
        self.play(Create(caja_nueva), run_time=1.2)
        self.next_slide()

        # ---------- Slide 9.5: el Hotel de Hilbert ----------
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)

        piso_y = -2.7
        suelo = Line([-7.2, piso_y, 0], [7.2, piso_y, 0], stroke_width=6, color=WHITE)
        rayas = VGroup(
            *[
                Line([x, piso_y, 0], [x - 0.45, piso_y - 0.5, 0], stroke_width=4, color=WHITE)
                for x in np.arange(-6.8, 7.4, 0.5)
            ]
        )
        for l in [suelo, *rayas]:
            l.cap_style = CapStyleType.ROUND

        edificio = rect_suave(3.2, 5.6, [-4.0, piso_y + 2.8, 0], radio=0.12)
        ventanas = VGroup(
            *[rect_suave(0.8, 0.62, [x, y, 0], radio=0.1, grosor=5) for y in [2.0, 0.85, -0.3] for x in [-4.75, -3.25]]
        )
        puerta_hotel = rect_suave(0.62, 1.15, [-4.0, piso_y + 0.575, 0], radio=0.08, grosor=5)

        cartel = rect_suave(4.6, 1.35, [0.5, 2.25, 0], radio=0.3)
        nombre_hotel = VGroup(
            Text("Hotel", font=FUENTE, font_size=38), Text("Hilbert", font=FUENTE, font_size=38)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        nombre_hotel.move_to(cartel.get_left() + RIGHT * (0.35 + nombre_hotel.width / 2))
        estrellas = VGroup(*[estrella_5(0.19) for _ in range(5)]).arrange(RIGHT, buff=0.12)
        estrellas.next_to(nombre_hotel, RIGHT, buff=0.35)
        soportes = VGroup(
            Line([-2.4, 2.45, 0], [cartel.get_left()[0], 2.45, 0], stroke_width=5, color=WHITE),
            Line([-2.4, 2.0, 0], [cartel.get_left()[0], 2.0, 0], stroke_width=5, color=WHITE),
        )

        fila_hotel = VGroup(*[persona() for _ in range(6)])
        for i, pe in enumerate(fila_hotel):
            pe.move_to([0.3 + 1.15 * i, piso_y + 0.99, 0])

        self.play(Create(suelo), LaggedStart(*[Create(r) for r in rayas], lag_ratio=0.03), run_time=1)
        self.play(Create(edificio), run_time=1)
        self.play(
            LaggedStart(*[Create(v) for v in ventanas], lag_ratio=0.15),
            Create(puerta_hotel),
            run_time=1.2,
        )
        self.play(Create(soportes), FadeIn(cartel, scale=0.9), run_time=0.7)
        self.play(
            Write(nombre_hotel),
            LaggedStart(*[GrowFromCenter(e) for e in estrellas], lag_ratio=0.2),
            run_time=1.2,
        )
        # La fila de personas llega saltando desde la derecha
        self.play(
            LaggedStart(
                *[
                    saltar(pe, pe.get_center() + RIGHT * 8, pe.get_center(), saltos=5, altura=0.3)
                    for pe in fila_hotel
                ],
                lag_ratio=0.12,
            ),
            run_time=2.6,
        )
        self.next_slide()

        # ---------- Slide 10: zoom a la puerta → las habitaciones ----------
        xs_puertas = [-4.5, 0.0, 4.5]
        puertas = [habitacion(n, [x, -0.1, 0]) for n, x in zip([1, 2, 3], xs_puertas)]
        marco2, hoja2, numero2 = puertas[1]

        d = puerta_hotel.get_center()
        destino10 = hoja2.get_center()
        zoom10 = hoja2.height / puerta_hotel.height
        resto = [suelo, rayas, edificio, ventanas, cartel, nombre_hotel, estrellas, soportes, fila_hotel]
        self.play(
            *[FadeOut(m, shift=pos_zoom(m, d, zoom10, destino10) - m.get_center(), scale=zoom10) for m in resto],
            ReplacementTransform(puerta_hotel, hoja2[0]),
            run_time=1.6,
        )
        # El marco (hueco de la puerta) va detrás de la hoja; queda tapado mientras está cerrada
        self.remove(hoja2[0])
        self.add(marco2, hoja2)
        hoja2[1].set_opacity(0)
        self.play(hoja2[1].animate.set_stroke(opacity=1), run_time=0.3)
        self.play(
            FadeIn(numero2),
            *[FadeIn(VGroup(*p), shift=0.3 * UP) for p in (puertas[0], puertas[2])],
            run_time=0.9,
        )
        self.next_slide()

        # ---------- Slide 11: se abre la puerta 2 y sale la persona a los saltitos ----------
        # La hoja y su número giran juntos sobre la bisagra (lado izquierdo)
        hoja_cerrada, numero_cerrado = hoja2.copy(), numero2.copy()
        abierta = VGroup(hoja2.copy(), numero2.copy()).stretch_to_fit_width(0.32).next_to(marco2, LEFT, buff=0)
        hoja_abierta, numero_abierto = abierta
        self.play(Transform(hoja2, hoja_abierta), Transform(numero2, numero_abierto), run_time=0.8)

        huesped = persona().scale(1.3)
        puerta_pos = marco2.get_bottom() + UP * (huesped.height / 2 + 0.05)
        huesped.move_to(puerta_pos)
        self.play(FadeIn(huesped, scale=0.6), run_time=0.6)
        self.play(
            saltar(huesped, puerta_pos, np.array([8.5, puerta_pos[1] - 0.9, 0]), saltos=6, altura=0.45),
            run_time=3.0,
        )
        self.remove(huesped)
        self.next_slide()

        # ---------- Slide 12: la puerta se cierra y aparece "!" ----------
        self.play(Transform(hoja2, hoja_cerrada), Transform(numero2, numero_cerrado), run_time=0.7)
        exclamacion = Text("!", font=FUENTE, font_size=90).move_to(hoja2[0].get_center())
        self.play(GrowFromCenter(exclamacion), run_time=0.5)
        self.play(Wiggle(exclamacion, scale_value=1.25, rotation_angle=0.06 * TAU), run_time=0.9)
        self.next_slide()

        # ---------- Slide 13: el de la 3 se muda a la 2, y uno nuevo entra a la 3 ----------
        marco3, hoja3, numero3 = puertas[2]
        pos2 = puerta_pos
        pos3 = marco3.get_bottom() + UP * (huesped.height / 2 + 0.05)

        # Se abre la 3 y sale una persona
        self.play(*mover_puerta(marco3, hoja3, numero3, abrir=True), run_time=0.7)
        de_la_3 = persona().scale(1.3).move_to(pos3)
        self.play(FadeIn(de_la_3, scale=0.6), run_time=0.5)
        # Va saltando hasta la 2; la puerta se abre (y se va el "!") cuando llega
        self.play(saltar(de_la_3, pos3, pos2, saltos=4, altura=0.4), run_time=1.8)
        self.play(
            FadeOut(exclamacion, scale=0.5),
            *mover_puerta(marco2, hoja2, numero2, abrir=True),
            run_time=0.7,
        )
        self.play(FadeOut(de_la_3, shift=0.25 * UP, scale=0.8), run_time=0.5)
        self.play(*mover_puerta(marco2, hoja2, numero2, abrir=False), run_time=0.6)

        # Desde la derecha llega otra persona y se mete en la 3
        nuevo = persona().scale(1.3)
        afuera_der = np.array([8.5, pos3[1], 0])
        nuevo.move_to(afuera_der)
        self.play(saltar(nuevo, afuera_der, pos3, saltos=4, altura=0.4), run_time=1.6)
        self.play(FadeOut(nuevo, shift=0.25 * UP, scale=0.8), run_time=0.5)
        self.play(*mover_puerta(marco3, hoja3, numero3, abrir=False), run_time=0.6)
        self.next_slide()

        # ---------- Slide 14: aparece una persona a la izquierda ----------
        izquierda = persona().scale(1.3).move_to([-6.4, pos2[1], 0])
        self.play(FadeIn(izquierda, shift=0.4 * DOWN, scale=0.7), run_time=0.7)
        self.next_slide()

        # ---------- Slide 15: espera impaciente (reloj) y se enoja ----------
        cabeza_izq = izquierda[0]
        reloj = reloj_mob(0.45).move_to(cabeza_izq.get_center() + UP * 1.35)
        _, _, minutero, horario = reloj
        centro_reloj = reloj.get_center()
        self.play(GrowFromCenter(reloj), run_time=0.5)

        cabeza_orig = cabeza_izq.copy()

        def agitar(m, alpha):
            m.become(cabeza_orig.copy().shift(RIGHT * 0.07 * np.sin(8 * TAU * alpha)))

        self.play(
            Rotate(minutero, -TAU, about_point=centro_reloj),
            Rotate(horario, -TAU / 12, about_point=centro_reloj),
            UpdateFromAlphaFunc(cabeza_izq, agitar),
            run_time=2.0,
            rate_func=linear,
        )
        # Chiquito, arriba a la derecha, encima de la cabeza
        enojo = simbolo_enojo(0.36).move_to(cabeza_izq.get_center() + np.array([0.36, 0.36, 0]))
        self.play(FadeOut(reloj, scale=0.6), GrowFromCenter(enojo), run_time=0.45)
        self.play(enojo.animate(rate_func=there_and_back).scale(1.25), run_time=0.4)
        self.next_slide()

        # ---------- Slide 16: todos se corren una habitación y el nuevo entra a la 1 ----------
        marco1, hoja1, numero1 = puertas[0]
        pos1 = marco1.get_bottom() + UP * (huesped.height / 2 + 0.05)
        arriba = marco1.get_top()[1] + 0.35
        flechas = VGroup(
            *[
                CurvedArrow([a + 0.4, arriba, 0], [b - 0.4, arriba, 0], angle=-PI / 2.5, color=WHITE, stroke_width=6)
                for a, b in [(-4.5, 0.0), (0.0, 4.5), (4.5, 7.4)]
            ]
        )
        corazon = corazon_mob(0.36).move_to(enojo.get_center())
        self.play(
            LaggedStart(*[Create(f) for f in flechas], lag_ratio=0.3),
            run_time=1.2,
        )

        # Se abren las tres puertas y sale el huésped de cada habitación
        self.play(
            *mover_puerta(marco1, hoja1, numero1, abrir=True),
            *mover_puerta(marco2, hoja2, numero2, abrir=True),
            *mover_puerta(marco3, hoja3, numero3, abrir=True),
            run_time=0.7,
        )
        h1, h2, h3 = [persona().scale(1.3).move_to(p) for p in (pos1, pos2, pos3)]
        self.play(*[FadeIn(h, scale=0.6) for h in (h1, h2, h3)], run_time=0.5)

        # 1 → 2, 2 → 3, 3 → se va por la derecha
        self.play(
            saltar(h1, pos1, pos2, saltos=4, altura=0.4),
            saltar(h2, pos2, pos3, saltos=4, altura=0.4),
            saltar(h3, pos3, afuera_der, saltos=4, altura=0.4),
            run_time=1.8,
        )
        self.remove(h3)
        # Los otros entran a sus nuevas habitaciones
        self.play(
            FadeOut(h1, shift=0.25 * UP, scale=0.8),
            FadeOut(h2, shift=0.25 * UP, scale=0.8),
            run_time=0.5,
        )
        # Recién ahí el enojo se vuelve corazoncito y el nuevo entra a la 1
        self.play(FadeTransform(enojo, corazon), run_time=0.5)
        self.play(corazon.animate(rate_func=there_and_back).scale(1.3), run_time=0.4)
        nuevo_y_corazon = VGroup(izquierda, corazon)
        self.play(
            saltar(nuevo_y_corazon, nuevo_y_corazon.get_center(), nuevo_y_corazon.get_center() + (pos1 - izquierda.get_center()), saltos=2, altura=0.3),
            run_time=0.9,
        )
        self.play(FadeOut(nuevo_y_corazon, shift=0.25 * UP, scale=0.8), run_time=0.5)
        self.play(
            *mover_puerta(marco1, hoja1, numero1, abrir=False),
            *mover_puerta(marco2, hoja2, numero2, abrir=False),
            *mover_puerta(marco3, hoja3, numero3, abrir=False),
            run_time=0.6,
        )
        self.next_slide()

        # ---------- Slide 17: se aleja la cámara, aparece la 4 y una fila infinita ----------
        S = 0.6  # factor del "dezoom"
        P, D = np.array([0, -0.1, 0]), np.array([0.7, 1.0, 0])
        partes = [m for p in puertas for m in p]
        self.play(
            *[m.animate.scale(S, about_point=P).shift(D) for m in partes],
            FadeOut(flechas, scale=S, shift=D),
            run_time=1.4,
        )
        marco4, hoja4, numero4 = habitacion(4, ORIGIN)
        for m in (marco4, hoja4, numero4):
            m.scale(S, about_point=ORIGIN).shift([6.1, 0.9, 0])
        self.play(FadeIn(VGroup(marco4, hoja4, numero4), shift=0.4 * LEFT), run_time=0.7)

        alto_p = persona().scale(1.3 * S).height
        marcos = [marco1, marco2, marco3, marco4]
        pos = [m.get_bottom() + UP * (alto_p / 2 + 0.03) for m in marcos]  # pos[0] = habitación 1
        y_fila = pos[0][1]
        xs_fila = [-3.2, -4.05, -4.9, -5.75, -6.6]  # el primero de la fila es el más cercano a la puerta 1
        # Los dos primeros son monigotes; los siguientes tres tienen las caras de Juanchi, Gael y Milo
        nombres_fila = [None, None, "juanchi", "gael", "milo"]
        fila = [
            (persona_con_cara(n, 1.3 * S) if n else persona().scale(1.3 * S)) for n in nombres_fila
        ]
        # Se ubican por el cuerpo (la foto hace que la caja del grupo sea más alta)
        ref = persona().scale(1.3 * S)
        cuerpo_off = ref[1].get_center() - ref.get_center()
        for p, x in zip(fila, xs_fila):
            p.shift(np.array([x, y_fila, 0]) + cuerpo_off - p[1].get_center())
        llave = Brace(Group(*fila), DOWN, buff=0.15, color=WHITE)
        infinito = MathTex(r"\infty", font_size=80).next_to(llave, DOWN, buff=0.15)
        self.play(
            LaggedStart(*[FadeIn(p, shift=0.4 * RIGHT) for p in reversed(fila)], lag_ratio=0.15),
            run_time=1.2,
        )
        self.play(GrowFromCenter(llave), Write(infinito), run_time=0.9)
        self.next_slide()

        # ---------- Slide 18: vuelve el reloj y la fila se enoja ----------
        cabezas_fila = [p[0] for p in fila]
        # Lo que se mueve al agitar la cabeza: el círculo y, si tiene, la foto de la cara
        partes_cabeza = [[p[0]] + ([p[2]] if len(p) > 2 else []) for p in fila]
        centros_cab = [c.get_center().copy() for c in cabezas_fila]
        reloj2 = reloj_mob(0.4).move_to([-4.9, 2.45, 0])
        _, _, minutero2, horario2 = reloj2
        self.play(GrowFromCenter(reloj2), run_time=0.5)
        fases = [0.0, 1.7, 3.1, 0.9, 2.4]

        def agitar_fila(m, alpha):
            for partes, c0, f in zip(partes_cabeza, centros_cab, fases):
                dx = 0.05 * (np.sin(8 * TAU * alpha + f) - np.sin(f))
                for parte in partes:
                    parte.move_to(c0 + RIGHT * dx)

        self.play(
            Rotate(minutero2, -TAU, about_point=reloj2.get_center()),
            Rotate(horario2, -TAU / 12, about_point=reloj2.get_center()),
            UpdateFromAlphaFunc(Group(*[x for partes in partes_cabeza for x in partes]), agitar_fila),
            run_time=2.0,
            rate_func=linear,
        )
        enojos = [simbolo_enojo(0.36 * S).move_to(c.get_center() + 0.36 * S * np.array([1, 1, 0])) for c in cabezas_fila]
        self.play(
            FadeOut(reloj2, scale=0.6),
            LaggedStart(*[GrowFromCenter(e) for e in enojos], lag_ratio=0.12),
            run_time=0.8,
        )
        self.next_slide()

        # ---------- Slide 19: el botones del hotel dice N = 2n ----------
        botones = botones_mob().move_to([0.6, -2.75, 0])
        globo_b = globo_dialogo([3.3, -2.45, 0], 1.75, 0.78, [(PI + 0.2, 0.3, [1.2, -2.15, 0])], grosor=6)
        regla = MathTex(r"N = 2n", font_size=60).move_to([3.3, -2.45, 0])
        self.play(FadeIn(botones, shift=1.2 * UP), run_time=0.8)
        self.play(FadeIn(globo_b, scale=0.85), run_time=0.5)
        self.play(Write(regla), run_time=0.9)
        self.next_slide()

        # ---------- Slide 20: 1→2, 2→4, 3 se va; la fila entra a las impares y sigue infinita ----------
        y_flecha = marco1.get_top()[1] + 0.25
        flechas2 = VGroup(
            CurvedArrow([pos[0][0] + 0.3, y_flecha, 0], [pos[1][0] - 0.3, y_flecha, 0], angle=-PI / 2.5, color=WHITE, stroke_width=5),
            CurvedArrow([pos[1][0] + 0.3, y_flecha, 0], [pos[3][0] - 0.3, y_flecha, 0], angle=-PI / 1.8, color=WHITE, stroke_width=5),
            CurvedArrow([pos[2][0] + 0.3, y_flecha, 0], [7.4, y_flecha, 0], angle=-PI / 3, color=WHITE, stroke_width=5),
        )
        self.play(LaggedStart(*[Create(f) for f in flechas2], lag_ratio=0.3), run_time=1.2)

        puertas4 = [(marco1, hoja1, numero1), (marco2, hoja2, numero2), (marco3, hoja3, numero3), (marco4, hoja4, numero4)]
        self.play(*[a for p in puertas4[:3] for a in mover_puerta(*p, abrir=True)], run_time=0.6)
        o1, o2, o3 = [persona().scale(1.3 * S).move_to(pos[i]) for i in range(3)]
        self.play(*[FadeIn(o, scale=0.6) for o in (o1, o2, o3)], run_time=0.4)
        self.play(
            saltar(o1, pos[0], pos[1], saltos=3, altura=0.3),
            saltar(o2, pos[1], pos[3], saltos=5, altura=0.3),
            saltar(o3, pos[2], np.array([8.0, pos[2][1], 0]), saltos=5, altura=0.3),
            AnimationGroup(*mover_puerta(*puertas4[3], abrir=True), lag_ratio=0),
            run_time=1.8,
        )
        self.remove(o3)
        self.play(entrar(o1), entrar(o2), run_time=0.45)
        self.play(
            *mover_puerta(*puertas4[1], abrir=False), *mover_puerta(*puertas4[3], abrir=False), run_time=0.5
        )

        # La fila se pone feliz: los enojos se vuelven corazones
        corazones = [corazon_mob(0.36 * S).move_to(e.get_center()) for e in enojos]
        self.play(*[FadeTransform(e, c) for e, c in zip(enojos, corazones)], run_time=0.5)
        self.play(*[c.animate(rate_func=there_and_back).scale(1.3) for c in corazones], run_time=0.4)
        grupos = [(Group if len(p) > 2 else VGroup)(p, c) for p, c in zip(fila, corazones)]

        # El primero va a la 1 y el segundo a la 3
        self.play(
            saltar_a(grupos[0], fila[0], pos[0], saltos=2, altura=0.25),
            saltar_a(grupos[1], fila[1], pos[2], saltos=5, altura=0.3),
            run_time=1.4,
        )
        self.play(entrar(grupos[0]), entrar(grupos[1]), run_time=0.45)
        self.play(
            *mover_puerta(*puertas4[0], abrir=False), *mover_puerta(*puertas4[2], abrir=False), run_time=0.5
        )

        # Los demás siguen caminando (a las habitaciones 5, 7, 9, ...) y cada vez más rápido
        sep = 0.85
        x0 = fila[2].get_center()[0]
        caminantes = grupos[2:] + [
            persona_feliz(1.3 * S).move_to([x0 - k * sep, y_fila, 0]) for k in range(3, 56)
        ]
        anclas = [g[0][1] for g in caminantes]  # el cuerpo de cada uno
        v0, t1, kexp, T = 1.4, 2.5, 0.9, 6.0

        def distancia(t):
            return v0 * t if t < t1 else v0 * t1 + v0 * (np.exp(kexp * (t - t1)) - 1) / kexp

        def velocidad(t):
            return v0 if t < t1 else v0 * np.exp(kexp * (t - t1))

        def caminar(_, alpha):
            t = alpha * T
            d = distancia(t)
            salto = 0.15 * min(1, v0 / velocidad(t)) * abs(np.sin(PI * d / sep))
            for k, (g, a) in enumerate(zip(caminantes, anclas)):
                destino = np.array([x0 - k * sep + d, y_fila + salto, 0]) + cuerpo_off
                g.shift(destino - a.get_center())

        self.play(FadeOut(llave), FadeOut(infinito), run_time=0.4)
        self.play(UpdateFromAlphaFunc(Group(*caminantes), caminar), run_time=T, rate_func=linear)

        # Loop hiper rápido: una cinta infinita de personas (termina idéntica a como empieza)
        v_fin = velocidad(T)
        fase = (x0 + distancia(T)) % sep
        M, L, x_min = 20, 20 * sep, -8.5
        cinta = [persona_feliz(1.3 * S) for _ in range(M)]
        anclas_c = [g[0][1] for g in cinta]
        n_pasos = int(round(v_fin * 1.0 / sep))
        dur = n_pasos * sep / v_fin

        def cinta_update(_, alpha):
            d = alpha * n_pasos * sep
            for j, (g, a) in enumerate(zip(cinta, anclas_c)):
                x = (fase + j * sep + d - x_min) % L + x_min
                g.shift(np.array([x, y_fila, 0]) + cuerpo_off - a.get_center())

        cinta_update(None, 0)
        self.next_slide(loop=True)
        self.remove(*caminantes)
        self.add(*cinta)
        self.play(UpdateFromAlphaFunc(VGroup(*cinta), cinta_update), run_time=dur, rate_func=linear)
        self.next_slide()

        # ---------- Slide: "Traslaciones" ----------
        # Zoom enorme hacia una zona negra (entre la fila y el botones) hasta que todo sale de pantalla
        # Las personas de la cinta siguen caminando a la misma velocidad mientras la cámara se acerca.
        todo = Group(*self.mobjects)
        otros = Group(*[m for m in self.mobjects if not any(m is g for g in cinta)])
        punto_zoom = np.array([-3.0, -1.0, 0])
        escala_actual = [1.0]
        plantilla = persona_feliz(1.3 * S)
        plantilla.shift(-plantilla[0][1].get_center())  # el cuerpo en el origen
        v_cinta = n_pasos * sep / dur
        T_zoom = 2.2

        def zoom_in(m, alpha):
            f = 120 ** rate_functions.ease_in_sine(alpha)  # crecimiento exponencial, arrancando suave
            otros.scale(f / escala_actual[0], about_point=punto_zoom)
            escala_actual[0] = f
            d = v_cinta * alpha * T_zoom
            for j, g in enumerate(cinta):
                x = (fase + j * sep + d - x_min) % L + x_min
                base = np.array([x, y_fila, 0]) + cuerpo_off
                g.become(plantilla.copy().scale(f, about_point=ORIGIN).shift(punto_zoom + f * (base - punto_zoom)))

        self.play(UpdateFromAlphaFunc(todo, zoom_in), run_time=T_zoom, rate_func=linear)
        self.remove(*self.mobjects)
        self.wait(0.3)
        titulo_tr = Text("Traslaciones", font=FUENTE, font_size=84)
        self.play(Write(titulo_tr), run_time=1.4)
        self.next_slide()
        self.play(FadeOut(titulo_tr, shift=0.4 * UP), run_time=0.6)

        # ---------- Slides 18–23: un vector que se traslada, primero en 2D y después en 3D ----------
        # Proyección 3D hecha a mano: rotación de cámara (a alrededor de y, b alrededor de x),
        # origen en pantalla (ox, oy) y escala s. Con a = b = 0 se ve exactamente como 2D.
        a_t, b_t = ValueTracker(0.0), ValueTracker(0.0)
        ox, oy, s_t = ValueTracker(-5.8), ValueTracker(-3.2), ValueTracker(1.0)
        tx, ty, tz = ValueTracker(2.5), ValueTracker(3.0), ValueTracker(0.0)
        v = np.array([1.5, 1.8, 0.0])

        def proyectar(p, a, b, s, o):
            ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
            rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
            q = rx @ ry @ np.array(p, dtype=float)
            return np.array([o[0] + s * q[0], o[1] + s * q[1], 0])

        def proj(p):
            return proyectar(p, a_t.get_value(), b_t.get_value(), s_t.get_value(), (ox.get_value(), oy.get_value()))

        etiquetas = {n: MathTex(n, font_size=48) for n in "xyz"}
        largo_x = ValueTracker(11.5)  # el eje x se acorta en la slide 24 para dejar lugar al texto
        largos = {"x": 11.5, "y": 6.6, "z": 8.0}
        direcciones = {"x": RIGHT, "y": UP, "z": OUT}

        def dibujar_ejes():
            g = VGroup()
            O = proj(ORIGIN)
            largos["x"] = largo_x.get_value()
            for n in "xyz":
                fin = proj(largos[n] * direcciones[n])
                largo = np.linalg.norm(fin - O)
                if largo < 0.05:
                    continue
                op = min(1.0, largo / 1.5)
                u = normalize(fin - O)
                perp = np.array([-u[1], u[0], 0])
                eje = Line(O, fin, stroke_width=4, color=WHITE)
                eje.add_tip(tip_length=0.22, tip_width=0.2)
                # Subdivisiones: una marquita por cada unidad
                marcas = VGroup(
                    *[
                        Line(proj(k * direcciones[n]) - 0.09 * perp, proj(k * direcciones[n]) + 0.09 * perp,
                             stroke_width=3, color=WHITE)
                        for k in range(1, int(largos[n] - 0.4) + 1)
                    ]
                )
                g.add(VGroup(eje, marcas).set_opacity(op))
                g.add(etiquetas[n].copy().move_to(fin + 0.4 * u).set_opacity(op))
            return g

        def dibujar_vector():
            cola = np.array([tx.get_value(), ty.get_value(), tz.get_value()])
            return Arrow(
                proj(cola), proj(cola + v), buff=0, color=YELLOW, stroke_width=8,
                max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=8,
            )

        # Slide 18: aparecen los ejes y el vector
        ejes_fijos, vector_fijo = dibujar_ejes(), dibujar_vector()
        self.play(Create(ejes_fijos), run_time=1.4)
        self.play(GrowArrow(vector_fijo), run_time=0.8)
        ejes = always_redraw(dibujar_ejes)
        vector = always_redraw(dibujar_vector)
        self.remove(ejes_fijos, vector_fijo)
        self.add(ejes, vector)
        self.next_slide()

        # Slides 19 y 20: el vector se traslada (misma dirección y largo, otro lugar)
        for cola in [(1.0, 0.6), (6.5, 2.8)]:
            self.play(tx.animate.set_value(cola[0]), ty.animate.set_value(cola[1]), run_time=1.5)
            self.next_slide()

        # Slide 21: la cámara gira y aparece el eje z; el vector pasa a moverse en 3D.
        # El origen final se calcula para que el dibujo 3D (ejes + etiquetas) quede centrado en pantalla.
        a3, b3, s3 = -0.7, 0.3, 0.68
        extremos = [proyectar(largos[n] * direcciones[n] * (1 + 0.5 / largos[n]), a3, b3, s3, (0, 0)) for n in "xyz"]
        extremos.append(np.zeros(3))
        caja_min, caja_max = np.min(extremos, axis=0), np.max(extremos, axis=0)
        centro = (caja_min + caja_max) / 2
        self.play(
            a_t.animate.set_value(a3),
            b_t.animate.set_value(b3),
            ox.animate.set_value(-centro[0]),
            oy.animate.set_value(-centro[1]),
            s_t.animate.set_value(s3),
            tx.animate.set_value(2.5),
            ty.animate.set_value(2.6),
            tz.animate.set_value(1.0),
            run_time=2.6,
        )
        self.next_slide()

        # Slides 22 y 23: traslaciones en 3D (los ejes quedan quietos)
        for cx, cy, cz in [(1.0, -0.2, 3.2), (0.3, 2.2, 4.0)]:
            self.play(
                tx.animate.set_value(cx),
                ty.animate.set_value(cy),
                tz.animate.set_value(cz),
                run_time=1.8,
            )
            self.next_slide()

        # ---------- Slide 24: vuelta de 3D a 2D (la transición al revés) + texto ----------
        P = np.array([1.5, 2.2, 0.0])  # punto de partida (rojo)
        Q = P + np.array([4.0, 0.6, 0.0])  # punto de llegada (azul)
        self.play(
            a_t.animate.set_value(0.0),
            b_t.animate.set_value(0.0),
            ox.animate.set_value(-0.8),
            oy.animate.set_value(-3.2),
            s_t.animate.set_value(0.85),
            largo_x.animate.set_value(8.6),
            tx.animate.set_value(P[0]),
            ty.animate.set_value(P[1]),
            tz.animate.set_value(0.0),
            run_time=2.6,
        )
        punto_rojo = Dot(proj(P), radius=0.1, color=ManimColor("#E8222A"))
        texto_tr = VGroup(
            Text("La traslación se anota", font=FUENTE, font_size=36),
            Text("a través de un vector", font=FUENTE, font_size=36),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-4.05, 1.0, 0])
        self.play(GrowFromCenter(punto_rojo), Write(texto_tr), run_time=1.5)
        self.bring_to_front(vector)
        self.next_slide()

        # ---------- Slide 25: el vector va al otro punto y aparece el vector de traslación v ----------
        VERDE_V = ManimColor("#83C167")

        def dibujar_v():
            cola = np.array([tx.get_value(), ty.get_value(), 0.0])
            ini, fin = proj(P), proj(cola)
            if np.linalg.norm(fin - ini) < 0.08:
                return VMobject()
            return Arrow(ini, fin, buff=0, color=VERDE_V, stroke_width=7,
                         max_tip_length_to_length_ratio=0.12, max_stroke_width_to_length_ratio=8)

        flecha_v = always_redraw(dibujar_v)
        self.add(flecha_v, punto_rojo, vector)  # la verde queda debajo del vector amarillo y del punto
        self.play(tx.animate.set_value(Q[0]), ty.animate.set_value(Q[1]), run_time=2.0)
        punto_azul = Dot(proj(Q), radius=0.1, color=ManimColor("#3BA3F0"))
        medio = (proj(P) + proj(Q)) / 2
        dir_v = normalize(proj(Q) - proj(P))
        nombre_v = MathTex(r"\vec{v}", font_size=56, color=VERDE_V).move_to(medio + 0.45 * np.array([-dir_v[1], dir_v[0], 0]))
        formula_v = MathTex(r"\vec{v} = (a,\, b)", font_size=56, color=VERDE_V)
        formula_v.next_to(texto_tr, DOWN, buff=0.9, aligned_edge=LEFT)
        self.play(GrowFromCenter(punto_azul), FadeIn(nombre_v, shift=0.2 * UP), run_time=0.7)
        self.play(Write(formula_v), run_time=1.2)
        self.next_slide()

        # ---------- Transición a "Rotaciones": zoom enorme mientras la cámara empieza a girar ----------
        for m in self.mobjects:
            m.clear_updaters()  # los ejes y vectores dejan de redibujarse para poder transformarlos
        todo = Group(*self.mobjects)
        punto_giro = np.array([-3.6, -2.4, 0])  # zona negra (abajo a la izquierda, lejos de todo)
        estado = {"f": 1.0, "ang": 0.0}

        def zoom_girando(m, alpha):
            f = 150 ** rate_functions.ease_in_sine(alpha)
            ang = -0.9 * PI * rate_functions.ease_in_quad(alpha)  # la cámara gira cada vez más rápido
            m.scale(f / estado["f"], about_point=punto_giro)
            m.rotate(ang - estado["ang"], about_point=punto_giro)
            estado["f"], estado["ang"] = f, ang

        self.play(UpdateFromAlphaFunc(todo, zoom_girando), run_time=2.4, rate_func=linear)
        self.remove(*self.mobjects)
        self.wait(0.3)
        titulo_rot = Text("Rotaciones", font=FUENTE, font_size=84)
        self.play(Write(titulo_rot), run_time=1.4)
        self.next_slide()
        self.play(FadeOut(titulo_rot, shift=0.4 * UP), run_time=0.6)

        # ---------- Rotaciones: el bloque "?" (modelo 3D renderizado con la GPU) ----------
        # Se reutiliza la misma cámara/proyección de las traslaciones, vuelta a la vista 2D inicial.
        for tr, val in [(a_t, 0), (b_t, 0), (ox, -5.8), (oy, -3.2), (s_t, 1.0), (largo_x, 11.5)]:
            tr.set_value(val)
        bloque = Modelo3D(
            str(CARPETA / "modelo3d" / "Cube_obj.obj"),
            {"aiStandardSurface2SG": (0.97, 0.72, 0.05), "aiStandardSurface3SG": (0.95, 0.95, 0.95)},
            resolucion=560,
        )
        # Posición del bloque (mundo) y su orientación: M = Rz(gz) · Rx(gx) · Ry(gy) · Rz(g0)
        cx, cy, cz = ValueTracker(5.5), ValueTracker(3.3), ValueTracker(0.0)
        g0, gy, gx, gz = (ValueTracker(0.0) for _ in range(4))
        TAM, MEDIO = 1.8, 0.9  # tamaño del bloque en el mundo y margen del render

        def rot_x(t):
            return np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])

        def rot_y(t):
            return np.array([[np.cos(t), 0, np.sin(t)], [0, 1, 0], [-np.sin(t), 0, np.cos(t)]])

        def rot_z(t):
            return np.array([[np.cos(t), -np.sin(t), 0], [np.sin(t), np.cos(t), 0], [0, 0, 1]])

        def centro_bloque():
            return np.array([cx.get_value(), cy.get_value(), cz.get_value()])

        def pixeles_bloque():
            camara = rot_x(b_t.get_value()) @ rot_y(a_t.get_value())
            M = rot_z(gz.get_value()) @ rot_x(gx.get_value()) @ rot_y(gy.get_value()) @ rot_z(g0.get_value())
            return bloque.render(camara @ M, medio=MEDIO)

        # Una sola imagen que se actualiza en el lugar en cada cuadro (píxeles, tamaño y posición)
        cubo = ImageMobject(pixeles_bloque())

        def actualizar_cubo(m):
            m.pixel_array = pixeles_bloque()
            m.set_height(2 * MEDIO * TAM * s_t.get_value()).move_to(proj(centro_bloque()))

        actualizar_cubo(cubo)
        cubo.add_updater(actualizar_cubo)

        def flecha_sentido(antihorario=True):
            """Flecha curva alrededor del bloque que indica el sentido de giro."""
            c = proj(centro_bloque())
            r = 0.95 * MEDIO * TAM * s_t.get_value()
            arco = Arc(radius=r, start_angle=PI / 6, angle=2 * PI / 3, arc_center=c, color=WHITE, stroke_width=6)
            if not antihorario:
                arco = Arc(radius=r, start_angle=5 * PI / 6, angle=-2 * PI / 3, arc_center=c, color=WHITE, stroke_width=6)
            return arco.add_tip(tip_length=0.25, tip_width=0.25)

        # Slide: ejes 2D y el bloque visto de frente
        ejes_fijos = dibujar_ejes()
        self.play(Create(ejes_fijos), run_time=1.4)
        ejes = always_redraw(dibujar_ejes)
        self.remove(ejes_fijos)
        self.add(ejes)
        self.play(FadeIn(cubo, scale=0.6), run_time=0.8)
        self.next_slide()

        # Slides: gira en un sentido y después en el otro
        for angulo, antihorario in [(PI / 3, True), (-PI / 4, False)]:
            sentido = flecha_sentido(antihorario)
            self.play(Create(sentido), run_time=0.5)
            self.play(g0.animate.set_value(angulo), run_time=1.6)
            self.play(FadeOut(sentido), run_time=0.4)
            self.next_slide()

        # Slide: pasa a 3D (misma transición que en traslaciones)
        self.play(
            a_t.animate.set_value(a3),
            b_t.animate.set_value(b3),
            ox.animate.set_value(-centro[0]),
            oy.animate.set_value(-centro[1]),
            s_t.animate.set_value(s3),
            cx.animate.set_value(4.5),
            cy.animate.set_value(3.2),
            cz.animate.set_value(2.5),
            run_time=2.6,
        )
        self.next_slide()

        # Slides: rotaciones en 3D alrededor de distintos ejes (con el eje de giro punteado)
        colores_eje = {"y": ManimColor("#83C167"), "x": ManimColor("#FC6255"), "z": ManimColor("#58C4DD")}
        for nombre, tracker, angulo in [("y", gy, 2 * PI / 3), ("x", gx, PI / 2), ("z", gz, -PI / 2)]:
            d = direcciones[nombre]
            c = centro_bloque()
            # El eje atraviesa el bloque: la mitad que apunta hacia la cámara se dibuja delante del bloque
            # (desde donde sale de la cara), y la otra mitad detrás (el bloque la tapa donde corresponde).
            camara = rot_x(b_t.get_value()) @ rot_y(a_t.get_value())
            hacia_camara = d if (camara @ d)[2] >= 0 else -d
            estilo = dict(color=colores_eje[nombre], stroke_width=5, dash_length=0.15)
            eje_atras = DashedLine(proj(c - 2.2 * hacia_camara), proj(c), **estilo)
            eje_adelante = DashedLine(proj(c + 0.55 * TAM * hacia_camara), proj(c + 2.2 * hacia_camara), **estilo)
            punta = proj(c + 2.2 * d)
            etiqueta_giro = MathTex(nombre, color=colores_eje[nombre], font_size=44).next_to(
                punta, normalize(punta - proj(c)), buff=0.15
            )
            self.add(eje_atras)
            self.bring_to_front(cubo)
            self.add(eje_adelante)
            self.play(Create(eje_atras), Create(eje_adelante), FadeIn(etiqueta_giro), run_time=0.5)
            self.play(tracker.animate.set_value(angulo), run_time=2.0)
            self.play(FadeOut(eje_atras), FadeOut(eje_adelante), FadeOut(etiqueta_giro), run_time=0.4)
            self.next_slide()

        # Slide: vuelve a 2D (al revés), el bloque queda de frente y aparece el texto
        self.play(
            a_t.animate.set_value(0.0),
            b_t.animate.set_value(0.0),
            ox.animate.set_value(-0.8),
            oy.animate.set_value(-3.2),
            s_t.animate.set_value(0.85),
            largo_x.animate.set_value(8.6),
            cx.animate.set_value(4.4),
            cy.animate.set_value(3.6),
            cz.animate.set_value(0.0),
            *[g.animate.set_value(0.0) for g in (g0, gy, gx, gz)],
            run_time=2.8,
        )
        texto_rot = VGroup(
            Text("La rotación se expresa", font=FUENTE, font_size=36),
            Text("a través de una matriz", font=FUENTE, font_size=36),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([-4.05, 2.2, 0])
        punto_centro = Dot(proj(centro_bloque()), radius=0.08, color=ManimColor("#E8222A"))
        self.play(Write(texto_rot), run_time=1.5)
        self.next_slide()

        # Slide: último giro (θ = 45°) con el ángulo marcado, y su matriz
        c = proj(centro_bloque())
        r_ang = 1.15 * MEDIO * TAM * s_t.get_value()  # más largo que la diagonal del bloque
        ref = DashedLine(c, c + r_ang * UP, color=WHITE, stroke_width=4, dash_length=0.1)
        theta = ValueTracker(0.0)
        brazo = always_redraw(
            lambda: Line(c, c + r_ang * np.array([-np.sin(theta.get_value()), np.cos(theta.get_value()), 0]),
                         color=VERDE_V, stroke_width=6)
        )
        arco_ang = always_redraw(
            lambda: Arc(radius=0.95 * r_ang, start_angle=PI / 2, angle=theta.get_value(), arc_center=c,
                        color=VERDE_V, stroke_width=5)
            if theta.get_value() > 0.01 else VMobject()
        )
        self.add(ref, brazo, arco_ang, punto_centro)
        self.bring_to_front(cubo)
        self.bring_to_front(ref, brazo, arco_ang, punto_centro)
        self.play(Create(ref), GrowFromCenter(punto_centro), run_time=0.6)
        self.play(theta.animate.set_value(PI / 4), g0.animate.set_value(PI / 4), run_time=2.0)
        nombre_theta = MathTex(r"\theta", color=VERDE_V, font_size=48).move_to(
            c + 1.15 * r_ang * np.array([-np.sin(PI / 8), np.cos(PI / 8), 0])
        )
        matriz_general = MathTex(
            r"R(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}",
            font_size=44, color=VERDE_V,
        ).next_to(texto_rot, DOWN, buff=0.7, aligned_edge=LEFT)
        matriz_45 = MathTex(
            r"R(45^\circ) = \begin{pmatrix} \tfrac{\sqrt{2}}{2} & -\tfrac{\sqrt{2}}{2} \\[4pt] \tfrac{\sqrt{2}}{2} & \tfrac{\sqrt{2}}{2} \end{pmatrix}",
            font_size=44, color=VERDE_V,
        ).next_to(matriz_general, DOWN, buff=0.6, aligned_edge=LEFT)
        self.play(FadeIn(nombre_theta, scale=0.6), run_time=0.5)
        self.play(Write(matriz_general), run_time=1.4)
        self.play(Write(matriz_45), run_time=1.4)
        self.next_slide()

        # ---------- Slide 26: el teorema, y a una persona le explota la cabeza ----------
        cubo.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)

        AZUL_T = ManimColor("#58C4DD")
        lineas = VGroup(
            Tex(r"Para todo $A, B$ (", r"acotados", r") $\subset E$ (espacio euclídeo de"),
            Tex(r"dimensión $d \geq 3$) $\mid$ interior$(A)$, interior$(B) \neq \varnothing$, $\exists$"),
            Tex(r"particiones de $A, B$ en un número finito de subconjuntos"),
            Tex(
                r"disjuntos, $A = \displaystyle\bigsqcup_{i=1}^{k} A_i$, "
                r"$B = \displaystyle\bigsqcup_{i=1}^{k} B_i \;\mid\; \forall i \in \mathbb{N},\ i \leq k \quad A_i, B_i$"
            ),
            Tex(r"son ", r"congruentes", r"."),
        )
        for l in lineas:
            l.scale(0.82)
        lineas[0][1].set_color(AZUL_T)
        lineas[4][1].set_color(AZUL_T)
        lineas.arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to([-1.3, 1.0, 0])
        caja_teo = RoundedRectangle(
            width=lineas.width + 0.9, height=lineas.height + 0.8, corner_radius=0.2, stroke_width=3, color=GREY_B
        ).move_to(lineas)
        self.play(Create(caja_teo), run_time=0.8)
        self.play(LaggedStart(*[Write(l) for l in lineas], lag_ratio=0.5), run_time=4.0)
        self.next_slide()

        lector = persona().scale(1.15).move_to([5.7, -2.4, 0])
        cabeza_l, cuerpo_l = lector
        self.play(FadeIn(lector, shift=0.6 * LEFT), run_time=0.8)
        # Mira el teorema: la cabeza vibra cada vez más fuerte y se va poniendo roja
        c0 = cabeza_l.get_center().copy()

        def vibrar(m, alpha):
            amp = 0.13 * alpha ** 1.5
            t = alpha * 2.6
            m.move_to(c0 + amp * np.array([np.sin(TAU * 17 * t), 0.5 * np.sin(TAU * 23 * t + 1.0), 0]))
            m.set_fill(interpolate_color(BLACK, ManimColor("#D7262E"), alpha ** 2), 1)

        self.play(UpdateFromAlphaFunc(cabeza_l, vibrar), run_time=2.6, rate_func=linear)
        # ¡Explota!: la cabeza se parte en pedazos que salen volando, más una onda y chispas
        centro_c = cabeza_l.get_center()
        radio_c = cabeza_l.width / 2
        n_trozos = 9
        trozos = VGroup(
            *[
                Sector(radius=radio_c, start_angle=k * TAU / n_trozos, angle=TAU / n_trozos * 0.92, arc_center=centro_c,
                       stroke_width=4, stroke_color=WHITE, fill_color=ManimColor("#D7262E"), fill_opacity=1)
                for k in range(n_trozos)
            ]
        )
        onda = Circle(radius=radio_c, color=ManimColor("#FFB000"), stroke_width=8).move_to(centro_c)
        rng_e = np.random.default_rng(3)
        chispas = VGroup(
            *[
                Dot(centro_c, radius=0.05, color=random_color_choice)
                for random_color_choice in rng_e.choice([ManimColor("#FFB000"), ManimColor("#D7262E"), WHITE], 18)
            ]
        )
        self.remove(cabeza_l)
        self.add(trozos, chispas)
        animaciones = [onda.animate.scale(4).set_stroke(opacity=0)]
        for k, tr in enumerate(trozos):
            ang = (k + 0.5) * TAU / n_trozos
            dir_k = np.array([np.cos(ang), np.sin(ang), 0])
            animaciones.append(
                tr.animate.shift(dir_k * rng_e.uniform(2.0, 3.2) + DOWN * 0.6).rotate(rng_e.uniform(-3, 3)).set_opacity(0)
            )
        for ch in chispas:
            ang = rng_e.uniform(0, TAU)
            animaciones.append(
                ch.animate.shift(np.array([np.cos(ang), np.sin(ang), 0]) * rng_e.uniform(1.0, 2.6)).set_opacity(0)
            )
        self.add(onda)
        self.play(*animaciones, run_time=1.1, rate_func=rate_functions.ease_out_cubic)
        self.remove(trozos, chispas, onda)
        self.next_slide()

        # ---------- Slides 27–31: la esfera de puntos verdes que pierde capas ----------
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
        rng_s = np.random.default_rng(11)
        bandas = [(2.4, 3.2, 1050), (1.6, 2.4, 540), (0.8, 1.6, 210), (0.12, 0.8, 45)]  # (r_min, r_max, cantidad)
        puntos_3d, banda_de = [], []
        for b, (r0, r1, n) in enumerate(bandas):
            dirs = rng_s.normal(size=(n, 3))
            dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
            radios = np.cbrt(rng_s.uniform(r0 ** 3, r1 ** 3, n))  # uniforme en volumen
            puntos_3d.append(dirs * radios[:, None])
            banda_de += [b] * n
        puntos_3d = np.vstack(puntos_3d)
        banda_de = np.array(banda_de)
        VERDE_P = ManimColor("#2ECC40")
        puntos = VGroup(*[Dot(radius=0.034, color=VERDE_P) for _ in range(len(puntos_3d))])
        centro_esf = Dot(ORIGIN, radius=0.05, color=VERDE_P)
        giro = ValueTracker(0.0)
        visible = [ValueTracker(0.0) for _ in bandas]  # opacidad de cada capa

        def actualizar_esfera(m):
            a = giro.get_value()
            R = rot_x(0.35) @ rot_y(a)
            q = puntos_3d @ R.T
            prof = (q[:, 2] + 3.2) / 6.4  # 0 = atrás, 1 = adelante
            ops = [v.get_value() for v in visible]
            for dot, (x, y, _), p, b in zip(puntos, q, prof, banda_de):
                dot.move_to([x, y, 0])
                dot.set_fill(opacity=(0.25 + 0.75 * p) * ops[b])

        actualizar_esfera(puntos)
        puntos.add_updater(actualizar_esfera)
        self.add(puntos, centro_esf)
        centro_esf.set_opacity(0)
        self.play(
            *[v.animate.set_value(1.0) for v in visible],
            centro_esf.animate.set_opacity(1),
            giro.animate.increment_value(0.6),
            run_time=1.5,
        )
        self.next_slide()

        # Se van sacando capas (desvaneciéndose) mientras la esfera sigue girando
        for b in range(len(bandas)):
            self.play(visible[b].animate.set_value(0.0), giro.animate.increment_value(0.9), run_time=1.6)
            if b < len(bandas) - 1:
                self.next_slide()

        # Solo queda un punto: aparece la flecha "Por acá" (misma slide que la última capa)
        puntos.clear_updaters()
        self.remove(puntos)
        flecha_aca = CurvedArrow([3.2, 1.6, 0], [0.25, 0.2, 0], angle=PI / 3, color=WHITE, stroke_width=6)
        texto_aca = Text("Por acá", font=FUENTE, font_size=56).next_to(flecha_aca.get_start(), UR, buff=0.15)
        self.play(Create(flecha_aca), Write(texto_aca), run_time=1.2)
        self.next_slide()

        # ---------- Slide 32: la esfera maciza, el punto de inicio (celeste) y las 4 direcciones ----------
        CELESTE = ManimColor("#9CDCEB")
        ROJO_P = ManimColor("#FC6255")
        esfera_g = esfera(2.6).move_to(ORIGIN)
        inicio = centro_esf
        self.add(esfera_g)
        self.bring_to_front(inicio)
        esfera_g.scale(0.01)
        self.play(
            FadeOut(flecha_aca), FadeOut(texto_aca),
            esfera_g.animate.scale(100),
            inicio.animate.set_color(CELESTE).scale(2.0),
            run_time=1.3,
        )
        brujula = {}
        for nombre, d in [("N", UP), ("S", DOWN), ("E", RIGHT), ("W", LEFT)]:
            fl = Arrow(ORIGIN, 1.7 * d, buff=0.12, color=WHITE, stroke_width=7, max_tip_length_to_length_ratio=0.18)
            et = Text(nombre, font=FUENTE, font_size=46).move_to(2.1 * d)
            brujula[nombre] = (fl, et)
        self.play(
            LaggedStart(*[AnimationGroup(GrowArrow(fl), FadeIn(et, scale=0.6)) for fl, et in brujula.values()], lag_ratio=0.2),
            run_time=1.4,
        )
        self.bring_to_front(inicio)
        self.next_slide()

        # ---------- Slide 33: zoom a la flecha N → su medida es arccos(1/3); el recorrido en la esfera ----------
        alfa = np.arccos(1 / 3)  # ≈ 70,53°
        flecha_n, etiqueta_n = brujula["N"]
        grande = Arrow([-5.6, -2.9, 0], [-5.6, 2.9, 0], buff=0, color=WHITE, stroke_width=8,
                       max_tip_length_to_length_ratio=0.07)
        p_zoom, z33 = ORIGIN, 3.4
        destino33 = np.array([-5.6, -2.9, 0])
        resto33 = [esfera_g, inicio, etiqueta_n] + [m for k, par in brujula.items() if k != "N" for m in par]
        self.play(
            Transform(flecha_n, grande),
            *[FadeOut(m, shift=pos_zoom(m, p_zoom, z33, destino33) - m.get_center(), scale=z33) for m in resto33],
            run_time=1.6,
        )
        llave33 = Brace(grande, RIGHT, buff=0.25, color=WHITE)
        medida = MathTex(r"\arccos\!\left(\tfrac{1}{3}\right) \approx 70{,}53^\circ", font_size=46)
        medida.next_to(llave33, RIGHT, buff=0.25)
        self.play(GrowFromCenter(llave33), Write(medida), run_time=1.2)

        # La esfera al costado, vista con una "cámara" propia para poder hacer zoom en la slide 34:
        # pantalla = T + z · (p − vc)
        vz, vcx, vcy, Tx, Ty = (ValueTracker(v) for v in (1.0, 0.0, 0.0, 0.0, 0.0))
        C_ESF, R_ESF = np.array([3.75, -0.2, 0]), 2.15

        def V(p):
            return np.array([Tx.get_value(), Ty.get_value(), 0]) + vz.get_value() * (
                np.array(p) - np.array([vcx.get_value(), vcy.get_value(), 0])
            )

        def punto_circ(ang):
            return C_ESF + R_ESF * np.array([np.cos(ang), np.sin(ang), 0])

        ang0 = PI  # el inicio, en el borde izquierdo
        progreso = [ValueTracker(0.0) for _ in range(5)]  # 5 pasos de arccos(1/3), en sentido horario

        def dibujar_recorrido():
            z = vz.get_value()
            g = VGroup(esfera(R_ESF * z, capas=70).move_to(V(C_ESF)))  # más capas: degradé suave al hacer zoom
            g.add(Circle(radius=R_ESF * z, color=WHITE, stroke_width=3).move_to(V(C_ESF)))
            r_arco = (R_ESF + 0.2) * z
            for k, pr in enumerate(progreso):
                t = pr.get_value()
                if t < 0.02:
                    continue
                arco = Arc(radius=r_arco, start_angle=ang0 - k * alfa, angle=-alfa * t, arc_center=V(C_ESF),
                           color=ROJO_P if k == 4 else VERDE_V, stroke_width=7)
                arco.add_tip(tip_length=0.28, tip_width=0.26)
                g.add(arco)
            return g

        recorrido = always_redraw(dibujar_recorrido)
        punto_ini = always_redraw(lambda: Dot(V(punto_circ(ang0)), radius=0.11, color=CELESTE))
        self.play(FadeIn(recorrido, scale=0.8), FadeIn(punto_ini, scale=0.5), run_time=1.0)
        for k, pr in enumerate(progreso):
            self.play(pr.animate.set_value(1.0), run_time=1.0 if k < 4 else 1.3)
        ang_fin = ang0 - 5 * alfa
        punto_fin = always_redraw(lambda: Dot(V(punto_circ(ang_fin)), radius=0.11, color=ROJO_P))
        self.play(GrowFromCenter(punto_fin), run_time=0.4)
        self.next_slide()

        # ---------- Slide 34: zoom al inicio y al final: no coinciden (desfase) ----------
        medio = (punto_circ(ang0) + punto_circ(ang_fin)) / 2
        self.play(
            FadeOut(flecha_n), FadeOut(llave33), FadeOut(medida),
            vz.animate.set_value(7.0),
            vcx.animate.set_value(medio[0]), vcy.animate.set_value(medio[1]),
            Tx.animate.set_value(0.6), Ty.animate.set_value(0.2),
            run_time=2.2,
        )
        et_ini = Text("inicio", font=FUENTE, font_size=40, color=CELESTE).next_to(V(punto_circ(ang0)), RIGHT, buff=0.4)
        et_fin = Text("final", font=FUENTE, font_size=40, color=ROJO_P).next_to(V(punto_circ(ang_fin)), RIGHT, buff=0.4)
        for et in (et_ini, et_fin):
            et.add_background_rectangle(color=BLACK, opacity=0.75, buff=0.1)
        cuenta = MathTex(
            r"5 \cdot \arccos\!\left(\tfrac{1}{3}\right) \approx 352{,}6^\circ \neq 360^\circ", font_size=48
        ).to_edge(DOWN, buff=0.5)
        cuenta.add_background_rectangle(color=BLACK, opacity=0.8, buff=0.15)
        self.play(FadeIn(et_ini, shift=0.2 * RIGHT), FadeIn(et_fin, shift=0.2 * RIGHT), run_time=0.7)
        self.play(Write(cuenta), run_time=1.4)
        self.next_slide()

        # ---------- Slides 35–38: palabras de movimientos (se leen de derecha a izquierda) ----------
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        for m in self.mobjects:
            m.clear_updaters()
        self.remove(*self.mobjects)

        C_MOV, R_MOV, PASO = np.array([3.3, -0.2, 0]), 2.6, 0.85
        esfera_m = esfera(R_MOV, capas=40).move_to(C_MOV)
        inicio_m = Dot(C_MOV, radius=0.1, color=CELESTE)
        DIRS = {"N": UP, "S": DOWN, "E": RIGHT, "W": LEFT}

        def palabra(letras, color_letras=None):
            """'Movimiento' + cada letra como objeto propio (para tipear y subrayar de a una)."""
            cab = Text("Movimiento", font=FUENTE, font_size=46)
            ls = VGroup(*[Text(l, font=FUENTE, font_size=46, color=(color_letras or {}).get(i, WHITE))
                          for i, l in enumerate(letras)])
            ls.arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
            g = VGroup(cab, ls).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
            return g.move_to([-3.9, 1.9, 0]), ls

        def flechas_camino(letras, desde=C_MOV, color=WHITE):
            """Una flecha por letra, aplicando las letras de derecha a izquierda."""
            p, fls = np.array(desde), []
            for l in reversed(letras):
                q = p + PASO * DIRS[l]
                fls.append(Arrow(p, q, buff=0, color=color, stroke_width=7,
                                 max_tip_length_to_length_ratio=0.28, max_stroke_width_to_length_ratio=12))
                p = q
            return fls, p

        self.play(GrowFromCenter(esfera_m), run_time=1.0)
        self.add(inicio_m)
        self.play(GrowFromCenter(inicio_m), run_time=0.4)

        # Slide 35: WNEN, con la aclaración de que se lee de derecha a izquierda
        texto_m, letras_m = palabra("WNEN")
        aclaracion = VGroup(
            Text("Se lee de derecha", font=FUENTE, font_size=40),
            Text("a izquierda", font=FUENTE, font_size=40),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([-4.3, -1.3, 0])
        flecha_lee = CurvedArrow(letras_m.get_bottom() + DOWN * 0.15, aclaracion.get_top() + UP * 0.15 + RIGHT * 0.3,
                                 angle=-PI / 3, color=WHITE, stroke_width=5)
        fls, _ = flechas_camino("WNEN")
        self.play(Write(texto_m), run_time=1.0)
        self.play(Create(flecha_lee), FadeIn(aclaracion, shift=0.2 * DOWN), run_time=1.0)
        self.play(*[GrowArrow(f) for f in fls], run_time=1.0)
        self.bring_to_front(inicio_m)
        self.next_slide()
        anteriores = [texto_m, flecha_lee, aclaracion, *fls]

        # Slides 36 y 37: ENNNES y WS (todas las flechas juntas)
        for w in ["ENNNES", "WS"]:
            texto_m, letras_m = palabra(w)
            fls, _ = flechas_camino(w)
            self.play(*[FadeOut(m) for m in anteriores], run_time=0.5)
            self.play(Write(texto_m), run_time=0.9)
            self.play(*[GrowArrow(f) for f in fls], run_time=1.0)
            self.bring_to_front(inicio_m)
            self.next_slide()
            anteriores = [texto_m, *fls]

        # Slide 38: NESS se tipea letra por letra de derecha a izquierda, con su flecha cada vez
        self.play(*[FadeOut(m) for m in anteriores], run_time=0.5)
        texto_m, letras_m = palabra("SNESS", {0: ROJO_P})  # la S roja (a la izquierda) se agrega al final
        cab_m = texto_m[0]
        self.play(Write(cab_m), run_time=0.8)
        subrayado = Line(LEFT * 0.17, RIGHT * 0.17, color=VERDE_V, stroke_width=6)
        p = C_MOV
        flechas_38 = []
        for i in range(len(letras_m) - 1, 0, -1):  # S, S, E, N
            letra = letras_m[i]
            q = p + PASO * DIRS["SNESS"[i]]
            fl = Arrow(p, q, buff=0, color=WHITE, stroke_width=6,
                       max_tip_length_to_length_ratio=0.32, max_stroke_width_to_length_ratio=12)
            nuevo_sub = subrayado.copy().next_to(letra, DOWN, buff=0.12)
            if i == len(letras_m) - 1:
                self.play(FadeIn(letra, shift=0.15 * DOWN), GrowFromCenter(nuevo_sub), run_time=0.35)
                subrayado = nuevo_sub
            else:
                self.play(FadeIn(letra, shift=0.15 * DOWN), subrayado.animate.move_to(nuevo_sub), run_time=0.35)
            self.play(GrowArrow(fl), run_time=0.55)
            self.bring_to_front(inicio_m)
            flechas_38.append(fl)
            p = q
        # Último: una S en rojo, que vuelve para atrás (deshace el último N)
        s_roja = letras_m[0]
        atras = Arrow(p + RIGHT * 0.13, p + RIGHT * 0.13 + PASO * DOWN, buff=0, color=ROJO_P, stroke_width=6,
                      max_tip_length_to_length_ratio=0.32, max_stroke_width_to_length_ratio=12)
        self.play(FadeIn(s_roja, shift=0.15 * DOWN), subrayado.animate.next_to(s_roja, DOWN, buff=0.12).set_color(ROJO_P),
                  run_time=0.4)
        self.play(GrowArrow(atras), run_time=0.7)
        self.next_slide()

        # ---------- La esfera va al centro, vibra y se rompe en 5 fragmentos ----------
        self.play(
            *[FadeOut(m) for m in [texto_m, subrayado, atras, *flechas_38, inicio_m]],
            esfera_m.animate.move_to(ORIGIN),
            run_time=1.2,
        )
        centro_v = esfera_m.get_center().copy()

        def vibrar_esfera(m, alpha):
            amp = 0.12 * alpha ** 1.6
            t = alpha * 2.2
            m.move_to(centro_v + amp * np.array([np.sin(TAU * 15 * t), 0.6 * np.sin(TAU * 21 * t + 0.7), 0]))

        self.play(UpdateFromAlphaFunc(esfera_m, vibrar_esfera), run_time=2.2, rate_func=linear)
        esfera_m.move_to(centro_v)

        # 5 piezas: cuñas desde el centro con bordes quebrados, recortadas de la esfera sombreada
        rng_f = np.random.default_rng(5)
        angs = PI / 2 + np.arange(5) * TAU / 5 + rng_f.uniform(-0.25, 0.25, 5)
        R_EXT = 1.4 * R_MOV

        def borde(ang):
            fin = R_EXT * np.array([np.cos(ang), np.sin(ang), 0])
            perp = np.array([-np.sin(ang), np.cos(ang), 0])
            return [t * fin + perp * rng_f.uniform(-0.13, 0.13) * R_MOV for t in (0.18, 0.38, 0.58, 0.8)] + [fin]

        bordes = [borde(a) for a in angs]
        piezas = VGroup()
        for i in range(5):
            a0, a1 = angs[i], angs[(i + 1) % 5] + (TAU if i == 4 else 0)
            arco_ext = [R_EXT * np.array([np.cos(a), np.sin(a), 0]) for a in np.linspace(a0, a1, 10)]
            forma = Polygon(ORIGIN, *bordes[i], *arco_ext, *reversed(bordes[(i + 1) % 5]))
            pieza = VGroup()
            for capa in esfera_m:
                trozo = Intersection(capa, forma)
                if len(trozo.points):
                    pieza.add(trozo.set_stroke(width=0).set_fill(capa.get_fill_color(), 1))
            piezas.add(pieza)
        grietas = VGroup(
            *[VMobject().set_points_as_corners([ORIGIN, *[q for q in b if np.linalg.norm(q) < R_MOV * 0.98]])
              .set_stroke(VERDE_OSCURO, 4) for b in bordes]
        )
        self.play(Create(grietas), run_time=0.35)
        # Al separarse los pedazos, las grietas dejan de existir (pasan a ser los bordes de cada pedazo)
        self.remove(esfera_m, grietas)
        self.add(piezas)
        destello = Circle(radius=0.3, stroke_width=0).set_fill(ManimColor("#FFFDE0"), 1).move_to(ORIGIN)
        onda_e = Circle(radius=0.6, color=ManimColor("#B8F5C8"), stroke_width=14).move_to(ORIGIN)
        particulas = VGroup(
            *[Dot(ORIGIN, radius=rng_f.uniform(0.03, 0.08),
                  color=rng_f.choice([VERDE, VERDE_CLARO, ManimColor("#FFFDE0")])) for _ in range(70)]
        )
        self.add(particulas, destello, onda_e)
        def rapido(fraccion, base=rate_functions.ease_out_expo):
            """Termina en la primera `fraccion` del tiempo total (para destello y onda)."""
            return lambda t: base(min(1.0, t / fraccion))

        vuelos = []
        for i, pieza in enumerate(piezas):
            medio_ang = (angs[i] + angs[(i + 1) % 5] + (TAU if i == 4 else 0)) / 2
            dir_p = np.array([np.cos(medio_ang), np.sin(medio_ang), 0])
            vuelos.append(
                pieza.animate(rate_func=rate_functions.ease_out_cubic)  # salen disparados y se ven volar
                .shift(dir_p * rng_f.uniform(13, 16)).rotate(rng_f.uniform(-4, 4))
            )
        for pt in particulas:
            ang = rng_f.uniform(0, TAU)
            vuelos.append(
                pt.animate(rate_func=rapido(0.7, rate_functions.ease_out_cubic))
                .shift(np.array([np.cos(ang), np.sin(ang), 0]) * rng_f.uniform(4, 12)).set_opacity(0)
            )
        self.play(
            *vuelos,
            destello.animate(rate_func=rapido(0.22)).scale(16).set_fill(opacity=0),
            onda_e.animate(rate_func=rapido(0.5)).scale(14).set_stroke(opacity=0, width=2),
            run_time=1.5,
        )
        self.remove(piezas, particulas, destello, onda_e)
        self.wait(0.4)
        self.next_slide()

        self.slide_final()

    def slide_final(self):
        """Slide final: Moyan, Juan y Luca detrás de la mesa haciendo backflips, el público saltando,
        un atardecer que sale detrás y un «¡Gracias por ver!» cinematográfico (franjas de cine,
        letras doradas que caen una por una y un destello). Dura 20 s."""
        DUR = 20
        rng = np.random.default_rng(42)

        # --- Atardecer: cielo en degradé + sol que sube por detrás de la mesa ---
        franjas_cielo = [
            (0.0, ManimColor("#120822")), (0.35, ManimColor("#3B1550")), (0.6, ManimColor("#9C2F5A")),
            (0.8, ManimColor("#E8613A")), (1.0, ManimColor("#FFB347")),
        ]

        def color_cielo(t):
            for (t0, c0), (t1, c1) in zip(franjas_cielo, franjas_cielo[1:]):
                if t <= t1:
                    return interpolate_color(c0, c1, (t - t0) / (t1 - t0))
            return franjas_cielo[-1][1]

        n_bandas = 60
        alto_banda = config.frame_height / n_bandas
        cielo = VGroup(*[
            Rectangle(width=config.frame_width + 0.2, height=alto_banda * 1.05, stroke_width=0)
            .set_fill(color_cielo(k / (n_bandas - 1)), 1)
            .move_to([0, config.frame_height / 2 - (k + 0.5) * alto_banda, 0])
            for k in range(n_bandas)
        ])
        cielo.set_opacity(0)
        sol = VGroup(*[
            Circle(radius=r, stroke_width=0).set_fill(c, o)
            for r, c, o in ((3.2, "#FF8C42", 0.10), (2.6, "#FF9F4A", 0.16), (2.1, "#FFB65C", 0.25),
                            (1.7, "#FFD27F", 1.0), (1.45, "#FFE3A3", 1.0))
        ])
        SOL_INI, SOL_FIN = np.array([0, -6.5, 0]), np.array([0, 0.9, 0])
        sol.move_to(SOL_INI)

        mesa = RoundedRectangle(width=7.2, height=2.8, corner_radius=0.12, stroke_width=5, color=WHITE)
        mesa.set_fill(BLACK, 1).move_to([0, -2.05, 0])
        oradores = [persona_con_cara(n, 1.15) for n in ("moyan", "juan", "luca")]
        for p, x in zip(oradores, (-2.4, 0, 2.4)):
            p.shift(np.array([x, -0.55, 0]) - p[1].get_bottom())
        # Público a los costados, amontonado; los de más abajo quedan adelante
        lugares = []
        for lado in (-1, 1):
            for fila, y in enumerate((-1.75, -2.45, -3.15, -3.85)):
                for k in range(3 if fila % 2 == 0 else 2):
                    x = lado * (4.25 + (k + (0.5 if fila % 2 else 0)) * 1.0 + rng.uniform(-0.15, 0.15))
                    lugares.append((x, y + rng.uniform(-0.1, 0.1)))
        lugares.sort(key=lambda q: -q[1])
        publico = VGroup()
        for x, y in lugares:
            p = persona(0.82)
            p.shift(np.array([x, y, 0]) - p[1].get_bottom())
            publico.add(p)
        originales = [p.copy() for p in publico]

        # --- Título cinematográfico ---
        DORADO = ManimColor("#FFD27F")
        titulo = Text("¡Gracias por ver!", font=FUENTE).scale(1.3).move_to([0, 2.75, 0])
        titulo.set_color_by_gradient(ManimColor("#FFF1C9"), DORADO, ManimColor("#FFB347"))
        letras = list(titulo)
        letras_fin = [l.copy() for l in letras]
        for l in letras:
            l.set_opacity(0)
        halo = titulo.copy().set_fill(opacity=0).set_stroke(ManimColor("#FFB347"), width=14, opacity=0)
        destello = Rectangle(width=0.35, height=1.6, stroke_width=0).set_fill(WHITE, 0.0).rotate(0.35)
        barra_sup = Rectangle(width=config.frame_width + 0.2, height=0.75, stroke_width=0).set_fill(BLACK, 1)
        barra_inf = barra_sup.copy()
        barra_sup.move_to([0, config.frame_height / 2 + 0.4, 0])
        barra_inf.move_to([0, -config.frame_height / 2 - 0.4, 0])
        sup_ini, inf_ini = barra_sup.get_center(), barra_inf.get_center()

        # Saltos periódicos del público: cada uno con su ritmo y su fase
        n_pub = rng.integers(30, 42, len(publico))
        f_pub = rng.uniform(0, 1, len(publico))
        n_ora = [36, 38, 36]
        f_ora = [0.0, 0.33, 0.66]
        # Backflips de los tres de arriba (segundos de inicio por orador)
        flips_ora = [[2.2, 7.6, 12.0, 16.4], [3.4, 9.0, 12.0, 17.0], [4.6, 10.4, 12.0, 17.6]]
        D_FLIP = 1.15
        orig_ora = [[parte.copy() for parte in p] for p in oradores]

        def altura(n, f, a, h):
            return h * abs(np.sin(PI * (n * a + f)))

        def tramo(t, t0, t1):
            return min(1, max(0, (t - t0) / (t1 - t0)))

        def animar(mob, a):
            t = 0.8 + a * (DUR - 0.8)
            # Atardecer
            s_cielo = smooth(tramo(t, 0.8, 7.0))
            cielo.set_fill(opacity=s_cielo)
            sol.move_to(interpolate(SOL_INI, SOL_FIN, smooth(tramo(t, 0.8, 9.0))))
            # Público
            for i, (p, o) in enumerate(zip(publico, originales)):
                p.become(o.copy().shift(UP * altura(n_pub[i], f_pub[i], a, 0.28)))
            # Oradores con backflips
            for i, p in enumerate(oradores):
                dy, giro = altura(n_ora[i], f_ora[i], a, 0.32), 0.0
                for t0 in flips_ora[i]:
                    if t0 <= t <= t0 + D_FLIP:
                        s = (t - t0) / D_FLIP
                        dy = 1.6 * 4 * s * (1 - s)
                        giro = TAU * smooth(s)
                c = orig_ora[i][1].get_center()
                for parte, orig in zip(p, orig_ora[i]):
                    m = orig.copy().rotate(giro, about_point=c).shift(UP * dy)
                    if isinstance(parte, ImageMobject):
                        parte.points = m.points
                    else:
                        parte.become(m)
            # Franjas de cine
            sb = smooth(tramo(t, 2.0, 3.2))
            barra_sup.move_to(sup_ini + DOWN * 0.75 * sb)
            barra_inf.move_to(inf_ini + UP * 0.75 * sb)
            # Letras que caen desde arriba, una por una
            for k, (l, fin) in enumerate(zip(letras, letras_fin)):
                s = tramo(t, 3.0 + 0.09 * k, 3.0 + 0.09 * k + 0.9)
                e = rate_functions.ease_out_back(s) if s > 0 else 0
                m = fin.copy().scale(1 + 0.8 * (1 - s)).shift(UP * 2.2 * (1 - e))
                m.set_opacity(min(1, 1.6 * s))
                l.become(m)
            # Halo que respira y destello que cruza el título
            sh = tramo(t, 5.0, 6.0)
            halo.set_stroke(opacity=sh * (0.22 + 0.1 * np.sin(2.2 * t)))
            sd = tramo(t, 6.2, 7.4)
            destello.move_to(titulo.get_center() + RIGHT * interpolate(-4.8, 4.8, smooth(sd)))
            destello.set_fill(opacity=0.55 * np.sin(PI * sd))

        self.next_slide()
        self.add(cielo, sol)
        self.play(FadeIn(mesa), *[FadeIn(p) for p in oradores], FadeIn(publico), run_time=0.8)
        self.add(halo, *letras, destello, barra_sup, barra_inf)
        self.play(
            UpdateFromAlphaFunc(Group(cielo, sol, mesa, *oradores, publico, halo, *letras, destello, barra_sup, barra_inf),
                                animar),
            run_time=DUR - 0.8,
            rate_func=linear,
        )
        self.next_slide()

    def loop_discusion(self, personas, insultos):
        """Cabezas que suben y bajan desincronizadas + texto que tiembla. Termina igual que empieza."""
        cabezas = [p[0] for p in personas]
        cabezas_orig = [c.copy() for c in cabezas]
        letras = list(insultos)
        letras_orig = [l.copy() for l in letras]
        rng = np.random.default_rng(7)
        fases_cab = rng.uniform(0, TAU, len(cabezas))
        frec_cab = [2, 3, 2, 3, 2, 3]
        fases_let = rng.uniform(0, TAU, (len(letras), 3))
        frec_let = rng.integers(4, 7, (len(letras), 3))

        def discutir(mob, alpha):
            for c, o, f, n in zip(cabezas, cabezas_orig, fases_cab, frec_cab):
                s = np.sin(n * TAU * alpha + f) - np.sin(f)
                c.become(o.copy().shift(0.09 * s * UP))
            for l, o, f, n in zip(letras, letras_orig, fases_let, frec_let):
                d = [np.sin(n[i] * TAU * alpha + f[i]) - np.sin(f[i]) for i in range(3)]
                l.become(o.copy().shift(0.035 * (d[0] * RIGHT + d[1] * UP)).rotate(0.07 * d[2]))

        self.play(UpdateFromAlphaFunc(VGroup(*cabezas, *letras), discutir), run_time=3, rate_func=linear)


class SlideFinal(BanachTarski):
    """Prueba rápida: solo la slide final."""

    def construct(self):
        self.slide_final()
