"""
Esfera de Bloch animada para o README do perfil.

Renderizar (na pasta assets/):
    manim --fps 20 -r 540,540 bloch_sphere.py BlochSphere

A cena dura dois ciclos de LOOP segundos; o GIF usa apenas o segundo,
assim o rastro já está formado e a animação fecha o loop sem "pulo".
"""
import numpy as np
from manim import *

config.frame_width = 8
config.frame_height = 8

BG = "#0d1117"          # fundo do tema escuro do GitHub
CYAN = "#58d5ff"
VIOLET = "#a371f7"
PINK = "#ff7eb6"
GRID = "#30476b"

LOOP = 8.0              # duração de um ciclo (s)
R = 2.2                 # raio da esfera


def bloch_point(t):
    """Posição do estado |ψ> no instante t (periódica em LOOP)."""
    phi = 2 * TAU * t / LOOP                      # duas voltas por ciclo
    theta = PI / 2 + 0.85 * np.sin(TAU * t / LOOP)  # nutação polo-a-polo
    return R * np.array([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta),
    ])


class BlochSphere(ThreeDScene):
    def construct(self):
        self.camera.background_color = BG
        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES, zoom=1.0)

        # Esfera translúcida
        sphere = Sphere(radius=R, resolution=(28, 28))
        sphere.set_fill(CYAN, opacity=0.06)
        sphere.set_stroke(GRID, width=0.6, opacity=0.5)

        # Equador e meridianos em destaque
        equator = Circle(radius=R, color=CYAN, stroke_width=2, stroke_opacity=0.8)
        meridian_xz = Circle(radius=R, color=CYAN, stroke_width=1.2, stroke_opacity=0.45).rotate(PI / 2, RIGHT)
        meridian_yz = meridian_xz.copy().rotate(PI / 2, OUT)

        # Eixos x, y, z
        axes = VGroup(*[
            Line3D(-v * (R + 0.35), v * (R + 0.35), color=GRAY_B, thickness=0.008)
            for v in (RIGHT, UP, OUT)
        ])

        # Rótulos dos polos e eixos (sempre de frente para a câmera)
        def label(tex, pos, color=WHITE, scale=0.75):
            m = MathTex(tex, color=color).scale(scale).move_to(pos)
            self.add_fixed_orientation_mobjects(m)
            return m

        labels = [
            label(r"|0\rangle", OUT * (R + 0.6), CYAN, 0.9),
            label(r"|1\rangle", IN * (R + 0.6), PINK, 0.9),
            label("x", RIGHT * (R + 0.6), GRAY_A, 0.6),
            label("y", UP * (R + 0.6), GRAY_A, 0.6),
        ]

        # Vetor de estado, rastro e brilho na ponta
        t = ValueTracker(0)
        tip = Dot3D(point=bloch_point(0), radius=0.07, color=PINK)
        tip.add_updater(lambda m: m.move_to(bloch_point(t.get_value())))

        state = Arrow3D(ORIGIN, bloch_point(0), color=PINK, thickness=0.025,
                        height=0.28, base_radius=0.08)
        state.add_updater(lambda m: m.become(
            Arrow3D(ORIGIN, bloch_point(t.get_value()), color=PINK, thickness=0.025,
                    height=0.28, base_radius=0.08)))

        trail = TracedPath(tip.get_center, stroke_color=VIOLET, stroke_width=5,
                           dissipating_time=LOOP * 0.45, stroke_opacity=[0, 1])
        glow = TracedPath(tip.get_center, stroke_color=VIOLET, stroke_width=14,
                          dissipating_time=LOOP * 0.45, stroke_opacity=[0, 0.22])
        halo = Dot3D(point=bloch_point(0), radius=0.16, color=PINK).set_opacity(0.3)
        halo.add_updater(lambda m: m.move_to(bloch_point(t.get_value())))

        # Projeção no equador (linha tracejada da ponta até o plano xy)
        proj = always_redraw(lambda: DashedLine(
            bloch_point(t.get_value()),
            np.array([*bloch_point(t.get_value())[:2], 0]),
            color=VIOLET, stroke_width=1.5, dash_length=0.08))

        # Equação fixa na tela
        eq = MathTex(
            r"|\psi\rangle = \cos\tfrac{\theta}{2}\,|0\rangle"
            r" + e^{i\varphi}\sin\tfrac{\theta}{2}\,|1\rangle",
            color=WHITE,
        ).scale(0.72).to_edge(DOWN, buff=0.45)
        eq[0][0:3].set_color(PINK)
        self.add_fixed_in_frame_mobjects(eq)

        self.add(sphere, equator, meridian_xz, meridian_yz, axes,
                 *labels, glow, trail, proj, state, halo, tip)

        # Câmera dá uma volta completa por ciclo -> loop perfeito
        self.begin_ambient_camera_rotation(rate=TAU / LOOP)
        self.play(t.animate.set_value(2 * LOOP), run_time=2 * LOOP, rate_func=linear)
        self.stop_ambient_camera_rotation()
