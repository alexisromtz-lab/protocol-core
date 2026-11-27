"""protocol — Materia A: Protocolo de Custodia Determinista y Reserva de Ranuras.

Subárbol limpio (Repo A). No contiene bitácora: la evidencia se cita, no se
copia aquí (SPEC §6.1). Este paquete no importa nada del taller y no depende de
rutas absolutas (§6.2).

La versión del árbol se declara aquí y la del documento en la cabecera de
`SPEC.md` (§6.3). Son nueve líneas repartidas en seis archivos —`pyproject.toml`,
este paquete, `README.md` tres veces, `SPEC.md`, `CITATION.cff` dos veces y
`NOTICE`— que un lector puede leer y que tienen que decir lo mismo.
`tests/test_version.py` las mide todas y además barre el árbol entero para que
ninguna se quede sin registrar. Una discrepancia es un defecto, no una
tolerancia. El tag no entra en esa lista porque no vive dentro del árbol: se mide
fuera, con `git describe --tags --exact-match`.
"""

__version__ = "0.2.0"

__all__ = ["__version__"]
