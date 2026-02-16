"""
mph.utils
=========
Unterstützungsfunktionen für:
- Generieren der diskreten Zeitreihe (Zeitfenster)
  Event überlappt Zeitfenster genau dann, wenn:
    event_start < window_end  UND  event_end > window_start
- Zustandsbestimmung je Zeitfenster (gesund/krank/tot)
- Generierung der Markov-Ketten für die Patienten

Regeln
------
- Priorität: tot > krank > gesund
- Absorption: nach tot bleibt tot
- state_code: gesund=0, krank=1, tot=2
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


# ----------------------------
# Zustände und Mapping
# ----------------------------

STATE_CODE: Dict[str, int] = {"gesund": 0, "krank": 1, "tot": 2}
STATE_LABEL: Dict[int, str] = {v: k for k, v in STATE_CODE.items()}
DEFAULT_STATES_ORDER: Tuple[str, str, str] = ("gesund", "krank", "tot")


# ----------------------------
# Zeitreihen
# ----------------------------

def add_step(dt: pd.Timestamp, step_unit: str, step_size: int) -> pd.Timestamp:
    """Addiert einen Zeitschritt zu dt."""
    if step_unit == "month":
        return dt + relativedelta(months=step_size)
    if step_unit == "quarter":
        return dt + relativedelta(months=3 * step_size)
    if step_unit == "day":
        return dt + timedelta(days=step_size)
    if step_unit == "hour":
        return dt + timedelta(hours=step_size)
    raise ValueError(step_unit)


def generiere_zeitreihe(
    first_contact: pd.Timestamp,
    observation_end: pd.Timestamp,
    step_unit: str,
    step_size: int,
) -> Tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """
    Erzeugt eine diskrete Zeitreihe als aufeinanderfolgende Zeitfenster [start, end)
    beginnend bei first_contact in Schritten (step_unit, step_size). Das letzte
    angebrochene Zeitfenster, das über observation_end hinausgeht, wird weggelassen.

    Parameters
    ----------
    first_contact : pd.Timestamp    Startzeitpunkt der Zeitreihe.
    observation_end : pd.Timestamp  Ende der Beobachtungszeit.
    step_unit : str                 Zeiteinheit: "month" | "quarter" | "day" | "hour"
    step_size : int                 Schrittweite (typisch 1).

    Returns
    -------
    Tuple[pd.DatetimeIndex, pd.DatetimeIndex]
        (window_starts, window_ends) mit gleicher Länge T.
        Fenster i entspricht time_step i+1.
    """
    starts: List[pd.Timestamp] = []
    ends: List[pd.Timestamp] = []

    zs = first_contact
    ze = add_step(zs, step_unit, step_size)
    while ze <= observation_end:
        starts.append(zs)
        ends.append(ze)
        zs = ze
        ze = add_step(zs, step_unit, step_size)

    return pd.DatetimeIndex(starts), pd.DatetimeIndex(ends)


# ----------------------------
# Zustandsbestimmung
# ----------------------------
# Grundidee (Reihenfolge ist wichtig):
#    1) Zunächst werden alle Zustände auf "gesund" gesetzt.
#    2) Danach werden alle Zeitfenster, bei denen ein Event für den Patienten vorliegt,
#       auf "krank" gesetzt.
#    3) Zum Schluss wird geprüft, ob ein Todesdatum vorhanden ist und dann werden alle
#       Zeitfenster ab dem Todeszeitpunkt als "tot" markiert (überschreibt krank/gesund).

def mark_sick(
    events: pd.DataFrame,
    window_starts: pd.DatetimeIndex,
    window_ends: pd.DatetimeIndex,
) -> np.ndarray:
    """
    Liefert eine Maske (bool) für Zeitfenster, die als "krank" gelten sollen.
    Returns
    -------
    np.ndarray(bool), Länge T
        True bedeutet: Zeitfenster i (time_step i+1) ist "krank".
    """
    T = len(window_starts)
    if T == 0 or events is None or len(events) == 0:
        return np.zeros(T, dtype=bool)

    # datetime64[ns] Arrays für schnelle searchsorted-Operationen
    s = events["starttime"].to_numpy(dtype="datetime64[ns]")
    e = events["endtime"].to_numpy(dtype="datetime64[ns]")
    ws = window_starts.to_numpy(dtype="datetime64[ns]")
    we = window_ends.to_numpy(dtype="datetime64[ns]")

    # Für jedes Event: finde Fenster-Indexbereich [l, r), der überlappt
    # l = erstes Fenster mit window_end  > event_start
    # r = erstes Fenster mit window_start >= event_end
    l = we.searchsorted(s, side="right")
    r = ws.searchsorted(e, side="left")

    mask = l < r
    if not np.any(mask):
        return np.zeros(T, dtype=bool)

    l = l[mask]
    r = r[mask]

    # Range-Marking via Diff-Array + cumsum
    diff = np.zeros(T + 1, dtype=np.int32)
    np.add.at(diff, l, 1)
    np.add.at(diff, r, -1)

    return np.cumsum(diff[:-1]) > 0

def mark_dead(dod: Optional[pd.Timestamp], window_ends: pd.DatetimeIndex) -> Optional[int]:
    """
    Bestimmt den Start-Index (0-basiert) ab dem der Zustand "tot" gilt.
    - Ein Zeitfenster gilt als "tot", wenn dod < window_end.
      -> wir suchen das erste Fenster mit window_end > dod.
    Returns
    -------
    Optional[int]
        0-basierter Index i (für time_step i+1), ab dem "tot" gilt.
        None, wenn dod fehlt/NaT ist oder nicht in den Fenstern liegt.
    """
    if dod is None or pd.isna(dod) or len(window_ends) == 0:
        return None

    idx = int(window_ends.searchsorted(pd.Timestamp(dod), side="right"))
    return None if idx >= len(window_ends) else idx

def generate_states(
    window_starts: pd.DatetimeIndex,
    window_ends: pd.DatetimeIndex,
    events: pd.DataFrame,
    dod: Optional[pd.Timestamp],
) -> np.ndarray:
    """
    Ermittelt den Zustand je Zeitfenster (time_step 1..T).
    Returns
    -------
    np.ndarray(object), Länge T
        Zustände pro Zeitfenster: "gesund" | "krank" | "tot"
    """
    T = len(window_starts)
    states = np.full(T, "gesund", dtype=object)

    sick = mark_sick(events, window_starts, window_ends)
    states[sick] = "krank"

    dead_idx = mark_dead(dod, window_ends)
    if dead_idx is not None:
        states[dead_idx:] = "tot"

    return states


# ----------------------------
# Erzeugen der Markov-Chain
# ----------------------------

def build_patient_chain(
    *,
    subject_id: int,
    first_contact: pd.Timestamp,
    observation_end: pd.Timestamp,
    dod: Optional[pd.Timestamp],
    events: pd.DataFrame,
    step_unit: str,
    step_size: int,
    start_state_t0: str = "gesund",
) -> List[Dict[str, Any]]:
    """
    Erzeugt die Markov-Kette (Zeitreihe + Zustände) für einen einzelnen Patienten.
    Ablauf
    ------
    1) Generiere die diskrete Zeitreihe (Zeitfenster) ab first_contact bis observation_end.
    2) Bestimme den Zustand je Zeitfenster (gesund/krank/tot) via generate_states
    3) Baue daraus die Chain als List[Dict] mit time_step=0..T.
    Erwartung
    ---------
    - events enthält nur Events dieses subject_id und ist bereits bereinigt
      (Spalten: starttime, endtime, Datetime-Typen).
    """
    window_starts, window_ends = generiere_zeitreihe(
        first_contact=first_contact,
        observation_end=observation_end,
        step_unit=step_unit,
        step_size=step_size,
    )

    states = generate_states(
        window_starts=window_starts,
        window_ends=window_ends,
        events=events,
        dod=dod,
    )

    chain: List[Dict[str, Any]] = [{
        "subject_id": int(subject_id),
        "time_step": 0,
        "state": str(start_state_t0),
        "state_code": int(STATE_CODE[str(start_state_t0)]),
        "zeitfenster_start": pd.Timestamp(first_contact),
        "zeitfenster_end": pd.Timestamp(first_contact),
    }]

    for i in range(len(window_starts)):
        state = str(states[i])
        chain.append({
            "subject_id": int(subject_id),
            "time_step": int(i + 1),
            "state": state,
            "state_code": int(STATE_CODE[state]),
            "zeitfenster_start": pd.Timestamp(window_starts[i]),
            "zeitfenster_end": pd.Timestamp(window_ends[i]),
        })

    return chain

